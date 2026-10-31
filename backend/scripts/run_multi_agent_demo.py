"""
Multi-Agent Workflow Demonstration Script.
Executes the full LangGraph verification pipeline and displays the specialist agent traces.
"""

from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

DEMO_DIR = Path(__file__).resolve().parent.parent / "demo_files"


def run_multi_agent_demo():
    print("=" * 80)
    print("DOCUVERIFY AI: ENTERPRISE MULTI-AGENT VERIFICATION DEMONSTRATION")
    print("=" * 80)

    client = TestClient(app)

    # 1. Health & Agents
    health = client.get("/api/health").json()
    print(f"\n[1] System Online: {health['status'].upper()} (Version: {health['version']}, Database: {health['database']})")

    # 2. Approved Order
    order_id = "ORD-10245"
    order_res = client.get(f"/api/orders/{order_id}")
    if order_res.status_code == 404:
        from scripts.generate_demo_data import seed_demo_data
        seed_demo_data()
        order = client.get(f"/api/orders/{order_id}").json()
    else:
        order = order_res.json()

    print(f"\n[2] Authoritative Baseline Order: {order['id']}")
    print(f"    Customer: {order['customer_name']} | Currency: {order['currency']}")
    print(f"    Expected Total: ${float(order['grand_total']):,.2f} | Quantity: {order['quantity']} PCS")

    # 3. Upload Document
    mismatch_pdf = DEMO_DIR / "invoice_mismatch_ORD-10245.pdf"
    if not mismatch_pdf.exists():
        from scripts.generate_demo_data import seed_demo_data
        seed_demo_data()

    with open(mismatch_pdf, "rb") as f:
        doc = client.post(
            "/api/documents/upload",
            files={"file": (mismatch_pdf.name, f, "application/pdf")},
            data={"order_id": order_id},
        ).json()
    doc_id = doc["id"]
    print(f"\n[3] Ingested Document: {doc['original_filename']} (ID: {doc_id})")

    # 4. Initiate Multi-Agent LangGraph Workflow
    print(f"\n[4] Dispatching to LangGraph Multi-Agent Orchestrator...")
    init_res = client.post(
        "/api/workflows/verify",
        json={"document_ids": [doc_id], "order_id": order_id, "run_async": False},
    )
    assert init_res.status_code == 202
    wf_id = init_res.json()["workflow_id"]
    print(f"    Workflow ID: {wf_id}")

    # 5. Fetch Agent Execution Trace
    agents_res = client.get(f"/api/workflows/{wf_id}/agents").json()
    print(f"\n[5] Multi-Agent Execution Trace ({agents_res['agent_execution_count']} Steps):")
    for idx, trace in enumerate(agents_res["agent_traces"], 1):
        print(f"    Step {idx}: [{trace['agent_name']}] -> {trace['action']} (Status: {trace['status']})")

    # 6. Fetch Workflow Status & Final Investigation Report
    wf_status = client.get(f"/api/workflows/{wf_id}").json()
    print(f"\n[6] Final Investigation Report:")
    print(f"    Workflow Status: {wf_status['workflow_status']}")
    print(f"    Requires Human Review: {wf_status['requires_human_review']}")
    report = wf_status["final_investigation_report"]
    if report:
        print(f"    Total Discrepancies: {report.get('total_discrepancies')}")
        print(f"    Summary Conclusion: {report.get('summary_conclusion')}")

    # 7. Discrepancy Evidence & Recommendations
    discs = client.get(f"/api/discrepancies?document_id={doc_id}").json()
    print(f"\n[7] Traceable Evidence & Investigation Recommendations:")
    for d in discs:
        print(f"    * Rule: {d['rule_id']} ({d['rule_name']}) | Severity: {d['severity']}")
        print(f"      Expected: {d['expected_value']} | Actual: {d['actual_value']} | Variance: {d['difference']}")
        print(f"      Source Page: {d['source_page']} | Quote: '{d['source_text']}'")
        print(f"      Explanation: {d['explanation']}")

    print("\n" + "=" * 80)
    print("MULTI-AGENT VERIFICATION DEMO COMPLETE: Full auditability preserved.")
    print("=" * 80)


if __name__ == "__main__":
    run_multi_agent_demo()

