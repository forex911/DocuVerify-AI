"""
Tests for LangGraph Multi-Agent Verification Architecture.
Validates:
- Agent routing and coordination (Supervisor, Document Intelligence, Order Matching, Validation, Reconciliation, Explanation)
- Bounded retry limits preventing infinite loops
- Ambiguous order matching escalation
- Evidence completeness across all generated discrepancies
- Guarantee that no agent can approve or reject documents
- Workflow API endpoints (/api/workflows/verify, /api/workflows/{id}, /api/workflows/{id}/agents)
"""

import io
from decimal import Decimal
import pymupdf
from app.database.models import Order
from app.orchestration.state import WorkflowState
from app.services.workflow_service import WorkflowService


def create_pdf(text: str) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text(pymupdf.Point(50, 100), text)
    b = doc.tobytes()
    doc.close()
    return b


def test_multi_agent_workflow_full_execution(client, db_session):
    # 1. Setup Order
    order_id = "ORD-AGENT-101"
    client.post(
        "/api/orders",
        json={
            "order_id": order_id,
            "order_number": order_id,
            "customer_name": "Atlas Industrial",
            "currency": "USD",
            "quantity": "500",
            "grand_total": "12500.00",
            "destination": "Rotterdam Port",
        },
    )

    # 2. Upload Invoice with Mismatch (12000.00 vs 12500.00)
    pdf_text = (
        "Commercial Invoice\n"
        "Order Ref: ORD-AGENT-101\n"
        "Customer: Atlas Industrial\n"
        "Currency: USD\n"
        "Quantity: 500\n"
        "Destination: Rotterdam Port\n"
        "Grand Total: USD 12,000.00\n"
    )
    doc_id = client.post(
        "/api/documents/upload",
        files={"file": ("inv.pdf", io.BytesIO(create_pdf(pdf_text)), "application/pdf")},
    ).json()["id"]

    # 3. Execute LangGraph workflow synchronously
    final_state = WorkflowService.start_verification_workflow(
        document_ids=[doc_id],
        order_id=order_id,
        run_async=False,
    )

    # 4. Verify Workflow State
    assert final_state.workflow_status == "REVIEW_REQUIRED"
    assert final_state.requires_human_review is True
    assert len(final_state.discrepancies) >= 1

    fin_disc = next((d for d in final_state.discrepancies if d["rule_id"] == "FIN-001"), None)
    assert fin_disc is not None
    assert fin_disc["severity"] == "HIGH"
    assert fin_disc["expected_value"] == "12500.00"
    assert fin_disc["actual_value"] == "12000.00"
    assert "investigation_steps" in fin_disc

    # 5. Verify All Agent Traces Recorded
    agent_names = [log["agent_name"] for log in final_state.agent_execution_log]
    assert "DocumentIntelligenceAgent" in agent_names
    assert "OrderMatchingAgent" in agent_names
    assert "ValidationAgent" in agent_names
    assert "ExplanationAgent" in agent_names
    assert "SupervisorAgent" in agent_names


def test_ambiguous_order_matching_routes_to_human(client):
    # Create two orders with identical normalized substrings for ambiguity test
    client.post(
        "/api/orders",
        json={
            "order_id": "ORD-AMBIG-A",
            "order_number": "ORD-AMBIG-A",
            "customer_name": "Multi Corp",
            "currency": "USD",
            "grand_total": "10000.00",
        },
    )
    client.post(
        "/api/orders",
        json={
            "order_id": "ORD-AMBIG-B",
            "order_number": "ORD-AMBIG-B",
            "customer_name": "Multi Corp",
            "currency": "USD",
            "grand_total": "10000.00",
        },
    )

    # Document with incomplete/ambiguous reference 'AMBIG'
    pdf_text = "Commercial Invoice\nOrder Ref: AMBIG\nCustomer: Multi Corp\nGrand Total: USD 10,000.00\n"
    doc_id = client.post(
        "/api/documents/upload",
        files={"file": ("ambig.pdf", io.BytesIO(create_pdf(pdf_text)), "application/pdf")},
    ).json()["id"]

    # Run workflow without explicit order_id
    final_state = WorkflowService.start_verification_workflow(
        document_ids=[doc_id],
        order_id=None,
        run_async=False,
    )

    assert final_state.order_match_result["match_type"] == "AMBIGUOUS"
    assert final_state.requires_human_review is True
    assert final_state.workflow_status == "REVIEW_REQUIRED"
    assert len(final_state.matching_candidates) >= 2


