"""
Documents API endpoints: upload, ingestion, extraction, and retrieval.
"""

from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import Document, DocumentExtraction, ExtractedField, Order
from app.schemas.document import (
    CanonicalDocument,
    DocumentDetailResponse,
    DocumentExtractionResponse,
    DocumentResponse,
    ExtractionPageResponse,
)
from app.services.audit_service import AuditService
from app.services.field_extractor import FieldExtractor
from app.services.pdf_extractor import PDFExtractor, PDFExtractionError
from app.utils.file_handler import save_uploaded_pdf

router = APIRouter(prefix="/documents", tags=["Documents Ingestion & Extraction"])


def build_canonical_document(doc: Document, extraction: Optional[DocumentExtraction]) -> CanonicalDocument:
    """Reconstructs the CanonicalDocument from DB records."""
    pages = extraction.pages_json if extraction and extraction.pages_json else []
    return FieldExtractor.extract_fields(
        document_id=doc.id,
        filename=doc.original_filename,
        pages=pages,
        document_type_hint=doc.document_type,
    )


@router.post("/upload", response_model=DocumentDetailResponse, status_code=status.HTTP_201_CREATED, summary="Upload & Ingest Commercial PDF")
async def upload_document(
    file: UploadFile = File(..., description="PDF document file (Invoice, Packing List, Bill of Lading)"),
    order_id: Optional[str] = Form(None, description="Optional approved order ID to associate with"),
    document_type: Optional[str] = Form(None, description="Optional document type override (invoice, packing_list, bill_of_lading)"),
    db: Session = Depends(get_db),
):
    """
    Securely uploads a commercial PDF document, extracts text page-by-page, and constructs canonical fields.
    """
    # Verify order exists if order_id is provided
    if order_id:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Associated Order ID '{order_id}' does not exist.",
            )

    # 1. Save and validate PDF safely
    doc_id, server_filename, file_path, file_hash, file_size = await save_uploaded_pdf(file)

    # 2. Create document record
    doc = Document(
        id=doc_id,
        order_id=order_id,
        filename=server_filename,
        original_filename=file.filename or "uploaded.pdf",
        file_path=str(file_path),
        file_hash=file_hash,
        file_size=file_size,
        mime_type="application/pdf",
        document_type=document_type.lower() if document_type else "unknown",
        status="UPLOADED",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 3. Extract text page-by-page using PyMuPDF
    try:
        extraction_result = PDFExtractor.extract_document(file_path)
    except PDFExtractionError as e:
        doc.status = "ERROR"
        doc.error_message = str(e)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"PDF extraction error: {str(e)}",
        )
    except Exception as e:
        doc.status = "ERROR"
        doc.error_message = f"Unexpected extraction error: {str(e)}"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the PDF.",
        )

    # 4. Save extraction record
    extraction = DocumentExtraction(
        document_id=doc.id,
        raw_text=extraction_result["full_text"],
        pages_json=extraction_result["pages"],
        page_count=extraction_result["page_count"],
        extraction_method=extraction_result["extraction_method"],
        requires_manual_extraction=extraction_result["requires_manual_extraction"],
        extraction_metadata=extraction_result["extraction_metadata"],
    )
    db.add(extraction)
    doc.page_count = extraction_result["page_count"]

    # 5. Extract canonical business fields
    canonical = FieldExtractor.extract_fields(
        document_id=doc.id,
        filename=doc.original_filename,
        pages=extraction_result["pages"],
        document_type_hint=doc.document_type if doc.document_type != "unknown" else None,
    )

    # Update classified document type if not overridden
    if doc.document_type == "unknown" and canonical.document_type != "unknown":
        doc.document_type = canonical.document_type

    # Save individual extracted fields for granular SQL indexing
    for field_name, prov in canonical.fields.items():
        ef = ExtractedField(
            document_id=doc.id,
            field_name=field_name,
            value=prov.value,
            numeric_value=prov.numeric_value,
            unit=prov.unit,
            page_number=prov.page_number,
            source_text=prov.source_text,
            extraction_method=prov.extraction_method,
            confidence=prov.confidence,
        )
        db.add(ef)

    doc.status = "EXTRACTED"
    db.commit()
    db.refresh(doc)

    # 6. Audit log
    AuditService.log_event(
        db=db,
        event_type="DOCUMENT_UPLOADED",
        entity_type="DOCUMENT",
        entity_id=doc.id,
        actor_id="system",
        details={
            "original_filename": doc.original_filename,
            "document_type": doc.document_type,
            "pages": doc.page_count,
            "order_id": doc.order_id,
        },
    )

    return DocumentDetailResponse(
        id=doc.id,
        order_id=doc.order_id,
        group_id=doc.group_id,
        filename=doc.filename,
        original_filename=doc.original_filename,
        file_hash=doc.file_hash,
        file_size=doc.file_size,
        mime_type=doc.mime_type,
        document_type=doc.document_type,
        status=doc.status,
        page_count=doc.page_count,
        error_message=doc.error_message,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        canonical_document=canonical,
        requires_manual_extraction=extraction.requires_manual_extraction,
        extraction_method=extraction.extraction_method,
    )


