"""
Normalization utilities for currencies, units, financial figures, and text.
Ensures deterministic, conservative conversions without guessing.
"""

import re
from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple


def normalize_whitespace(text: Optional[str]) -> Optional[str]:
    """Collapses multiple spaces, newlines, and tabs into a single clean string."""
    if text is None:
        return None
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned if cleaned else None


def normalize_currency(raw_currency: Optional[str]) -> Optional[str]:
    """
    Normalizes unambiguous currency representations to ISO 4217 standard codes.
    Returns uppercase ISO code or None.
    """
    if not raw_currency:
        return None
    raw = raw_currency.strip().upper()

    mapping = {
        "$": "USD",
        "USD": "USD",
        "US DOLLAR": "USD",
        "US DOLLARS": "USD",
        "EUR": "EUR",
        "€": "EUR",
        "EURO": "EUR",
        "EUROS": "EUR",
        "GBP": "GBP",
        "£": "GBP",
        "POUND": "GBP",
        "POUNDS": "GBP",
        "INR": "INR",
        "₹": "INR",
        "RUPEE": "INR",
        "RUPEES": "INR",
        "CAD": "CAD",
        "AUD": "AUD",
        "JPY": "JPY",
        "¥": "JPY",
        "CNY": "CNY",
        "RMB": "CNY",
    }
    return mapping.get(raw, raw if len(raw) == 3 and raw.isalpha() else None)


def parse_decimal_value(raw_val: Optional[str]) -> Tuple[Optional[Decimal], Optional[str]]:
    """
    Parses a string into a Decimal, extracting currency prefix/suffix if present.
    Example: 'USD 24,000.00' -> (Decimal('24000.00'), 'USD')
    Example: '$1,250.50' -> (Decimal('1250.50'), 'USD')
    Returns (Decimal or None, detected_currency or None).
    """
    if not raw_val:
        return None, None

    clean_str = raw_val.strip()
    detected_currency = None

    # Check currency symbols or codes
    for sym, code in [("$", "USD"), ("€", "EUR"), ("£", "GBP"), ("₹", "INR"), ("¥", "JPY")]:
        if sym in clean_str:
            detected_currency = code
            clean_str = clean_str.replace(sym, "")

    # Check for text codes like USD, EUR, etc.
    code_match = re.search(r"\b(USD|EUR|GBP|INR|CAD|AUD|JPY|CNY)\b", clean_str, re.IGNORECASE)
    if code_match:
        detected_currency = code_match.group(1).upper()
        clean_str = re.sub(r"\b" + code_match.group(1) + r"\b", "", clean_str, flags=re.IGNORECASE)

    # Strip unwanted characters except numbers, decimal point, comma, and minus
    cleaned_num = re.sub(r"[^\d.,\-]", "", clean_str).strip()
    if not cleaned_num:
        return None, detected_currency

    # Handle commas vs dots (e.g. 24,000.00 vs 24.000,00)
    if "," in cleaned_num and "." in cleaned_num:
        if cleaned_num.rfind(",") > cleaned_num.rfind("."):
            # European format: 1.000,50 -> 1000.50
            cleaned_num = cleaned_num.replace(".", "").replace(",", ".")
        else:
            # Standard format: 1,000.50 -> 1000.50
            cleaned_num = cleaned_num.replace(",", "")
    elif "," in cleaned_num and "." not in cleaned_num:
        # Check if comma is decimal (e.g. 1000,50) or thousand separator (e.g. 24,000)
        parts = cleaned_num.split(",")
        if len(parts) == 2 and len(parts[1]) in (1, 2):
            cleaned_num = cleaned_num.replace(",", ".")
        else:
            cleaned_num = cleaned_num.replace(",", "")

    try:
        dec = Decimal(cleaned_num)
        return dec, detected_currency
    except InvalidOperation:
        return None, detected_currency


def normalize_unit(unit: Optional[str]) -> Optional[str]:
    """
    Normalizes unambiguous unit representations.
    """
    if not unit:
        return None
    raw = unit.strip().upper()
    mapping = {
        "PCS": "PCS",
        "PC": "PCS",
        "PIECE": "PCS",
        "PIECES": "PCS",
        "UNIT": "PCS",
        "UNITS": "PCS",
        "KG": "KG",
        "KGS": "KG",
        "KILOGRAM": "KG",
        "KILOGRAMS": "KG",
        "CTN": "CTN",
        "CTNS": "CTN",
        "CARTON": "CTN",
        "CARTONS": "CTN",
        "BOX": "BOX",
        "BOXES": "BOX",
        "PLT": "PLT",
        "PALLET": "PLT",
        "PALLETS": "PLT",
        "MTR": "MTR",
        "METERS": "MTR",
        "METRES": "MTR",
        "MT": "MT",
        "TON": "MT",
        "TONS": "MT",
    }
    return mapping.get(raw, raw)


def normalize_text_semantic(text: Optional[str]) -> str:
    """Standardizes string comparison by trimming and lowercasing."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip().lower()

