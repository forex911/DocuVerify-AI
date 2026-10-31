"""
Agent 6: Explanation and Evidence Agent.
Synthesizes verifiable evidence, generates audit-ready explanations, and outlines recommended reviewer actions.
Strict Rule: Never alters values, severity, or decisions.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from app.core.config import settings
from app.orchestration.state import WorkflowState
from app.services.explanation_service import ExplanationService


class ExplanationAgent:
    """Specialist agent responsible for evidence correlation, narrative formulation, and reviewer recommendations."""

    AGENT_NAME = "ExplanationAgent"

    @classmethod
    def execute(cls, state: WorkflowState, db: Session) -> WorkflowState:
        start_time = datetime.now(timezone.utc).isoformat()
        logs = list(state.agent_execution_log)
        refined_discrepancies: List[Dict[str, Any]] = []

        evidence_map: Dict[str, Any] = dict(state.evidence_references)

        for disc in state.discrepancies:
            rule_id = disc.get("rule_id", "GEN-001")
            field_name = disc.get("field_name", "unknown")
            doc_id = disc.get("document_id", "unknown")

            # 1. Deterministic evidence explanation
            base_explanation = disc.get("explanation") or ExplanationService.generate_explanation(
                rule_id=rule_id,
                field_name=field_name,
                expected_val=disc.get("expected_value"),
                actual_val=disc.get("actual_value"),
                difference=disc.get("difference"),
            )

            # 2. Recommended human investigation steps based on rule
            investigation_steps = cls._recommend_investigation_steps(rule_id, field_name, disc)

            # 3. Optional Gemini refinement of narrative clarity (strictly preserves facts)
            enhanced_explanation = base_explanation
            if settings.GEMINI_API_KEY:
                enhanced_explanation = ExplanationService.enhance_with_gemini(
                    deterministic_explanation=base_explanation,
                    context_dict={
                        "rule_id": rule_id,
                        "field": field_name,
                        "expected": disc.get("expected_value"),
                        "actual": disc.get("actual_value"),
                        "difference": disc.get("difference"),
                    },
                )

            updated_disc = dict(disc)
            updated_disc["explanation"] = enhanced_explanation
            updated_disc["investigation_steps"] = investigation_steps
            refined_discrepancies.append(updated_disc)

            # Evidence reference mapping
            evidence_key = f"{doc_id}_{rule_id}_{field_name}"
            evidence_map[evidence_key] = {
                "source_page": disc.get("source_page"),
                "source_text": disc.get("source_text"),
                "expected_value": disc.get("expected_value"),
                "actual_value": disc.get("actual_value"),
                "rule_id": rule_id,
            }

        # 4. Final investigation report summary
        investigation_report = {
            "workflow_id": state.workflow_id,
            "order_id": state.order_id,
            "total_discrepancies": len(refined_discrepancies),
            "critical_count": sum(1 for d in refined_discrepancies if d.get("severity") == "CRITICAL"),
            "high_count": sum(1 for d in refined_discrepancies if d.get("severity") == "HIGH"),
            "medium_count": sum(1 for d in refined_discrepancies if d.get("severity") == "MEDIUM"),
            "low_count": sum(1 for d in refined_discrepancies if d.get("severity") == "LOW"),
            "summary_conclusion": (
                f"{len(refined_discrepancies)} commercial discrepancy(ies) identified. Human reviewer determination required."
                if refined_discrepancies
                else "No discrepancies detected --- awaiting human reviewer confirmation."
            ),
        }

        logs.append({
            "agent_name": cls.AGENT_NAME,
            "action": f"Formulated evidence and explanations for {len(refined_discrepancies)} issue(s).",
            "status": "SUCCESS",
            "details": investigation_report,
            "timestamp": start_time,
        })

        state.discrepancies = refined_discrepancies
        state.evidence_references = evidence_map
        state.final_investigation_report = investigation_report
        state.agent_execution_log = logs

        return state

    @classmethod
    def _recommend_investigation_steps(cls, rule_id: str, field_name: str, disc: Dict[str, Any]) -> List[str]:
        if rule_id == "FIN-001":
            return [
                "Verify whether customer order had an approved pricing addendum, volume rebate, or discount.",
                "Inspect invoice line item subtotals, tax rates, and freight surcharges.",
                "Confirm if partial shipment or milestone billing was authorized.",
            ]
        elif rule_id == "QTY-001":
            return [
                "Cross-reference packing list count against physical warehouse dispatch log.",
                "Check for backordered or phased delivery schedule.",
            ]
        elif rule_id == "ID-001":
            return [
                "Confirm whether customer issued an amended Purchase Order number.",
                "Verify internal ERP sales order link.",
            ]
        elif rule_id == "CUR-001":
            return [
                "Check if multi-currency settlement contract is active.",
                "Verify foreign exchange billing rate agreement.",
            ]
        elif rule_id == "DEST-001" or rule_id == "XDOC-003":
            return [
                "Confirm consignee delivery instructions and customs port of discharge.",
                "Review bill of lading port change addendum.",
            ]
        return [
            f"Review extracted evidence for '{field_name}' on source page {disc.get('source_page', 'unknown')}.",
            "Consult customer order contract for acceptable commercial variance tolerance.",
        ]

