"""
Audit and Review Decision Service.
Ensures an immutable, append-only history of reviewer actions and system events.
Enforces that only humans make final verification determinations.
"""

import uuid
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.constants import ReviewStatus
from app.database.models import AuditLog, Discrepancy, ReviewDecision
from app.schemas.review import AuditLogResponse, ReviewDecisionResponse


class AuditService:
    """Manages immutable audit logging and human review decision recording."""

    @classmethod
    def log_event(
        cls,
        db: Session,
        event_type: str,
        entity_type: str,
        entity_id: str,
        actor_id: str = "system",
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Appends an event to the immutable audit log."""
        log_entry = AuditLog(
            id=str(uuid.uuid4()),
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            details=details or {},
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry

    @classmethod
    def record_decision(
        cls,
        db: Session,
        discrepancy_id: str,
        action: str,
        comment: str,
        reviewer_id: str,
    ) -> ReviewDecisionResponse:
        """
        Records a human reviewer's decision on a discrepancy.
        Enforces non-empty comment, updates discrepancy status, and appends to audit log.
        """
        disc = db.query(Discrepancy).filter(Discrepancy.id == discrepancy_id).first()
        if not disc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Discrepancy with ID '{discrepancy_id}' not found.",
            )

        trimmed_comment = comment.strip()
        if not trimmed_comment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A non-empty reviewer comment is mandatory for submitting a verification decision.",
            )

        action_upper = action.upper()
        valid_actions = {s.value for s in ReviewStatus}
        if action_upper not in valid_actions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action '{action}'. Permitted actions: {', '.join(valid_actions)}",
            )

        prev_status = disc.review_status
        new_status = action_upper

        # Update discrepancy status
        disc.review_status = new_status

        # Create immutable ReviewDecision
        decision = ReviewDecision(
            id=str(uuid.uuid4()),
            discrepancy_id=disc.id,
            document_id=disc.document_id,
            reviewer_id=reviewer_id,
            action=action_upper,
            comment=trimmed_comment,
            previous_status=prev_status,
            new_status=new_status,
        )
        db.add(decision)

        # Append to Audit Log
        audit_entry = AuditLog(
            id=str(uuid.uuid4()),
            event_type="HUMAN_REVIEW_DECISION",
            entity_type="DISCREPANCY",
            entity_id=disc.id,
            actor_id=reviewer_id,
            details={
                "document_id": disc.document_id,
                "order_id": disc.order_id,
                "field_name": disc.field_name,
                "rule_id": disc.rule_id,
                "action": action_upper,
                "comment": trimmed_comment,
                "previous_status": prev_status,
                "new_status": new_status,
            },
        )
        db.add(audit_entry)

        db.commit()
        db.refresh(decision)

        return ReviewDecisionResponse(
            id=decision.id,
            discrepancy_id=decision.discrepancy_id,
            document_id=decision.document_id,
            reviewer_id=decision.reviewer_id,
            action=decision.action,
            comment=decision.comment,
            previous_status=decision.previous_status,
            new_status=decision.new_status,
            created_at=decision.created_at,
        )

    @classmethod
    def list_audit_logs(
        cls,
        db: Session,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditLogResponse]:
        """Queries audit log entries in reverse chronological order."""
        query = db.query(AuditLog)
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        if entity_id:
            query = query.filter(AuditLog.entity_id == entity_id)
        if event_type:
            query = query.filter(AuditLog.event_type == event_type)

        items = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
        return [
            AuditLogResponse(
                id=item.id,
                event_type=item.event_type,
                entity_type=item.entity_type,
                entity_id=item.entity_id,
                actor_id=item.actor_id,
                details=item.details,
                created_at=item.created_at,
            )
            for item in items
        ]

