"""
Tests for Cross-Document Consistency Rules (XDOC-001, XDOC-002, XDOC-003).
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


def test_cross_document_quantity_mismatch(client):
    # Setup order
    order_id = "ORD-XDOC-1"
    client.post(
        "/api/orders",
        json={
            "order_id": order_id,
            "order_number": order_id,
            "customer_name": "ABC Trade",
            "currency": "USD",
            "quantity": "1000",
            "grand_total": "25000.00",
        },
    )

    # Document 1: Invoice with 1000 PCS
    inv_text = (
        "Commercial Invoice\n"
        "Order Ref: ORD-XDOC-1\n"
        "Total Quantity: 1000\n"
        "Grand Total: USD 25,000.00\n"
    )
    doc1_id = client.post(
        "/api/documents/upload",
        files={"file": ("inv.pdf", io.BytesIO(create_pdf(inv_text)), "application/pdf")},
        data={"order_id": order_id},
    ).json()["id"]

    # Document 2: Packing list with 850 PCS
    pl_text = (
        "Packing List\n"
        "Order Ref: ORD-XDOC-1\n"
        "Total Quantity: 850\n"
        "Total Packages: 40\n"
    )
    doc2_id = client.post(
        "/api/documents/upload",
        files={"file": ("pl.pdf", io.BytesIO(create_pdf(pl_text)), "application/pdf")},
        data={"order_id": order_id},
    ).json()["id"]

    # Run verification on both documents together
    res = client.post("/api/verification/run", json={"order_id": order_id, "document_ids": [doc1_id, doc2_id]})
    assert res.status_code == 200

    discs = client.get(f"/api/discrepancies?rule_id=XDOC-001").json()
    assert len(discs) >= 1
    xdoc_disc = discs[0]
    assert xdoc_disc["rule_id"] == "XDOC-001"
    assert xdoc_disc["severity"] == "HIGH"
    assert "850" in xdoc_disc["actual_value"] or "850" in xdoc_disc["expected_value"]
    assert xdoc_disc["difference"] == "150"


def test_cross_document_package_count_mismatch(client):
    order_id = "ORD-XDOC-PKG"
    client.post(
        "/api/orders",
        json={
            "order_id": order_id,
            "order_number": order_id,
            "customer_name": "ABC Trade",
            "currency": "USD",
            "grand_total": "10000.00",
            "package_count": 40,
        },
    )

    # Document 1: Packing List with 40 packages
    pl_text = (
        "Packing List\n"
        "Order Ref: ORD-XDOC-PKG\n"
        "Total Packages: 40\n"
    )
    doc1_id = client.post(
        "/api/documents/upload",
        files={"file": ("pl.pdf", io.BytesIO(create_pdf(pl_text)), "application/pdf")},
        data={"order_id": order_id},
    ).json()["id"]

    # Document 2: Bill of Lading with 35 packages
    bl_text = (
        "Ocean Bill of Lading\n"
        "Order Ref: ORD-XDOC-PKG\n"
        "Total Packages: 35\n"
        "Port of Discharge: Chennai Port\n"
    )
    doc2_id = client.post(
        "/api/documents/upload",
        files={"file": ("bl.pdf", io.BytesIO(create_pdf(bl_text)), "application/pdf")},
        data={"order_id": order_id},
    ).json()["id"]

    res = client.post("/api/verification/run", json={"order_id": order_id, "document_ids": [doc1_id, doc2_id]})
    assert res.status_code == 200

    discs = client.get(f"/api/discrepancies?rule_id=XDOC-002").json()
    assert len(discs) >= 1
    assert discs[0]["rule_id"] == "XDOC-002"
    assert discs[0]["severity"] == "MEDIUM"
    assert discs[0]["difference"] == "5"

