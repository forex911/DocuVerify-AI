"""
Verification API: runs deterministic comparison engine across documents and approved orders.
"""

from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.constants import Severity
from app.database.connection import get_db
from app.database.models import Document, DocumentExtraction, Order
from app.schemas.discrepancy import VerificationRequest, VerificationSummary
from app.schemas.document import CanonicalDocument
from app.schemas.order import OrderResponse
from app.services.audit_service import AuditService
from app.services.comparison_engine import ComparisonEngine
from app.services.discrepancy_engine import DiscrepancyEngine
from app.services.explanation_service import ExplanationService
from app.services.field_extractor import FieldExtractor

router = APIRouter(prefix="/verification", tags=["Document Verification Engine"])


@router.post("/run", response_model=VerificationSummary, summary="Execute Verification Rules")
def run_verification(payload: VerificationRequest, db: Session = Depends(get_db)):
    """
    Executes deterministic verification rules for one or more documents against the approved order.
    Idempotent: Re-running verification updates evidence but preserves any previously recorded human review decisions.
    """
    # 1. Fetch Order
    order = db.query(Order).filter(Order.id == payload.order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approved Order '{payload.order_id}' not found.",
        )
    order_resp = OrderResponse.model_validate(order)

    # 2. Fetch Documents to verify
    query = db.query(Document)
    if payload.document_ids:
        query = query.filter(Document.id.in_(payload.document_ids))
    elif payload.group_id:
        query = query.filter(Document.group_id == payload.group_id)
    else:
        query = query.filter(Document.order_id == payload.order_id)

    documents = query.all()
    if not documents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No documents found to verify for order '{payload.order_id}'. Please upload documents first.",
        )

    # 3. Build canonical representations
    canonical_docs: List[CanonicalDocument] = []
    for doc in documents:
        extraction = db.query(DocumentExtraction).filter(DocumentExtraction.document_id == doc.id).first()
        pages = extraction.pages_json if extraction and extraction.pages_json else []
        c_doc = FieldExtractor.extract_fields(
            document_id=doc.id,
            filename=doc.original_filename,
            pages=pages,
            document_type_hint=doc.document_type,
        )
        canonical_docs.append(c_doc)

    # 4. Run single document vs order checks
    all_raw_discrepancies = []
    for c_doc in canonical_docs:
        discs = ComparisonEngine.compare_document_to_order(c_doc, order_resp)
        all_raw_discrepancies.extend(discs)

    # 5. Run cross-document consistency checks
    cross_discs = ComparisonEngine.compare_cross_documents(canonical_docs, order_id=order.id)
    all_raw_discrepancies.extend(cross_discs)

    # 6. Optional Gemini explanation refinement (never changes values or severity)
    for d in all_raw_discrepancies:
        d.explanation = ExplanationService.enhance_with_gemini(
            deterministic_explanation=d.explanation,
            context_dict={
                "rule_id": d.rule_id,
                "field": d.field_name,
                "expected": d.expected_value,
                "actual": d.actual_value,
                "difference": d.difference,
            },
        )

    # 7. Persist idempotently
    persisted = DiscrepancyEngine.persist_discrepancies(db, all_raw_discrepancies)

    # 8. Update document status
    for doc in documents:
        doc.status = "VERIFIED"
        doc.order_id = order.id
    db.commit()

    # 9. Calculate summary metrics
    crit_count = sum(1 for p in persisted if p.severity == Severity.CRITICAL.value)
    high_count = sum(1 for p in persisted if p.severity == Severity.HIGH.value)
    med_count = sum(1 for p in persisted if p.severity == Severity.MEDIUM.value)
    low_count = sum(1 for p in persisted if p.severity == Severity.LOW.value)

    doc_ids_with_discs = {p.document_id for p in persisted}
    clean_docs = len([d for d in documents if d.id not in doc_ids_with_discs])

    # 10. Audit log
    AuditService.log_event(
        db=db,
        event_type="VERIFICATION_EXECUTED",
        entity_type="ORDER",
        entity_id=order.id,
        actor_id="system",
        details={
            "documents_count": len(documents),
            "discrepancies_count": len(persisted),
            "critical": crit_count,
            "high": high_count,
        },
    )

    return VerificationSummary(
        order_id=order.id,
        documents_evaluated=len(documents),
        discrepancies_found=len(persisted),
        critical_count=crit_count,
        high_count=high_count,
        medium_count=med_count,
        low_count=low_count,
        clean_documents=clean_docs,
        timestamp=datetime.now(timezone.utc),
    )

