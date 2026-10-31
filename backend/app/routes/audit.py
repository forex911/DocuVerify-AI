"""
Audit Trail API endpoints.
Provides append-only immutable history of human decisions and verification events.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.review import AuditLogResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["Audit Trail"])


@router.get("", response_model=List[AuditLogResponse], summary="Retrieve Immutable Audit Log")
def get_audit_trail(
    entity_type: Optional[str] = Query(None, description="Filter by entity type (ORDER, DOCUMENT, DISCREPANCY)"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(100, ge=1, le=500, description="Max log entries to retrieve"),
    db: Session = Depends(get_db),
):
    """
    Returns an append-only audit log of reviewer determinations, document uploads, and system operations.
    """
    return AuditService.list_audit_logs(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=event_type,
        limit=limit,
    )

