"""
Pydantic schemas for Discrepancy Evidence and Verification.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.core.constants import Severity, ReviewStatus


class DiscrepancyBase(BaseModel):
    document_id: str
    order_id: Optional[str] = None
    field_name: str
    discrepancy_type: str
    severity: str
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    difference: Optional[str] = None
    rule_id: str
    rule_version: str = "1.0.0"
    source_page: Optional[int] = None
    source_text: Optional[str] = None
    explanation: str
    review_status: str = ReviewStatus.PENDING.value


class DiscrepancyCreate(DiscrepancyBase):
    pass


class DiscrepancyResponse(DiscrepancyBase):
    id: str
    document_filename: Optional[str] = None
    document_type: Optional[str] = None
    rule_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VerificationRequest(BaseModel):
    order_id: str
    document_ids: Optional[list[str]] = None
    group_id: Optional[str] = None


class VerificationSummary(BaseModel):
    order_id: str
    documents_evaluated: int
    discrepancies_found: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    clean_documents: int
    timestamp: datetime
