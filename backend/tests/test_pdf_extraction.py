"""
Tests for PDF Extraction and Limitations Reporting.
"""

import io
import pymupdf


def test_pdf_extraction_page_provenance(client):
    # Create multi-page PDF
    doc = pymupdf.open()
    p1 = doc.new_page()
    p1.insert_text(pymupdf.Point(50, 100), "Commercial Invoice Header\nOrder Ref: ORD-10245")
    p2 = doc.new_page()
    p2.insert_text(pymupdf.Point(50, 100), "Destination: Chennai Port\nGrand Total: USD 25,000.00")
    pdf_bytes = doc.tobytes()
    doc.close()

    files = {"file": ("multipage.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    upload_res = client.post("/api/documents/upload", files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # Check extraction endpoint
    ext_res = client.get(f"/api/documents/{doc_id}/extraction")
    assert ext_res.status_code == 200
    ext_data = ext_res.json()
    assert ext_data["page_count"] == 2
    assert len(ext_data["pages"]) == 2
    assert ext_data["pages"][0]["page_number"] == 1
    assert "ORD-10245" in ext_data["pages"][0]["text"]
    assert ext_data["pages"][1]["page_number"] == 2
    assert "25,000.00" in ext_data["pages"][1]["text"]


def test_scanned_page_honest_limitations(client):
    # Create an empty/scanned page PDF (no text)
    doc = pymupdf.open()
    doc.new_page()  # Blank page with 0 text
    pdf_bytes = doc.tobytes()
    doc.close()

    files = {"file": ("scanned_blank.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    upload_res = client.post("/api/documents/upload", files=files)
    assert upload_res.status_code == 201
    data = upload_res.json()
    assert data["requires_manual_extraction"] is True

    # Verify extraction report
    ext_res = client.get(f"/api/documents/{data['id']}/extraction")
    assert ext_res.status_code == 200
    ext_data = ext_res.json()
    assert ext_data["requires_manual_extraction"] is True

