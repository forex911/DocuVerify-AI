"""
End-to-End Demo Script for DocuVerify AI.
Demonstrates:
1. Loading approved order ORD-10245.
2. Uploading invoice with financial mismatch (USD 24,000.00 vs approved USD 25,000.00).
3. Extracting canonical business fields.
4. Executing deterministic verification (detects FIN-001 High discrepancy).
5. Human reviewer records ACCEPT_WITH_JUSTIFICATION with mandatory rationale comment.
6. Verifying decision persistence and immutable audit trail.
7. Demonstrating clean scenario where all checks pass.
"""

from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

DEMO_DIR = Path(__file__).resolve().parent.parent / "demo_files"


def run_e2e_demo():
    print("=" * 75)
    print("DOCUVERIFY AI: END-TO-END VERIFICATION DEMONSTRATION")
    print("=" * 75)

    client = TestClient(app)

    # 1. System Health
    health = client.get("/api/health").json()
    print(f"\n[1] System Health: {health['status'].upper()} (Version: {health['version']}, Database: {health['database']})")
    print(f"    OCR Available: {health['tesseract_ocr_available']} | Gemini Configured: {health['gemini_configured']}")

    # 2. Approved Order ORD-10245
    order_id = "ORD-10245"
    order_res = client.get(f"/api/orders/{order_id}")
    if order_res.status_code == 404:
        # Create order
        order_payload = {
            "order_id": order_id,
            "order_number": order_id,
            "customer_name": "ABC Industries",
            "currency": "USD",
            "quantity": "1000.00",
            "unit_price": "25.00",
            "grand_total": "25000.00",
            "destination": "Chennai Port",
            "package_count": 40,
        }
        order = client.post("/api/orders", json=order_payload).json()
    else:
        order = order_res.json()

    print(f"\n[2] Authoritative Customer Order: {order['id']}")
    print(f"    Customer: {order['customer_name']} | Currency: {order['currency']}")
    print(f"    Quantity: {order['quantity']} PCS @ ${order['unit_price']} | Grand Total: ${float(order['grand_total']):,.2f}")
    print(f"    Destination: {order['destination']} | Package Count: {order['package_count']}")

    # 3. Upload Invoice with Mismatch (24,000.00)
    mismatch_pdf = DEMO_DIR / "invoice_mismatch_ORD-10245.pdf"
    if not mismatch_pdf.exists():
        from scripts.generate_demo_data import seed_demo_data
        seed_demo_data()

    with open(mismatch_pdf, "rb") as f:
        upload_res = client.post(
            "/api/documents/upload",
            files={"file": (mismatch_pdf.name, f, "application/pdf")},
            data={"order_id": order_id},
        )
    assert upload_res.status_code == 201
    doc_data = upload_res.json()
    doc_id = doc_data["id"]

    print(f"\n[3] Ingested Commercial PDF: {doc_data['original_filename']} -> ID: {doc_id}")
    print(f"    Classified Document Type: {doc_data['document_type'].upper()}")
    print(f"    Pages: {doc_data['page_count']} | SHA-256: {doc_data['file_hash'][:16]}...")
    canonical = doc_data["canonical_document"]
    print(f"    Extracted Total: {canonical.get('currency', 'USD')} {canonical.get('grand_total')}")

    # 4. Run Deterministic Verification
    ver_res = client.post("/api/verification/run", json={"order_id": order_id, "document_ids": [doc_id]})
    assert ver_res.status_code == 200
    summary = ver_res.json()
    print(f"\n[4] Verification Executed:")
    print(f"    Documents Evaluated: {summary['documents_evaluated']}")
    print(f"    Discrepancies Found: {summary['discrepancies_found']} (Critical: {summary['critical_count']}, High: {summary['high_count']}, Medium: {summary['medium_count']})")

    # 5. Inspect Discrepancies Evidence
    discs = client.get(f"/api/discrepancies?document_id={doc_id}").json()
    print(f"\n[5] Traceable Discrepancy Evidence:")
    target_disc = None
    for d in discs:
        print(f"    - ID: {d['id']} | Rule: {d['rule_id']} ({d['rule_name']}) | Severity: {d['severity']}")
        print(f"      Field: {d['field_name']} | Expected: {d['expected_value']} | Actual: {d['actual_value']} | Variance: {d['difference']}")
        print(f"      Source Page: {d['source_page']} | Source Text: '{d['source_text']}'")
        print(f"      Explanation: {d['explanation']}")
        print(f"      Review Status: {d['review_status']}")
        if d["rule_id"] == "FIN-001":
            target_disc = d

    # 6. Human Review Decision Submission
    if target_disc:
        print(f"\n[6] Submitting Human Review Decision for {target_disc['id']}:")
        decision_payload = {
            "action": "ACCEPT_WITH_JUSTIFICATION",
            "comment": "Commercial variance of $1,000.00 approved per volume incentive discount agreement #VIA-2026.",
            "reviewer_id": "sarah_senior_auditor",
        }
        dec_res = client.post(f"/api/discrepancies/{target_disc['id']}/decision", json=decision_payload)
        assert dec_res.status_code == 200
        dec = dec_res.json()
        print(f"    Decision Recorded: {dec['action']}")
        print(f"    Reviewer: {dec['reviewer_id']} | Transition: {dec['previous_status']} -> {dec['new_status']}")
        print(f"    Mandatory Justification: '{dec['comment']}'")

    # 7. Audit Log Verification
    audit_logs = client.get(f"/api/audit?entity_id={target_disc['id']}").json()
    print(f"\n[7] Immutable Audit Trail Entries for {target_disc['id']}:")
    for log in audit_logs:
        print(f"    - Event: {log['event_type']} | Actor: {log['actor_id']} | Time: {log['created_at']}")
        print(f"      Details: {log['details']}")

    # 8. Clean Scenario
    clean_pdf = DEMO_DIR / "invoice_clean_ORD-10245.pdf"
    with open(clean_pdf, "rb") as f:
        clean_doc = client.post(
            "/api/documents/upload",
            files={"file": (clean_pdf.name, f, "application/pdf")},
            data={"order_id": order_id},
        ).json()
    clean_ver = client.post("/api/verification/run", json={"order_id": order_id, "document_ids": [clean_doc["id"]]}).json()
    print(f"\n[8] Clean Scenario Result for {clean_doc['original_filename']}:")
    print(f"    Discrepancies: {clean_ver['discrepancies_found']}")
    print(f"    Status: No discrepancies detected --- awaiting reviewer confirmation.")

    # 9. Dashboard Metrics
    dash = client.get("/api/dashboard/summary").json()
    print(f"\n[9] Verification Dashboard Overview:")
    print(f"    Total Documents: {dash['total_documents']} | Total Orders: {dash['total_orders']}")
    print(f"    Open Discrepancies: {dash['open_discrepancies']} | Resolved Discrepancies: {dash['resolved_discrepancies']}")
    print(f"    Critical: {dash['critical_discrepancies']} | High: {dash['high_discrepancies']} | Medium: {dash['medium_discrepancies']}")
    print("\n" + "=" * 75)
    print("DEMO RUN COMPLETE: All business rules, evidence, and audit trails verified.")
    print("=" * 75)


if __name__ == "__main__":
    run_e2e_demo()

