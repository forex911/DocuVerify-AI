"""
SQLAlchemy models for DocuVerify AI.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Numeric,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship
from app.database.connection import Base
from app.core.constants import Severity, ReviewStatus


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Order(Base):
    __tablename__ = "orders"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    order_number = Column(String(64), nullable=False, index=True)
    customer_name = Column(String(255), nullable=False, index=True)
    currency = Column(String(10), nullable=False, default="USD")
    quantity = Column(Numeric(14, 4), nullable=True)
    unit_price = Column(Numeric(14, 4), nullable=True)
    subtotal = Column(Numeric(14, 4), nullable=True)
    tax = Column(Numeric(14, 4), nullable=True)
    freight = Column(Numeric(14, 4), nullable=True)
    grand_total = Column(Numeric(14, 4), nullable=False)
    destination = Column(String(255), nullable=True)
    package_count = Column(Integer, nullable=True)
    version = Column(Integer, default=1)
    is_authoritative = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="order")
    discrepancies = relationship("Discrepancy", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(String(64), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    sku = Column(String(64), nullable=True)
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(14, 4), nullable=False)
    unit = Column(String(32), default="PCS")
    unit_price = Column(Numeric(14, 4), nullable=False)
    line_total = Column(Numeric(14, 4), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    order = relationship("Order", back_populates="items")


class DocumentGroup(Base):
    __tablename__ = "document_groups"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(128), nullable=False)
    order_id = Column(String(64), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    documents = relationship("Document", back_populates="group")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    order_id = Column(String(64), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    group_id = Column(String(36), ForeignKey("document_groups.id", ondelete="SET NULL"), nullable=True, index=True)
    filename = Column(String(255), nullable=False)  # Server stored safe filename
    original_filename = Column(String(255), nullable=False)  # User upload filename
    file_path = Column(String(512), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)  # SHA-256
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), default="application/pdf")
    document_type = Column(String(50), default="unknown")  # invoice, packing_list, bill_of_lading, unknown
    status = Column(String(50), default="UPLOADED", index=True)  # UPLOADED, EXTRACTED, VERIFIED, ERROR
    page_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    order = relationship("Order", back_populates="documents")
    group = relationship("DocumentGroup", back_populates="documents")
    extraction = relationship("DocumentExtraction", back_populates="document", uselist=False, cascade="all, delete-orphan")
    extracted_fields = relationship("ExtractedField", back_populates="document", cascade="all, delete-orphan")
    discrepancies = relationship("Discrepancy", back_populates="document", cascade="all, delete-orphan")
    review_decisions = relationship("ReviewDecision", back_populates="document", cascade="all, delete-orphan")


class DocumentExtraction(Base):
    __tablename__ = "document_extractions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(64), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    raw_text = Column(Text, nullable=True)
    pages_json = Column(JSON, nullable=True)  # list of {page_number, text, method, ocr_used}
    page_count = Column(Integer, default=0)
    extraction_method = Column(String(64), default="pymupdf")
    requires_manual_extraction = Column(Boolean, default=False)
    extraction_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    document = relationship("Document", back_populates="extraction")


class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(64), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String(64), nullable=False, index=True)
    value = Column(String(255), nullable=True)
    numeric_value = Column(Numeric(14, 4), nullable=True)
    unit = Column(String(32), nullable=True)
    page_number = Column(Integer, nullable=True)
    source_text = Column(Text, nullable=True)
    extraction_method = Column(String(64), default="pymupdf")
    confidence = Column(Numeric(4, 2), nullable=True)  # Null unless calibrated; never fabricated
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    document = relationship("Document", back_populates="extracted_fields")


class ValidationRule(Base):
    __tablename__ = "validation_rules"

    id = Column(String(32), primary_key=True)  # e.g. ID-001, FIN-001
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=False)
    default_severity = Column(String(20), nullable=False, default=Severity.HIGH.value)
    version = Column(String(20), default="1.0.0")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    discrepancies = relationship("Discrepancy", back_populates="rule")


class Discrepancy(Base):
    __tablename__ = "discrepancies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(64), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(String(64), ForeignKey("orders.id", ondelete="CASCADE"), nullable=True, index=True)
    field_name = Column(String(64), nullable=False, index=True)
    discrepancy_type = Column(String(64), nullable=False)
    severity = Column(String(20), nullable=False, index=True)  # CRITICAL, HIGH, MEDIUM, LOW
    expected_value = Column(String(255), nullable=True)
    actual_value = Column(String(255), nullable=True)
    difference = Column(String(255), nullable=True)
    rule_id = Column(String(32), ForeignKey("validation_rules.id"), nullable=False, index=True)
    rule_version = Column(String(20), default="1.0.0")
    source_page = Column(Integer, nullable=True)
    source_text = Column(Text, nullable=True)
    explanation = Column(Text, nullable=False)
    review_status = Column(String(32), default=ReviewStatus.PENDING.value, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("document_id", "rule_id", "field_name", name="uq_discrepancy_doc_rule_field"),
    )

    document = relationship("Document", back_populates="discrepancies")
    order = relationship("Order", back_populates="discrepancies")
    rule = relationship("ValidationRule", back_populates="discrepancies")
    review_decisions = relationship("ReviewDecision", back_populates="discrepancy", cascade="all, delete-orphan")


class ReviewDecision(Base):
    __tablename__ = "review_decisions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    discrepancy_id = Column(String(36), ForeignKey("discrepancies.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(64), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(String(128), nullable=False)
    action = Column(String(50), nullable=False)
    comment = Column(Text, nullable=False)  # Reviewer comment required for submitted decisions
    previous_status = Column(String(32), nullable=False)
    new_status = Column(String(32), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    discrepancy = relationship("Discrepancy", back_populates="review_decisions")
    document = relationship("Document", back_populates="review_decisions")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_type = Column(String(64), nullable=False, index=True)
    entity_type = Column(String(64), nullable=False, index=True)
    entity_id = Column(String(64), nullable=False, index=True)
    actor_id = Column(String(128), nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_type = Column(String(64), nullable=False, index=True)
    target_id = Column(String(64), nullable=False)
    status = Column(String(32), default="PENDING", index=True)
    details = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)

