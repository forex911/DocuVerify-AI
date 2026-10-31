"""
Pydantic schemas for Human Review Decisions and Audit Trail.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.core.constants import ReviewStatus


class ReviewDecisionCreate(BaseModel):
    action: ReviewStatus = Field(
        ...,
        description="Reviewer decision action: ACCEPT_WITH_JUSTIFICATION, REQUEST_CORRECTION, REJECT, ESCALATE, KEEP_PENDING"
    )
    comment: str = Field(
        ...,
        min_length=1,
        description="Mandatory reviewer rationale/justification for the submitted decision"
    )
    reviewer_id: str = Field(
        default="human_reviewer_demo",
        min_length=1,
        description="Identifier of the human reviewer making the decision"
    )

    @field_validator("comment")
    @classmethod
    def validate_non_empty_comment(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Reviewer comment cannot be empty or pure whitespace.")
        return trimmed


class ReviewDecisionResponse(BaseModel):
    id: str
    discrepancy_id: str
    document_id: str
    reviewer_id: str
    action: str
    comment: str
    previous_status: str
    new_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogResponse(BaseModel):
    id: str
    event_type: str
    entity_type: str
    entity_id: str
    actor_id: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
