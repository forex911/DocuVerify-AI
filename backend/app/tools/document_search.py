"""
Document search and metadata retrieval tools.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.database.models import Document


def search_documents_by_order(db: Session, order_id: str) -> List[Dict[str, Any]]:
    """Retrieves all documents associated with an approved order."""
    docs = db.query(Document).filter(Document.order_id == order_id).all()
    return [_doc_to_dict(d) for d in docs]


def get_document_by_id(db: Session, document_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves document metadata by document ID."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if doc:
        return _doc_to_dict(doc)
    return None


def _doc_to_dict(doc: Document) -> Dict[str, Any]:
    return {
        "id": doc.id,
        "order_id": doc.order_id,
        "filename": doc.filename,
        "original_filename": doc.original_filename,
        "file_hash": doc.file_hash,
        "file_size": doc.file_size,
        "document_type": doc.document_type,
        "status": doc.status,
        "page_count": doc.page_count,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }

