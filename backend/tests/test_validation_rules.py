"""
Tests for Deterministic Validation Rules (ID-001, FIN-001, QTY-001, CUR-001, DEST-001, FIN-002, REQ-001).
"""

import io
from decimal import Decimal
import pymupdf


def create_pdf(text: str) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text(pymupdf.Point(50, 100), text)
    b = doc.tobytes()
    doc.close()
    return b


def setup_test_order(client, order_id="ORD-TEST-1"):
    payload = {
        "order_id": order_id,
        "order_number": order_id,
        "customer_name": "Acme Global",
        "currency": "USD",
        "quantity": "1000.00",
        "unit_price": "25.00",
        "grand_total": "25000.00",
        "destination": "Chennai Port",
        "package_count": 40,
    }
    res = client.post("/api/orders", json=payload)
    assert res.status_code == 201
    return order_id


def test_fin_001_grand_total_mismatch(client):
    order_id = setup_test_order(client, "ORD-FIN-1")

    # Document with total 24,000.00 (mismatch vs 25,000.00)
    pdf_text = (
        "Commercial Invoice\n"
        "Order Ref: ORD-FIN-1\n"
        "Customer: Acme Global\n"
        "Currency: USD\n"
        "Quantity: 1000\n"
        "Destination: Chennai Port\n"
        "Grand Total: USD 24,000.00\n"
    )
    files = {"file": ("inv.pdf", io.BytesIO(create_pdf(pdf_text)), "application/pdf")}
    doc_res = client.post("/api/documents/upload", files=files, data={"order_id": order_id})
    assert doc_res.status_code == 201
    doc_id = doc_res.json()["id"]

    # Run verification
    ver_res = client.post("/api/verification/run", json={"order_id": order_id, "document_ids": [doc_id]})
    assert ver_res.status_code == 200
    summary = ver_res.json()
    assert summary["discrepancies_found"] >= 1
    assert summary["high_count"] >= 1

    # Check discrepancy list
    disc_res = client.get(f"/api/discrepancies?document_id={doc_id}")
    assert disc_res.status_code == 200
    discs = disc_res.json()

    fin_disc = next((d for d in discs if d["rule_id"] == "FIN-001"), None)
    assert fin_disc is not None
    assert fin_disc["severity"] == "HIGH"
    assert fin_disc["expected_value"] == "25000.00"
    assert fin_disc["actual_value"] == "24000.00"
    assert fin_disc["difference"] == "1000.00"
    assert "24,000.00" in fin_disc["source_text"]
    assert fin_disc["source_page"] == 1


def test_id_001_order_reference_mismatch(client):
    order_id = setup_test_order(client, "ORD-ID-MATCH")

    # Document specifies a different order reference
    pdf_text = (
        "Commercial Invoice\n"
        "Order Ref: ORD-DIFFERENT-999\n"
        "Grand Total: USD 25,000.00\n"
    )
    files = {"file": ("inv.pdf", io.BytesIO(create_pdf(pdf_text)), "application/pdf")}
    doc_res = client.post("/api/documents/upload", files=files, data={"order_id": order_id})
    doc_id = doc_res.json()["id"]

    client.post("/api/verification/run", json={"order_id": order_id, "document_ids": [doc_id]})
    discs = client.get(f"/api/discrepancies?document_id={doc_id}&rule_id=ID-001").json()

    assert len(discs) == 1
    assert discs[0]["severity"] == "CRITICAL"
    assert discs[0]["expected_value"] == "ORD-ID-MATCH"
    assert discs[0]["actual_value"] == "ORD-DIFFERENT-999"


def test_qty_001_quantity_mismatch(client):
    order_id = setup_test_order(client, "ORD-QTY-MATCH")

    # Document specifies 800 instead of 1000
    pdf_text = (
        "Commercial Invoice\n"
        "Order Ref: ORD-QTY-MATCH\n"
        "Total Quantity: 800\n"
        "Grand Total: USD 25,000.00\n"
    )
    files = {"file": ("inv.pdf", io.BytesIO(create_pdf(pdf_text)), "application/pdf")}
    doc_id = client.post("/api/documents/upload", files=files, data={"order_id": order_id}).json()["id"]

    client.post("/api/verification/run", json={"order_id": order_id, "document_ids": [doc_id]})
    discs = client.get(f"/api/discrepancies?document_id={doc_id}&rule_id=QTY-001").json()

    assert len(discs) == 1
    assert discs[0]["severity"] == "HIGH"
    assert discs[0]["expected_value"] == "1000.00"
    assert discs[0]["actual_value"] == "800.00"
    assert discs[0]["difference"] == "200.00"


def test_cur_001_currency_mismatch(client):
    order_id = setup_test_order(client, "ORD-CUR-MATCH")

    # Document specifies EUR instead of USD
    pdf_text = (
        "Commercial Invoice\n"
        "Order Ref: ORD-CUR-MATCH\n"
        "Currency: EUR\n"
        "Grand Total: 25,000.00\n"
    )
    files = {"file": ("inv.pdf", io.BytesIO(create_pdf(pdf_text)), "application/pdf")}
    doc_id = client.post("/api/documents/upload", files=files, data={"order_id": order_id}).json()["id"]

    client.post("/api/verification/run", json={"order_id": order_id, "document_ids": [doc_id]})
    discs = client.get(f"/api/discrepancies?document_id={doc_id}&rule_id=CUR-001").json()

    assert len(discs) == 1
    assert discs[0]["severity"] == "CRITICAL"
    assert discs[0]["expected_value"] == "USD"
    assert discs[0]["actual_value"] == "EUR"


def test_clean_sample_no_discrepancies(client):
    order_id = setup_test_order(client, "ORD-CLEAN-1")

    # Perfectly matching invoice
    pdf_text = (
        "Commercial Invoice\n"
        "Order Ref: ORD-CLEAN-1\n"
        "Customer: Acme Global\n"
        "Currency: USD\n"
        "Total Quantity: 1000\n"
        "Destination: Chennai Port\n"
        "Grand Total: USD 25,000.00\n"
    )
    files = {"file": ("clean.pdf", io.BytesIO(create_pdf(pdf_text)), "application/pdf")}
    doc_id = client.post("/api/documents/upload", files=files, data={"order_id": order_id}).json()["id"]

    ver_res = client.post("/api/verification/run", json={"order_id": order_id, "document_ids": [doc_id]})
    assert ver_res.status_code == 200
    summary = ver_res.json()
    assert summary["discrepancies_found"] == 0
    assert summary["clean_documents"] == 1