@router.get("", response_model=List[DocumentResponse], summary="List Ingested Documents")
def list_documents(
    order_id: Optional[str] = None,
    document_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Lists uploaded documents with optional filtering."""
    query = db.query(Document)
    if order_id:
        query = query.filter(Document.order_id == order_id)
    if document_type:
        query = query.filter(Document.document_type == document_type.lower())
    if status:
        query = query.filter(Document.status == status.upper())

    return query.order_by(Document.created_at.desc()).all()


@router.get("/{document_id}", response_model=DocumentDetailResponse, summary="Get Document Details & Extracted Fields")
def get_document(document_id: str, db: Session = Depends(get_db)):
    """Retrieves document details and its structured canonical fields."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )

    extraction = db.query(DocumentExtraction).filter(DocumentExtraction.document_id == document_id).first()
    canonical = build_canonical_document(doc, extraction) if extraction else None

    return DocumentDetailResponse(
        id=doc.id,
        order_id=doc.order_id,
        group_id=doc.group_id,
        filename=doc.filename,
        original_filename=doc.original_filename,
        file_hash=doc.file_hash,
        file_size=doc.file_size,
        mime_type=doc.mime_type,
        document_type=doc.document_type,
        status=doc.status,
        page_count=doc.page_count,
        error_message=doc.error_message,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        canonical_document=canonical,
        requires_manual_extraction=extraction.requires_manual_extraction if extraction else False,
        extraction_method=extraction.extraction_method if extraction else None,
    )


@router.get("/{document_id}/extraction", response_model=DocumentExtractionResponse, summary="Get Raw Extraction & Page Breakdown")
def get_document_extraction(document_id: str, db: Session = Depends(get_db)):
    """Retrieves full extraction breakdown page by page, including OCR usage and limitations."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )

    extraction = db.query(DocumentExtraction).filter(DocumentExtraction.document_id == document_id).first()
    if not extraction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Extraction records not found for document '{document_id}'.",
        )

    pages_resp = [
        ExtractionPageResponse(
            page_number=p.get("page_number", 1),
            text=p.get("text", ""),
            char_count=p.get("char_count", len(p.get("text", ""))),
            method=p.get("method", "pymupdf"),
            ocr_used=p.get("ocr_used", False),
        )
        for p in (extraction.pages_json or [])
    ]

    canonical = build_canonical_document(doc, extraction)

    return DocumentExtractionResponse(
        document_id=doc.id,
        raw_text=extraction.raw_text,
        pages=pages_resp,
        page_count=extraction.page_count,
        extraction_method=extraction.extraction_method,
        requires_manual_extraction=extraction.requires_manual_extraction,
        canonical_document=canonical,
        created_at=extraction.created_at,
    )


@router.get("/{document_id}/file", summary="Stream Original PDF Document")
def get_document_file(document_id: str, db: Session = Depends(get_db)):
    """Streams the raw PDF file for inline PDF rendering and downloading."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )
    file_path = Path(doc.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physical document file missing on server.",
        )
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=doc.original_filename,
        content_disposition_type="inline",
        headers={
            "X-Content-Type-Options": "nosniff",
            "Access-Control-Allow-Origin": "*",
        },
    )


