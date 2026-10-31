"""
Pydantic schemas for Document Ingestion, Extraction, and Canonical Representation.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class ExtractedFieldProvenance(BaseModel):
    field_name: str
    value: Optional[str] = None
    numeric_value: Optional[Decimal] = None
    unit: Optional[str] = None
    source_document_id: Optional[str] = None
    page_number: Optional[int] = None
    source_text: Optional[str] = None
    extraction_method: str = "pymupdf"
    confidence: Optional[float] = None  # None unless calibrated; never fabricated


class DocumentItemSchema(BaseModel):
    sku: Optional[str] = None
    description: str
    quantity: Decimal
    unit: Optional[str] = "PCS"
    unit_price: Decimal
    line_total: Decimal
    page_number: Optional[int] = None
    source_text: Optional[str] = None


class CanonicalDocument(BaseModel):
    document_id: str
    filename: str
    document_type: str = "unknown"
    order_reference: Optional[str] = None
    customer_name: Optional[str] = None
    currency: Optional[str] = None
    items: List[DocumentItemSchema] = []
    subtotal: Optional[Decimal] = None
    tax: Optional[Decimal] = None
    freight: Optional[Decimal] = None
    grand_total: Optional[Decimal] = None
    destination: Optional[str] = None
    package_count: Optional[int] = None
    gross_weight: Optional[str] = None
    fields: Dict[str, ExtractedFieldProvenance] = Field(default_factory=dict)
    source_pages: Dict[str, Optional[int]] = Field(default_factory=dict)


class ExtractionPageResponse(BaseModel):
    page_number: int
    text: str
    char_count: int
    method: str = "pymupdf"
    ocr_used: bool = False


class DocumentExtractionResponse(BaseModel):
    document_id: str
    raw_text: Optional[str] = None
    pages: List[ExtractionPageResponse] = []
    page_count: int = 0
    extraction_method: str = "pymupdf"
    requires_manual_extraction: bool = False
    canonical_document: Optional[CanonicalDocument] = None
    created_at: datetime


class DocumentResponse(BaseModel):
    id: str
    order_id: Optional[str] = None
    group_id: Optional[str] = None
    filename: str
    original_filename: str
    file_hash: str
    file_size: int
    mime_type: str
    document_type: str
    status: str
    page_count: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailResponse(DocumentResponse):
    canonical_document: Optional[CanonicalDocument] = None
    requires_manual_extraction: bool = False
    extraction_method: Optional[str] = None
