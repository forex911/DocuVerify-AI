"""
Constants and definitions for DocuVerify AI.
"""

from enum import Enum
from typing import Dict, Any


class DocumentType(str, Enum):
    INVOICE = "invoice"
    PACKING_LIST = "packing_list"
    BILL_OF_LADING = "bill_of_lading"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ReviewStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPT_WITH_JUSTIFICATION = "ACCEPT_WITH_JUSTIFICATION"
    REQUEST_CORRECTION = "REQUEST_CORRECTION"
    REJECT = "REJECT"
    ESCALATE = "ESCALATE"
    KEEP_PENDING = "KEEP_PENDING"


class RuleID(str, Enum):
    ID_001 = "ID-001"
    REQ_001 = "REQ-001"
    QTY_001 = "QTY-001"
    FIN_001 = "FIN-001"
    FIN_002 = "FIN-002"
    CUR_001 = "CUR-001"
    DEST_001 = "DEST-001"
    XDOC_001 = "XDOC-001"
    XDOC_002 = "XDOC-002"
    XDOC_003 = "XDOC-003"


RULE_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    RuleID.ID_001.value: {
        "rule_id": RuleID.ID_001.value,
        "name": "Order Reference Mismatch",
        "description": "Extracted order reference does not match approved order identifier.",
        "default_severity": Severity.CRITICAL.value,
        "version": "1.0.0",
    },
    RuleID.REQ_001.value: {
        "rule_id": RuleID.REQ_001.value,
        "name": "Required Field Missing",
        "description": "A required commercial field is missing or could not be reliably extracted.",
        "default_severity": Severity.HIGH.value,
        "version": "1.0.0",
    },
    RuleID.QTY_001.value: {
        "rule_id": RuleID.QTY_001.value,
        "name": "Quantity Mismatch",
        "description": "Extracted total quantity differs from approved order quantity.",
        "default_severity": Severity.HIGH.value,
        "version": "1.0.0",
    },
    RuleID.FIN_001.value: {
        "rule_id": RuleID.FIN_001.value,
        "name": "Grand Total Mismatch",
        "description": "Extracted document grand total differs from approved order grand total.",
        "default_severity": Severity.HIGH.value,
        "version": "1.0.0",
    },
    RuleID.FIN_002.value: {
        "rule_id": RuleID.FIN_002.value,
        "name": "Line Item Arithmetic Mismatch",
        "description": "Quantity multiplied by unit price does not equal line total, or line totals do not sum to subtotal.",
        "default_severity": Severity.HIGH.value,
        "version": "1.0.0",
    },
    RuleID.CUR_001.value: {
        "rule_id": RuleID.CUR_001.value,
        "name": "Currency Mismatch",
        "description": "Extracted currency does not match approved order currency.",
        "default_severity": Severity.CRITICAL.value,
        "version": "1.0.0",
    },
    RuleID.DEST_001.value: {
        "rule_id": RuleID.DEST_001.value,
        "name": "Destination Mismatch",
        "description": "Extracted delivery/discharge destination differs from approved order destination.",
        "default_severity": Severity.MEDIUM.value,
        "version": "1.0.0",
    },
    RuleID.XDOC_001.value: {
        "rule_id": RuleID.XDOC_001.value,
        "name": "Cross-Document Quantity Mismatch",
        "description": "Quantity differs across related commercial documents (e.g., invoice vs. packing list vs. bill of lading).",
        "default_severity": Severity.HIGH.value,
        "version": "1.0.0",
    },
    RuleID.XDOC_002.value: {
        "rule_id": RuleID.XDOC_002.value,
        "name": "Cross-Document Package Count Mismatch",
        "description": "Package count differs across related commercial documents.",
        "default_severity": Severity.MEDIUM.value,
        "version": "1.0.0",
    },
    RuleID.XDOC_003.value: {
        "rule_id": RuleID.XDOC_003.value,
        "name": "Cross-Document Destination Mismatch",
        "description": "Delivery destination differs across related commercial documents.",
        "default_severity": Severity.MEDIUM.value,
        "version": "1.0.0",
    },
}

