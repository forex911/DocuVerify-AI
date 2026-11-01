"""
Discrepancy Engine: persists, updates, and retrieves discrepancies idempotently.
Ensures repeated verification runs do not generate duplicate records or wipe human decisions.
"""

import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.constants import ReviewStatus
from app.database.models import Discrepancy, Document, ValidationRule
from app.schemas.discrepancy import DiscrepancyCreate, DiscrepancyResponse


class DiscrepancyEngine:
    """Manages discrepancy persistence, idempotency, and querying."""

    @classmethod
    def persist_discrepancies(
        cls, db: Session, discrepancies: List[DiscrepancyCreate]
    ) -> List[Discrepancy]:
        """
        Idempotently persists discrepancies.
        If a discrepancy already exists for (document_id, rule_id, field_name):
            - Preserves existing human review decision / status!
            - Updates values, difference, and evidence if changed.
        If new:
            - Inserts with PENDING review status.
        """
        persisted: List[Discrepancy] = []

        for d in discrepancies:
            existing = (
                db.query(Discrepancy)
                .filter(
                    Discrepancy.document_id == d.document_id,
                    Discrepancy.rule_id == d.rule_id,
                    Discrepancy.field_name == d.field_name,
                )
                .first()
            )

            if existing:
                # Update evidence and values, but preserve human review status
                existing.expected_value = d.expected_value
                existing.actual_value = d.actual_value
                existing.difference = d.difference
                existing.severity = d.severity
                existing.rule_version = d.rule_version
                existing.source_page = d.source_page
                existing.source_text = d.source_text
                existing.explanation = d.explanation
                existing.order_id = d.order_id or existing.order_id
                persisted.append(existing)
            else:
                disc_id = f"DISC-{uuid.uuid4().hex[:8].upper()}"
                new_disc = Discrepancy(
                    id=disc_id,
                    document_id=d.document_id,
                    order_id=d.order_id,
                    field_name=d.field_name,
                    discrepancy_type=d.discrepancy_type,
                    severity=d.severity,
                    expected_value=d.expected_value,
                    actual_value=d.actual_value,
                    difference=d.difference,
                    rule_id=d.rule_id,
                    rule_version=d.rule_version,
                    source_page=d.source_page,
                    source_text=d.source_text,
                    explanation=d.explanation,
                    review_status=ReviewStatus.PENDING.value,
                )
                db.add(new_disc)
                persisted.append(new_disc)

        db.commit()
        for p in persisted:
            db.refresh(p)
        return persisted

    @classmethod
    def list_discrepancies(
        cls,
        db: Session,
        discrepancy_id: Optional[str] = None,
        document_id: Optional[str] = None,
        order_id: Optional[str] = None,
        severity: Optional[str] = None,
        review_status: Optional[str] = None,
        rule_id: Optional[str] = None,
    ) -> List[DiscrepancyResponse]:
        """Queries discrepancies with flexible filtering and joins document metadata."""
        query = db.query(Discrepancy).join(Document, Discrepancy.document_id == Document.id, isouter=True)

        if discrepancy_id:
            query = query.filter(Discrepancy.id == discrepancy_id)
        if document_id:
            query = query.filter(Discrepancy.document_id == document_id)
        if order_id:
            query = query.filter(Discrepancy.order_id == order_id)
        if severity:
            query = query.filter(Discrepancy.severity == severity.upper())
        if review_status:
            query = query.filter(Discrepancy.review_status == review_status.upper())
        if rule_id:
            query = query.filter(Discrepancy.rule_id == rule_id.upper())

        query = query.order_by(Discrepancy.created_at.desc())
        items = query.all()

        responses: List[DiscrepancyResponse] = []
        for item in items:
            doc = item.document
            rule = db.query(ValidationRule).filter(ValidationRule.id == item.rule_id).first()
            resp = DiscrepancyResponse(
                id=item.id,
                document_id=item.document_id,
                order_id=item.order_id,
                field_name=item.field_name,
                discrepancy_type=item.discrepancy_type,
                severity=item.severity,
                expected_value=item.expected_value,
                actual_value=item.actual_value,
                difference=item.difference,
                rule_id=item.rule_id,
                rule_version=item.rule_version,
                source_page=item.source_page,
                source_text=item.source_text,
                explanation=item.explanation,
                review_status=item.review_status,
                document_filename=doc.original_filename if doc else None,
                document_type=doc.document_type if doc else None,
                rule_name=rule.name if rule else item.rule_id,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            responses.append(resp)

        return responses

