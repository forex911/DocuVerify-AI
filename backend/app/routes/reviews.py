"""
Human Review and Discrepancy Management API endpoints.
Enforces human-in-the-loop decisions with mandatory justification comments.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.discrepancy import DiscrepancyResponse
from app.schemas.review import ReviewDecisionCreate, ReviewDecisionResponse
from app.services.audit_service import AuditService
from app.services.discrepancy_engine import DiscrepancyEngine

router = APIRouter(tags=["Discrepancies & Human Review"])


@router.get("/discrepancies", response_model=List[DiscrepancyResponse], summary="List Discrepancy Records")
def get_discrepancies(
    document_id: Optional[str] = None,
    order_id: Optional[str] = None,
    severity: Optional[str] = None,
    review_status: Optional[str] = None,
    rule_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Retrieves discrepancies with optional filtering by severity, review status, order, or document.
    """
    return DiscrepancyEngine.list_discrepancies(
        db=db,
        document_id=document_id,
        order_id=order_id,
        severity=severity,
        review_status=review_status,
        rule_id=rule_id,
    )


@router.get("/discrepancies/{discrepancy_id}", response_model=DiscrepancyResponse, summary="Get Discrepancy Evidence")
def get_discrepancy_detail(discrepancy_id: str, db: Session = Depends(get_db)):
    """Retrieves full traceable evidence for a specific discrepancy."""
    items = DiscrepancyEngine.list_discrepancies(db=db)
    for item in items:
        if item.id == discrepancy_id:
            return item

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Discrepancy '{discrepancy_id}' not found.",
    )


@router.post(
    "/discrepancies/{discrepancy_id}/decision",
    response_model=ReviewDecisionResponse,
    status_code=status.HTTP_200_OK,
    summary="Record Human Review Decision",
)
def record_review_decision(
    discrepancy_id: str,
    payload: ReviewDecisionCreate,
    db: Session = Depends(get_db),
):
    """
    Records a human reviewer's decision on a discrepancy.
    Requires a non-empty rationale comment. Never permits automated AI approvals.
    """
    return AuditService.record_decision(
        db=db,
        discrepancy_id=discrepancy_id,
        action=payload.action.value,
        comment=payload.comment,
        reviewer_id=payload.reviewer_id,
    )

