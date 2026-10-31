"""
Dashboard Metrics and Executive Summary API endpoints.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.constants import ReviewStatus, Severity
from app.database.connection import get_db
from app.database.models import AuditLog, Discrepancy, Document, Order
from app.schemas.review import AuditLogResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Metrics"])


class DashboardSummary(BaseModel):
    total_documents: int
    documents_awaiting_review: int
    open_discrepancies: int
    resolved_discrepancies: int
    critical_discrepancies: int
    high_discrepancies: int
    medium_discrepancies: int
    low_discrepancies: int
    total_orders: int
    document_type_breakdown: Dict[str, int]
    recent_activity: List[AuditLogResponse]


@router.get("/summary", response_model=DashboardSummary, summary="Get Verification Dashboard Summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """
    Computes key operational metrics for reviewer oversight.
    """
    total_docs = db.query(Document).count()
    total_orders = db.query(Order).count()

    # Discrepancy counts
    open_discs = db.query(Discrepancy).filter(Discrepancy.review_status == ReviewStatus.PENDING.value).count()
    resolved_discs = db.query(Discrepancy).filter(Discrepancy.review_status != ReviewStatus.PENDING.value).count()

    crit_count = db.query(Discrepancy).filter(
        Discrepancy.severity == Severity.CRITICAL.value,
        Discrepancy.review_status == ReviewStatus.PENDING.value
    ).count()
    high_count = db.query(Discrepancy).filter(
        Discrepancy.severity == Severity.HIGH.value,
        Discrepancy.review_status == ReviewStatus.PENDING.value
    ).count()
    med_count = db.query(Discrepancy).filter(
        Discrepancy.severity == Severity.MEDIUM.value,
        Discrepancy.review_status == ReviewStatus.PENDING.value
    ).count()
    low_count = db.query(Discrepancy).filter(
        Discrepancy.severity == Severity.LOW.value,
        Discrepancy.review_status == ReviewStatus.PENDING.value
    ).count()

    # Documents awaiting review: documents with pending discrepancies
    pending_doc_ids = db.query(Discrepancy.document_id).filter(
        Discrepancy.review_status == ReviewStatus.PENDING.value
    ).distinct().all()
    docs_awaiting_review = len(pending_doc_ids)

    # Document type breakdown
    types = ["invoice", "packing_list", "bill_of_lading", "unknown"]
    breakdown = {}
    for t in types:
        breakdown[t] = db.query(Document).filter(Document.document_type == t).count()

    # Recent activity
    recent_logs = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(10)
        .all()
    )
    activity_resp = [
        AuditLogResponse(
            id=l.id,
            event_type=l.event_type,
            entity_type=l.entity_type,
            entity_id=l.entity_id,
            actor_id=l.actor_id,
            details=l.details,
            created_at=l.created_at,
        )
        for l in recent_logs
    ]

    return DashboardSummary(
        total_documents=total_docs,
        documents_awaiting_review=docs_awaiting_review,
        open_discrepancies=open_discs,
        resolved_discrepancies=resolved_discs,
        critical_discrepancies=crit_count,
        high_discrepancies=high_count,
        medium_discrepancies=med_count,
        low_discrepancies=low_count,
        total_orders=total_orders,
        document_type_breakdown=breakdown,
        recent_activity=activity_resp,
    )

