"""
Tests for Discrepancy Idempotency, Evidence Traceability, and Query Filters.
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


def test_idempotent_verification_no_duplicates(client):
    order_id = "ORD-IDEMP-1"
    client.post(
        "/api/orders",
        json={
            "order_id": order_id,
            "order_number": order_id,
            "customer_name": "Idempotent Corp",
            "currency": "USD",
            "grand_total": "50000.00",
        },
    )

    pdf_text = (
        "Commercial Invoice\n"
        "Order Ref: ORD-IDEMP-1\n"
        "Grand Total: USD 45,000.00\n"
    )
    doc_id = client.post(
        "/api/documents/upload",
        files={"file": ("inv.pdf", io.BytesIO(create_pdf(pdf_text)), "application/pdf")},
        data={"order_id": order_id},
    ).json()["id"]

    # Run verification Run 1
    res1 = client.post("/api/verification/run", json={"order_id": order_id, "document_ids": [doc_id]})
    assert res1.status_code == 200
    assert res1.json()["discrepancies_found"] == 1

    discs1 = client.get(f"/api/discrepancies?document_id={doc_id}").json()
    assert len(discs1) == 1
    disc_id_1 = discs1[0]["id"]

    # Run verification Run 2 (repeated)
    res2 = client.post("/api/verification/run", json={"order_id": order_id, "document_ids": [doc_id]})
    assert res2.status_code == 200
    assert res2.json()["discrepancies_found"] == 1

    discs2 = client.get(f"/api/discrepancies?document_id={doc_id}").json()
    # Must NOT create duplicate discrepancy
    assert len(discs2) == 1
    assert discs2[0]["id"] == disc_id_1


def test_discrepancy_filtering(client):
    order_id = "ORD-FILTER-1"
    client.post(
        "/api/orders",
        json={
            "order_id": order_id,
            "order_number": order_id,
            "customer_name": "Filter Corp",
            "currency": "USD",
            "grand_total": "30000.00",
            "quantity": "500",
        },
    )

    # Document with total mismatch (HIGH) and quantity mismatch (HIGH)
    pdf_text = (
        "Commercial Invoice\n"
        "Order Ref: ORD-FILTER-1\n"
        "Quantity: 400\n"
        "Grand Total: USD 28,000.00\n"
    )
    doc_id = client.post(
        "/api/documents/upload",
        files={"file": ("inv.pdf", io.BytesIO(create_pdf(pdf_text)), "application/pdf")},
        data={"order_id": order_id},
    ).json()["id"]

    client.post("/api/verification/run", json={"order_id": order_id, "document_ids": [doc_id]})

    # Filter by severity
    high_discs = client.get("/api/discrepancies?severity=HIGH").json()
    assert len(high_discs) >= 2

    # Filter by rule ID
    fin_discs = client.get(f"/api/discrepancies?rule_id=FIN-001&document_id={doc_id}").json()
    assert len(fin_discs) == 1
    assert fin_discs[0]["field_name"] == "grand_total"

