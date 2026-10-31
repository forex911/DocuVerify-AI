"""
Tests for Human Review Decisions, Mandatory Comments, Decision Persistence, and Audit Trail.
"""

import io
import pymupdf


def create_pdf(text: str) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text(pymupdf.Point(50, 100), text)
    b = doc.tobytes()
    doc.close()
    return b


def setup_order_and_discrepancy(client):
    order_id = "ORD-REV-1"
    client.post(
        "/api/orders",
        json={
            "order_id": order_id,
            "order_number": order_id,
            "customer_name": "Review Corp",
            "currency": "USD",
            "grand_total": "20000.00",
        },
    )

    pdf_text = "Commercial Invoice\nOrder Ref: ORD-REV-1\nGrand Total: USD 19,000.00\n"
    doc_id = client.post(
        "/api/documents/upload",
        files={"file": ("inv.pdf", io.BytesIO(create_pdf(pdf_text)), "application/pdf")},
        data={"order_id": order_id},
    ).json()["id"]

    client.post("/api/verification/run", json={"order_id": order_id, "document_ids": [doc_id]})
    discs = client.get(f"/api/discrepancies?document_id={doc_id}").json()
    assert len(discs) == 1
    return discs[0]["id"]


def test_mandatory_comment_validation(client):
    disc_id = setup_order_and_discrepancy(client)

    # Empty comment must fail
    res_empty = client.post(
        f"/api/discrepancies/{disc_id}/decision",
        json={"action": "ACCEPT_WITH_JUSTIFICATION", "comment": "   ", "reviewer_id": "auditor_1"},
    )
    assert res_empty.status_code in (400, 422)

    # Missing comment must fail
    res_missing = client.post(
        f"/api/discrepancies/{disc_id}/decision",
        json={"action": "ACCEPT_WITH_JUSTIFICATION", "reviewer_id": "auditor_1"},
    )
    assert res_missing.status_code in (400, 422)


def test_decision_persistence_and_audit(client):
    disc_id = setup_order_and_discrepancy(client)

    decision_payload = {
        "action": "ACCEPT_WITH_JUSTIFICATION",
        "comment": "Pre-approved $1,000 contractual volume discount per amendment #4.",
        "reviewer_id": "senior_auditor_jane",
    }
    decision_res = client.post(f"/api/discrepancies/{disc_id}/decision", json=decision_payload)
    assert decision_res.status_code == 200
    dec_data = decision_res.json()
    assert dec_data["action"] == "ACCEPT_WITH_JUSTIFICATION"
    assert dec_data["previous_status"] == "PENDING"
    assert dec_data["new_status"] == "ACCEPT_WITH_JUSTIFICATION"
    assert dec_data["comment"] == decision_payload["comment"]

    # Verify discrepancy status persisted
    disc_check = client.get(f"/api/discrepancies/{disc_id}").json()
    assert disc_check["review_status"] == "ACCEPT_WITH_JUSTIFICATION"

    # Verify immutable audit log
    audit_res = client.get(f"/api/audit?entity_id={disc_id}")
    assert audit_res.status_code == 200
    logs = audit_res.json()
    assert len(logs) >= 1
    audit_entry = next((l for l in logs if l["event_type"] == "HUMAN_REVIEW_DECISION"), None)
    assert audit_entry is not None
    assert audit_entry["actor_id"] == "senior_auditor_jane"
    assert audit_entry["details"]["new_status"] == "ACCEPT_WITH_JUSTIFICATION"

    # Verify dashboard summary reflects updated counts
    dash_res = client.get("/api/dashboard/summary").json()
    assert dash_res["resolved_discrepancies"] >= 1

