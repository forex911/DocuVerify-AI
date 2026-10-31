"""
Order retrieval and reference matching tools.
Implements hierarchical matching priority:
1. Exact order ID
2. Exact customer reference
3. Normalized reference match
4. Candidate search / ambiguity detection
"""

import re
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.database.models import Order
from app.services.normalization import normalize_text_semantic


def normalize_order_reference(raw_ref: Optional[str]) -> str:
    """Normalizes order/PO references by removing punctuation, spaces, and leading zeros."""
    if not raw_ref:
        return ""
    cleaned = re.sub(r"[^A-Za-z0-9]", "", raw_ref).upper()
    return cleaned


def lookup_order_by_id(db: Session, order_id: str) -> Optional[Dict[str, Any]]:
    """Looks up an approved order by exact ID or order_number."""
    order = db.query(Order).filter((Order.id == order_id) | (Order.order_number == order_id)).first()
    if order:
        return _order_to_dict(order)
    return None


def match_order_reference(
    db: Session,
    extracted_ref: Optional[str],
    customer_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Hierarchical order matching engine:
    1. Exact order ID
    2. Exact customer reference match
    3. Normalized reference match
    4. Contextual candidate matching
    
    Returns structured match evaluation with ambiguity and escalation flags.
    """
    if not extracted_ref:
        # If reference is missing completely, search candidate orders by customer if available
        if customer_name:
            candidates = _search_orders_by_customer(db, customer_name)
            if len(candidates) == 1:
                return {
                    "matched_order": candidates[0],
                    "match_type": "CUSTOMER_SINGLE_CANDIDATE",
                    "candidates": candidates,
                    "confidence": 0.75,
                    "requires_human_investigation": False,
                    "explanation": f"Matched via customer name '{customer_name}' with single candidate order {candidates[0]['id']}.",
                }
            elif len(candidates) > 1:
                return {
                    "matched_order": None,
                    "match_type": "AMBIGUOUS",
                    "candidates": candidates,
                    "confidence": None,
                    "requires_human_investigation": True,
                    "explanation": f"Extracted reference is missing and customer '{customer_name}' has multiple candidate orders ({len(candidates)} found). Human review required.",
                }
        return {
            "matched_order": None,
            "match_type": "UNMATCHED",
            "candidates": [],
            "confidence": None,
            "requires_human_investigation": True,
            "explanation": "No order reference extracted and customer candidates unavailable.",
        }

    clean_ref = extracted_ref.strip()

    # Priority 1: Exact order ID / order number
    exact = db.query(Order).filter((Order.id == clean_ref) | (Order.order_number == clean_ref)).first()
    if exact:
        return {
            "matched_order": _order_to_dict(exact),
            "match_type": "EXACT_ID",
            "candidates": [_order_to_dict(exact)],
            "confidence": 1.0,
            "requires_human_investigation": False,
            "explanation": f"Exact match found for order identifier '{clean_ref}'.",
        }

    # Priority 2: Normalized reference match
    norm_extracted = normalize_order_reference(clean_ref)
    all_orders = db.query(Order).all()
    norm_matches = []
    for ord_obj in all_orders:
        if normalize_order_reference(ord_obj.id) == norm_extracted or normalize_order_reference(ord_obj.order_number) == norm_extracted:
            norm_matches.append(_order_to_dict(ord_obj))

    if len(norm_matches) == 1:
        return {
            "matched_order": norm_matches[0],
            "match_type": "NORMALIZED_REF",
            "candidates": norm_matches,
            "confidence": 0.95,
            "requires_human_investigation": False,
            "explanation": f"Normalized reference '{norm_extracted}' matched order {norm_matches[0]['id']}.",
        }
    elif len(norm_matches) > 1:
        return {
            "matched_order": None,
            "match_type": "AMBIGUOUS",
            "candidates": norm_matches,
            "confidence": None,
            "requires_human_investigation": True,
            "explanation": f"Multiple orders matched normalized reference '{norm_extracted}'. Human investigation required.",
        }

    # Priority 3: Substring / Customer Candidate Matching
    candidate_matches = []
    for ord_obj in all_orders:
        if norm_extracted in normalize_order_reference(ord_obj.id) or normalize_order_reference(ord_obj.id) in norm_extracted:
            candidate_matches.append(_order_to_dict(ord_obj))

    if len(candidate_matches) == 1:
        return {
            "matched_order": candidate_matches[0],
            "match_type": "CANDIDATE_MATCH",
            "candidates": candidate_matches,
            "confidence": 0.85,
            "requires_human_investigation": False,
            "explanation": f"Candidate match resolved to order {candidate_matches[0]['id']}.",
        }
    elif len(candidate_matches) > 1:
        return {
            "matched_order": None,
            "match_type": "AMBIGUOUS",
            "candidates": candidate_matches,
            "confidence": None,
            "requires_human_investigation": True,
            "explanation": f"Ambiguous match: {len(candidate_matches)} candidate orders found for reference '{clean_ref}'. Human review required.",
        }

    # Unmatched
    return {
        "matched_order": None,
        "match_type": "UNMATCHED",
        "candidates": [],
        "confidence": None,
        "requires_human_investigation": True,
        "explanation": f"No approved order found matching reference '{clean_ref}'.",
    }


def _search_orders_by_customer(db: Session, customer_name: str) -> List[Dict[str, Any]]:
    norm_cust = normalize_text_semantic(customer_name)
    all_orders = db.query(Order).all()
    results = []
    for ord_obj in all_orders:
        if norm_cust in normalize_text_semantic(ord_obj.customer_name):
            results.append(_order_to_dict(ord_obj))
    return results


def _order_to_dict(order: Order) -> Dict[str, Any]:
    return {
        "id": order.id,
        "order_number": order.order_number,
        "customer_name": order.customer_name,
        "currency": order.currency,
        "quantity": float(order.quantity) if order.quantity is not None else None,
        "unit_price": float(order.unit_price) if order.unit_price is not None else None,
        "subtotal": float(order.subtotal) if order.subtotal is not None else None,
        "tax": float(order.tax) if order.tax is not None else None,
        "freight": float(order.freight) if order.freight is not None else None,
        "grand_total": float(order.grand_total) if order.grand_total is not None else None,
        "destination": order.destination,
        "package_count": order.package_count,
        "notes": order.notes,
        "is_authoritative": order.is_authoritative,
    }