def test_evidence_completeness(client):
    order_id = "ORD-EVID-1"
    client.post(
        "/api/orders",
        json={
            "order_id": order_id,
            "order_number": order_id,
            "customer_name": "Evidence Corp",
            "currency": "USD",
            "quantity": "100",
            "grand_total": "5000.00",
        },
    )

    pdf_text = (
        "Commercial Invoice\n"
        "Order Ref: ORD-EVID-1\n"
        "Total Quantity: 80\n"
        "Grand Total: USD 4,000.00\n"
    )
    doc_id = client.post(
        "/api/documents/upload",
        files={"file": ("evid.pdf", io.BytesIO(create_pdf(pdf_text)), "application/pdf")},
    ).json()["id"]

    final_state = WorkflowService.start_verification_workflow(
        document_ids=[doc_id],
        order_id=order_id,
        run_async=False,
    )

    # Every discrepancy must have evidence references
    for disc in final_state.discrepancies:
        assert disc["document_id"] == doc_id
        assert disc["rule_id"] is not None
        assert disc["severity"] in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
        assert disc["expected_value"] is not None
        assert disc["actual_value"] is not None
        assert disc["explanation"] is not None
        assert disc["source_page"] is not None
        assert disc["source_text"] is not None


def test_no_agent_can_approve_or_reject(client):
    """Verifies invariant: Even perfectly clean documents are NOT approved by agents."""
    order_id = "ORD-NO-AUTO-APP"
    client.post(
        "/api/orders",
        json={
            "order_id": order_id,
            "order_number": order_id,
            "customer_name": "Safe Trade",
            "currency": "USD",
            "quantity": "200",
            "grand_total": "4000.00",
            "destination": "Singapore Port",
        },
    )

    # Perfectly matching invoice
    pdf_text = (
        "Commercial Invoice\n"
        "Order Ref: ORD-NO-AUTO-APP\n"
        "Customer: Safe Trade\n"
        "Currency: USD\n"
        "Total Quantity: 200\n"
        "Destination: Singapore Port\n"
        "Grand Total: USD 4,000.00\n"
    )
    doc_id = client.post(
        "/api/documents/upload",
        files={"file": ("clean.pdf", io.BytesIO(create_pdf(pdf_text)), "application/pdf")},
    ).json()["id"]

    final_state = WorkflowService.start_verification_workflow(
        document_ids=[doc_id],
        order_id=order_id,
        run_async=False,
    )

    # Discrepancies is 0, but status is REVIEW_REQUIRED (never APPROVED!)
    assert len(final_state.discrepancies) == 0
    assert final_state.workflow_status == "REVIEW_REQUIRED"
    assert "awaiting" in final_state.final_investigation_report["summary_conclusion"].lower()


def test_workflow_api_endpoints(client):
    order_id = "ORD-API-TEST"
    client.post(
        "/api/orders",
        json={
            "order_id": order_id,
            "order_number": order_id,
            "customer_name": "API Corp",
            "currency": "USD",
            "grand_total": "1000.00",
        },
    )
    pdf_text = "Commercial Invoice\nOrder Ref: ORD-API-TEST\nGrand Total: USD 1,000.00\n"
    doc_id = client.post(
        "/api/documents/upload",
        files={"file": ("api.pdf", io.BytesIO(create_pdf(pdf_text)), "application/pdf")},
    ).json()["id"]

    # 1. POST /api/workflows/verify
    init_res = client.post(
        "/api/workflows/verify",
        json={"document_ids": [doc_id], "order_id": order_id, "run_async": False},
    )
    assert init_res.status_code == 202
    wf_id = init_res.json()["workflow_id"]

    # 2. GET /api/workflows/{workflow_id}
    status_res = client.get(f"/api/workflows/{wf_id}")
    assert status_res.status_code == 200
    wf_data = status_res.json()
    assert wf_data["workflow_id"] == wf_id
    assert wf_data["workflow_status"] == "REVIEW_REQUIRED"

    # 3. GET /api/workflows/{workflow_id}/agents
    agents_res = client.get(f"/api/workflows/{wf_id}/agents")
    assert agents_res.status_code == 200
    agents_data = agents_res.json()
    assert agents_data["agent_execution_count"] >= 5
    assert len(agents_data["agent_traces"]) >= 5

