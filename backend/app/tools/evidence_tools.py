"""
Evidence retrieval and provenance assembly tools.
"""

from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.database.models import Document, DocumentExtraction, ExtractedField


def lookup_field_evidence(db: Session, document_id: str, field_name: str) -> Optional[Dict[str, Any]]:
    """Retrieves exact page number and source quote for an extracted field."""
    field_record = (
        db.query(ExtractedField)
        .filter(ExtractedField.document_id == document_id, ExtractedField.field_name == field_name)
        .first()
    )
    if field_record:
        doc = db.query(Document).filter(Document.id == document_id).first()
        return {
            "document_id": document_id,
            "filename": doc.original_filename if doc else "unknown",
            "field_name": field_name,
            "value": field_record.value,
            "page_number": field_record.page_number,
            "source_text": field_record.source_text,
            "extraction_method": field_record.extraction_method,
            "confidence": float(field_record.confidence) if field_record.confidence is not None else None,
        }
    return None


def get_page_snippet(db: Session, document_id: str, page_number: int) -> Optional[str]:
    """Retrieves the full extracted text for a specific page."""
    ext = db.query(DocumentExtraction).filter(DocumentExtraction.document_id == document_id).first()
    if ext and ext.pages_json:
        for p in ext.pages_json:
            if p.get("page_number") == page_number:
                return p.get("text")
    return None

