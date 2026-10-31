"""
Deterministic validation tools executed by Agent 4 (Validation Agent).
Strict Rule: All arithmetic and comparisons are performed in Python with Decimal, never by LLMs.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.core.constants import RuleID, Severity, RULE_DEFINITIONS
from app.services.explanation_service import ExplanationService
from app.services.normalization import normalize_currency, normalize_text_semantic


def validate_order_reference(
    expected_ref: str,
    actual_ref: Optional[str],
    document_id: str,
    page_number: Optional[int] = None,
    source_text: Optional[str] = None,
    doc_type: str = "document",
) -> Optional[Dict[str, Any]]:
    """Rule ID-001: Order reference mismatch."""
    rule = RULE_DEFINITIONS[RuleID.ID_001.value]
    if not actual_ref:
        return None

    clean_exp = normalize_text_semantic(expected_ref)
    clean_act = normalize_text_semantic(actual_ref)

    if clean_exp != clean_act and clean_exp not in clean_act and clean_act not in clean_exp:
        expl = ExplanationService.generate_explanation(
            rule_id=RuleID.ID_001.value,
            field_name="order_reference",
            expected_val=expected_ref,
            actual_val=actual_ref,
            difference="Identifier mismatch",
            doc_type=doc_type,
        )
        return {
            "document_id": document_id,
            "field_name": "order_reference",
            "discrepancy_type": "ORDER_IDENTITY_MISMATCH",
            "severity": rule["default_severity"],
            "expected_value": expected_ref,
            "actual_value": actual_ref,
            "difference": "Does not match approved order identifier",
            "rule_id": RuleID.ID_001.value,
            "rule_version": rule["version"],
            "source_page": page_number,
            "source_text": source_text,
            "explanation": expl,
        }
    return None


def validate_customer(
    expected_customer: str,
    actual_customer: Optional[str],
    document_id: str,
    page_number: Optional[int] = None,
    source_text: Optional[str] = None,
    doc_type: str = "document",
) -> Optional[Dict[str, Any]]:
    """Validates buyer/customer name match."""
    if not actual_customer or not expected_customer:
        return None

    clean_exp = normalize_text_semantic(expected_customer)
    clean_act = normalize_text_semantic(actual_customer)

    if clean_exp != clean_act and clean_exp not in clean_act and clean_act not in clean_exp:
        return {
            "document_id": document_id,
            "field_name": "customer_name",
            "discrepancy_type": "CUSTOMER_MISMATCH",
            "severity": Severity.MEDIUM.value,
            "expected_value": expected_customer,
            "actual_value": actual_customer,
            "difference": "Customer name differs",
            "rule_id": "CUST-001",
            "rule_version": "1.0.0",
            "source_page": page_number,
            "source_text": source_text,
            "explanation": f"The {doc_type} specifies customer '{actual_customer}', which differs from approved '{expected_customer}'.",
        }
    return None


def validate_quantity(
    expected_qty: Decimal,
    actual_qty: Optional[Decimal],
    document_id: str,
    tolerance: Optional[Decimal] = None,
    page_number: Optional[int] = None,
    source_text: Optional[str] = None,
    doc_type: str = "document",
) -> Optional[Dict[str, Any]]:
    """Rule QTY-001: Quantity mismatch."""
    rule = RULE_DEFINITIONS[RuleID.QTY_001.value]
    if actual_qty is None:
        return None

    tol = tolerance if tolerance is not None else settings.QUANTITY_TOLERANCE
    diff = abs(expected_qty - actual_qty)

    if diff > tol:
        expl = ExplanationService.generate_explanation(
            rule_id=RuleID.QTY_001.value,
            field_name="quantity",
            expected_val=f"{expected_qty:.2f}",
            actual_val=f"{actual_qty:.2f}",
            difference=f"{diff:.2f}",
            doc_type=doc_type,
        )
        return {
            "document_id": document_id,
            "field_name": "quantity",
            "discrepancy_type": "QUANTITY_MISMATCH",
            "severity": rule["default_severity"],
            "expected_value": f"{expected_qty:.2f}",
            "actual_value": f"{actual_qty:.2f}",
            "difference": f"{diff:.2f}",
            "rule_id": RuleID.QTY_001.value,
            "rule_version": rule["version"],
            "source_page": page_number,
            "source_text": source_text,
            "explanation": expl,
        }
    return None


def validate_total_amount(
    expected_total: Decimal,
    actual_total: Optional[Decimal],
    document_id: str,
    currency: str = "USD",
    tolerance: Optional[Decimal] = None,
    page_number: Optional[int] = None,
    source_text: Optional[str] = None,
    doc_type: str = "invoice",
) -> Optional[Dict[str, Any]]:
    """Rule FIN-001: Grand total financial mismatch."""
    rule = RULE_DEFINITIONS[RuleID.FIN_001.value]
    if actual_total is None:
        return None

    tol = tolerance if tolerance is not None else settings.FINANCIAL_TOLERANCE
    diff = abs(expected_total - actual_total)

    if diff > tol:
        expl = ExplanationService.generate_explanation(
            rule_id=RuleID.FIN_001.value,
            field_name="grand_total",
            expected_val=f"{expected_total:.2f}",
            actual_val=f"{actual_total:.2f}",
            difference=f"{diff:.2f}",
            doc_type=doc_type,
            currency=currency,
        )
        return {
            "document_id": document_id,
            "field_name": "grand_total",
            "discrepancy_type": "FINANCIAL_MISMATCH",
            "severity": rule["default_severity"],
            "expected_value": f"{expected_total:.2f}",
            "actual_value": f"{actual_total:.2f}",
            "difference": f"{diff:.2f}",
            "rule_id": RuleID.FIN_001.value,
            "rule_version": rule["version"],
            "source_page": page_number,
            "source_text": source_text,
            "explanation": expl,
        }
    return None


def validate_currency(
    expected_currency: str,
    actual_currency: Optional[str],
    document_id: str,
    page_number: Optional[int] = None,
    source_text: Optional[str] = None,
    doc_type: str = "document",
) -> Optional[Dict[str, Any]]:
    """Rule CUR-001: Currency mismatch."""
    rule = RULE_DEFINITIONS[RuleID.CUR_001.value]
    if not actual_currency:
        return None

    norm_exp = normalize_currency(expected_currency)
    norm_act = normalize_currency(actual_currency)

    if norm_exp and norm_act and norm_exp != norm_act:
        expl = ExplanationService.generate_explanation(
            rule_id=RuleID.CUR_001.value,
            field_name="currency",
            expected_val=norm_exp,
            actual_val=norm_act,
            difference="Currency code mismatch",
            doc_type=doc_type,
        )
        return {
            "document_id": document_id,
            "field_name": "currency",
            "discrepancy_type": "CURRENCY_MISMATCH",
            "severity": rule["default_severity"],
            "expected_value": norm_exp,
            "actual_value": norm_act,
            "difference": f"Expected {norm_exp}, found {norm_act}",
            "rule_id": RuleID.CUR_001.value,
            "rule_version": rule["version"],
            "source_page": page_number,
            "source_text": source_text,
            "explanation": expl,
        }
    return None


def validate_unit_price(
    expected_price: Decimal,
    actual_price: Optional[Decimal],
    document_id: str,
    page_number: Optional[int] = None,
    source_text: Optional[str] = None,
    doc_type: str = "document",
) -> Optional[Dict[str, Any]]:
    """Validates item unit price."""
    if actual_price is None:
        return None

    diff = abs(expected_price - actual_price)
    if diff > Decimal("0.01"):
        return {
            "document_id": document_id,
            "field_name": "unit_price",
            "discrepancy_type": "UNIT_PRICE_MISMATCH",
            "severity": Severity.HIGH.value,
            "expected_value": f"{expected_price:.2f}",
            "actual_value": f"{actual_price:.2f}",
            "difference": f"{diff:.2f}",
            "rule_id": "PRC-001",
            "rule_version": "1.0.0",
            "source_page": page_number,
            "source_text": source_text,
            "explanation": f"Unit price in {doc_type} ({actual_price:.2f}) differs from approved order ({expected_price:.2f}).",
        }
    return None


def validate_line_arithmetic(
    items: List[Any],
    subtotal: Optional[Decimal],
    document_id: str,
    doc_type: str = "document",
) -> List[Dict[str, Any]]:
    """Rule FIN-002: Line item arithmetic verification."""
    discs = []
    rule = RULE_DEFINITIONS[RuleID.FIN_002.value]

    sum_lines = Decimal("0.00")
    for item in items:
        if isinstance(item, dict):
            qty = Decimal(str(item.get("quantity", 0)))
            price = Decimal(str(item.get("unit_price", 0)))
            actual_line = Decimal(str(item.get("line_total", 0)))
            page_num = item.get("page_number")
            source_text = item.get("source_text")
            desc = item.get("description", "item")
        else:
            qty = Decimal(str(getattr(item, "quantity", 0)))
            price = Decimal(str(getattr(item, "unit_price", 0)))
            actual_line = Decimal(str(getattr(item, "line_total", 0)))
            page_num = getattr(item, "page_number", None)
            source_text = getattr(item, "source_text", None)
            desc = getattr(item, "description", "item")

        expected_line = qty * price
        diff = abs(expected_line - actual_line)

        if diff > Decimal("0.01"):
            discs.append({
                "document_id": document_id,
                "field_name": "line_total",
                "discrepancy_type": "ARITHMETIC_MISMATCH",
                "severity": rule["default_severity"],
                "expected_value": f"{expected_line:.2f}",
                "actual_value": f"{actual_line:.2f}",
                "difference": f"{diff:.2f}",
                "rule_id": RuleID.FIN_002.value,
                "rule_version": rule["version"],
                "source_page": page_num,
                "source_text": source_text,
                "explanation": f"Line total mismatch for '{desc}': {qty} * {price} = {expected_line:.2f}, but line states {actual_line:.2f}.",
            })
        sum_lines += actual_line

    if subtotal is not None and items:
        subtotal_dec = Decimal(str(subtotal))
        diff_sub = abs(sum_lines - subtotal_dec)
        if diff_sub > Decimal("0.01"):
            discs.append({
                "document_id": document_id,
                "field_name": "subtotal",
                "discrepancy_type": "ARITHMETIC_MISMATCH",
                "severity": rule["default_severity"],
                "expected_value": f"{sum_lines:.2f}",
                "actual_value": f"{subtotal_dec:.2f}",
                "difference": f"{diff_sub:.2f}",
                "rule_id": RuleID.FIN_002.value,
                "rule_version": rule["version"],
                "source_page": None,
                "source_text": None,
                "explanation": f"Sum of item rows ({sum_lines:.2f}) does not match parsed subtotal ({subtotal_dec:.2f}).",
            })

    return discs


def validate_required_fields(
    doc_type: str,
    present_fields: Dict[str, Any],
    document_id: str,
) -> List[Dict[str, Any]]:
    """Rule REQ-001: Required commercial field verification."""
    discs = []
    rule = RULE_DEFINITIONS[RuleID.REQ_001.value]

    required_map = {
        "invoice": ["order_reference", "grand_total"],
        "packing_list": ["order_reference"],
        "bill_of_lading": ["order_reference", "destination"],
    }
    needed = required_map.get(doc_type.lower(), ["order_reference"])

    for field in needed:
        val = present_fields.get(field)
        if val is None or val == "":
            discs.append({
                "document_id": document_id,
                "field_name": field,
                "discrepancy_type": "REQUIRED_FIELD_MISSING",
                "severity": rule["default_severity"],
                "expected_value": "Present in document",
                "actual_value": "Missing / Null",
                "difference": "Field not found",
                "rule_id": RuleID.REQ_001.value,
                "rule_version": rule["version"],
                "source_page": None,
                "source_text": None,
                "explanation": f"Required commercial field '{field}' is missing or could not be parsed from {doc_type}.",
            })
    return discs


def validate_destination(
    expected_dest: str,
    actual_dest: Optional[str],
    document_id: str,
    page_number: Optional[int] = None,
    source_text: Optional[str] = None,
    doc_type: str = "document",
) -> Optional[Dict[str, Any]]:
    """Rule DEST-001: Destination mismatch."""
    rule = RULE_DEFINITIONS[RuleID.DEST_001.value]
    if not actual_dest or not expected_dest:
        return None

    clean_exp = normalize_text_semantic(expected_dest)
    clean_act = normalize_text_semantic(actual_dest)

    if clean_exp != clean_act and clean_exp not in clean_act and clean_act not in clean_exp:
        return {
            "document_id": document_id,
            "field_name": "destination",
            "discrepancy_type": "DESTINATION_MISMATCH",
            "severity": rule["default_severity"],
            "expected_value": expected_dest,
            "actual_value": actual_dest,
            "difference": "Destination mismatch",
            "rule_id": RuleID.DEST_001.value,
            "rule_version": rule["version"],
            "source_page": page_number,
            "source_text": source_text,
            "explanation": f"Destination in {doc_type} ('{actual_dest}') differs from approved destination ('{expected_dest}').",
        }
    return None


def validate_payment_terms(
    expected_terms: Optional[str],
    actual_terms: Optional[str],
    document_id: str,
    page_number: Optional[int] = None,
    source_text: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Validates payment terms (e.g., Net 30, COD, LC)."""
    if not expected_terms or not actual_terms:
        return None

    if normalize_text_semantic(expected_terms) != normalize_text_semantic(actual_terms):
        return {
            "document_id": document_id,
            "field_name": "payment_terms",
            "discrepancy_type": "PAYMENT_TERMS_MISMATCH",
            "severity": Severity.MEDIUM.value,
            "expected_value": expected_terms,
            "actual_value": actual_terms,
            "difference": "Terms differ",
            "rule_id": "TERM-001",
            "rule_version": "1.0.0",
            "source_page": page_number,
            "source_text": source_text,
            "explanation": f"Document payment terms ('{actual_terms}') do not match order agreement ('{expected_terms}').",
        }
    return None

