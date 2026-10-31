"""
Tools package exports.
"""

from app.tools.pdf_tools import extract_pdf_pages, check_pdf_density
from app.tools.ocr_tools import is_ocr_available, run_ocr, get_ocr_diagnostic
from app.tools.order_lookup import lookup_order_by_id, match_order_reference, normalize_order_reference
from app.tools.validation_tools import (
    validate_order_reference,
    validate_customer,
    validate_quantity,
    validate_unit_price,
    validate_currency,
    validate_total_amount,
    validate_line_arithmetic,
    validate_required_fields,
    validate_destination,
    validate_payment_terms,
)
from app.tools.document_search import search_documents_by_order, get_document_by_id
from app.tools.evidence_tools import lookup_field_evidence, get_page_snippet

__all__ = [
    "extract_pdf_pages",
    "check_pdf_density",
    "is_ocr_available",
    "run_ocr",
    "get_ocr_diagnostic",
    "lookup_order_by_id",
    "match_order_reference",
    "normalize_order_reference",
    "validate_order_reference",
    "validate_customer",
    "validate_quantity",
    "validate_unit_price",
    "validate_currency",
    "validate_total_amount",
    "validate_line_arithmetic",
    "validate_required_fields",
    "validate_destination",
    "validate_payment_terms",
    "search_documents_by_order",
    "get_document_by_id",
    "lookup_field_evidence",
    "get_page_snippet",
]

