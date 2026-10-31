"""
Agent 5: Cross-Document Reconciliation Agent.
Validates multi-document consistency across Invoices, Packing Lists, and Bills of Lading.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.constants import RuleID, Severity, RULE_DEFINITIONS
from app.orchestration.state import WorkflowState
from app.services.explanation_service import ExplanationService
from app.services.normalization import normalize_text_semantic


class ReconciliationAgent:
    """Specialist agent responsible for reconciling commercial documents within a shipment group."""

    AGENT_NAME = "ReconciliationAgent"

    @classmethod
    def execute(cls, state: WorkflowState, db: Session) -> WorkflowState:
        start_time = datetime.now(timezone.utc).isoformat()
        logs = list(state.agent_execution_log)
        all_discrepancies: List[Dict[str, Any]] = list(state.discrepancies)
        cross_results: List[Dict[str, Any]] = []

        docs = list(state.extracted_documents.values())
        if len(docs) < 2:
            logs.append({
                "agent_name": cls.AGENT_NAME,
                "action": "Skipped cross-document reconciliation (fewer than 2 documents in workflow).",
                "status": "SKIPPED",
                "details": {"document_count": len(docs)},
                "timestamp": start_time,
            })
            state.agent_execution_log = logs
            return state

        # XDOC-001: Quantity across related documents
        qty_docs = [d for d in docs if d.get("fields", {}).get("quantity", {}).get("numeric_value") is not None]
        for i in range(len(qty_docs)):
            for j in range(i + 1, len(qty_docs)):
                doc_a, doc_b = qty_docs[i], qty_docs[j]
                val_a = Decimal(str(doc_a["fields"]["quantity"]["numeric_value"]))
                val_b = Decimal(str(doc_b["fields"]["quantity"]["numeric_value"]))
                diff = abs(val_a - val_b)

                if diff > settings.QUANTITY_TOLERANCE:
                    rule = RULE_DEFINITIONS[RuleID.XDOC_001.value]
                    expl = ExplanationService.generate_explanation(
                        rule_id=RuleID.XDOC_001.value,
                        field_name="quantity",
                        expected_val=f"{val_a} ({doc_a.get('document_type')})",
                        actual_val=f"{val_b} ({doc_b.get('document_type')})",
                        difference=str(diff),
                        extra_context=f"{doc_a.get('filename')} states {val_a} whereas {doc_b.get('filename')} states {val_b}.",
                    )
                    disc = {
                        "document_id": doc_b.get("document_id"),
                        "field_name": "quantity",
                        "discrepancy_type": "CROSS_DOC_QUANTITY_MISMATCH",
                        "severity": rule["default_severity"],
                        "expected_value": f"{val_a} [{doc_a.get('filename')}]",
                        "actual_value": f"{val_b} [{doc_b.get('filename')}]",
                        "difference": str(diff),
                        "rule_id": RuleID.XDOC_001.value,
                        "rule_version": rule["version"],
                        "source_page": doc_b.get("fields", {}).get("quantity", {}).get("page_number"),
                        "source_text": doc_b.get("fields", {}).get("quantity", {}).get("source_text"),
                        "explanation": expl,
                    }
                    all_discrepancies.append(disc)
                    cross_results.append(disc)

        # XDOC-002: Package count across related documents
        pkg_docs = [d for d in docs if d.get("package_count") is not None]
        for i in range(len(pkg_docs)):
            for j in range(i + 1, len(pkg_docs)):
                doc_a, doc_b = pkg_docs[i], pkg_docs[j]
                if doc_a["package_count"] != doc_b["package_count"]:
                    diff = abs(doc_a["package_count"] - doc_b["package_count"])
                    rule = RULE_DEFINITIONS[RuleID.XDOC_002.value]
                    expl = ExplanationService.generate_explanation(
                        rule_id=RuleID.XDOC_002.value,
                        field_name="package_count",
                        expected_val=f"{doc_a['package_count']} ({doc_a.get('filename')})",
                        actual_val=f"{doc_b['package_count']} ({doc_b.get('filename')})",
                        difference=str(diff),
                        extra_context=f"{doc_a.get('filename')} lists {doc_a['package_count']} pkgs, but {doc_b.get('filename')} lists {doc_b['package_count']} pkgs.",
                    )
                    disc = {
                        "document_id": doc_b.get("document_id"),
                        "field_name": "package_count",
                        "discrepancy_type": "CROSS_DOC_PACKAGE_MISMATCH",
                        "severity": rule["default_severity"],
                        "expected_value": f"{doc_a['package_count']} [{doc_a.get('filename')}]",
                        "actual_value": f"{doc_b['package_count']} [{doc_b.get('filename')}]",
                        "difference": str(diff),
                        "rule_id": RuleID.XDOC_002.value,
                        "rule_version": rule["version"],
                        "source_page": doc_b.get("fields", {}).get("package_count", {}).get("page_number"),
                        "source_text": doc_b.get("fields", {}).get("package_count", {}).get("source_text"),
                        "explanation": expl,
                    }
                    all_discrepancies.append(disc)
                    cross_results.append(disc)

        # XDOC-003: Destination across related documents
        dest_docs = [d for d in docs if d.get("destination")]
        for i in range(len(dest_docs)):
            for j in range(i + 1, len(dest_docs)):
                doc_a, doc_b = dest_docs[i], dest_docs[j]
                norm_a = normalize_text_semantic(doc_a["destination"])
                norm_b = normalize_text_semantic(doc_b["destination"])
                if norm_a and norm_b and norm_a != norm_b:
                    rule = RULE_DEFINITIONS[RuleID.XDOC_003.value]
                    expl = ExplanationService.generate_explanation(
                        rule_id=RuleID.XDOC_003.value,
                        field_name="destination",
                        expected_val=doc_a["destination"],
                        actual_val=doc_b["destination"],
                        difference="Destination mismatch",
                        extra_context=f"Destination '{doc_a['destination']}' in {doc_a.get('filename')} differs from '{doc_b['destination']}' in {doc_b.get('filename')}.",
                    )
                    disc = {
                        "document_id": doc_b.get("document_id"),
                        "field_name": "destination",
                        "discrepancy_type": "CROSS_DOC_DESTINATION_MISMATCH",
                        "severity": rule["default_severity"],
                        "expected_value": f"{doc_a['destination']} [{doc_a.get('filename')}]",
                        "actual_value": f"{doc_b['destination']} [{doc_b.get('filename')}]",
                        "difference": "Differs across documents",
                        "rule_id": RuleID.XDOC_003.value,
                        "rule_version": rule["version"],
                        "source_page": doc_b.get("fields", {}).get("destination", {}).get("page_number"),
                        "source_text": doc_b.get("fields", {}).get("destination", {}).get("source_text"),
                        "explanation": expl,
                    }
                    all_discrepancies.append(disc)
                    cross_results.append(disc)

        action_desc = f"Cross-document reconciliation: {len(cross_results)} issue(s) detected across {len(docs)} documents."
        logs.append({
            "agent_name": cls.AGENT_NAME,
            "action": action_desc,
            "status": "SUCCESS" if not cross_results else "CROSS_DISCREPANCIES_FOUND",
            "details": {"cross_issues_count": len(cross_results)},
            "timestamp": start_time,
        })

        state.discrepancies = all_discrepancies
        state.cross_document_results = cross_results
        state.agent_execution_log = logs
        if cross_results:
            state.requires_human_review = True

        return state

