"""
Tests for PDF Upload Validation, Security, and File Handling.
"""

import io
import pymupdf


def create_dummy_pdf_bytes(text: str = "Test Document Content") -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text(pymupdf.Point(50, 100), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_valid_pdf_upload(client):
    pdf_bytes = create_dummy_pdf_bytes("Invoice No: INV-100\nOrder Ref: ORD-10245\nTotal: USD 25,000.00")
    files = {"file": ("invoice.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    response = client.post("/api/documents/upload", files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["id"].startswith("DOC-")
    assert data["original_filename"] == "invoice.pdf"
    assert data["status"] == "EXTRACTED"
    assert data["page_count"] == 1
    assert "file_hash" in data


def test_reject_non_pdf_extension(client):
    files = {"file": ("malicious.txt", io.BytesIO(b"Hello world"), "text/plain")}
    response = client.post("/api/documents/upload", files=files)
    assert response.status_code == 400
    assert "Only PDF documents" in response.json()["detail"]


def test_reject_fake_pdf_header(client):
    # Extension is .pdf, but file content doesn't start with %PDF-
    fake_content = b"Not really a PDF file at all"
    files = {"file": ("spoofed.pdf", io.BytesIO(fake_content), "application/pdf")}
    response = client.post("/api/documents/upload", files=files)
    assert response.status_code == 400
    assert "valid PDF format" in response.json()["detail"]


def test_reject_empty_file(client):
    files = {"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")}
    response = client.post("/api/documents/upload", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_path_traversal_prevention(client):
    pdf_bytes = create_dummy_pdf_bytes("Some content")
    # File name with path traversal
    files = {"file": ("../../etc/passwd.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    response = client.post("/api/documents/upload", files=files)
    assert response.status_code == 201
    data = response.json()
    # The server filename must not contain directory slashes
    assert "/" not in data["filename"]
    assert "\\" not in data["filename"]

