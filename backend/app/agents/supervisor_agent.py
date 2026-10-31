"""
Agent 1: Supervisor / Orchestrator Agent.
Coordinates specialist agents, monitors workflow state, enforces bounded retries, and manages routing.
"""

from datetime import datetime, timezone
from typing import Literal
from sqlalchemy.orm import Session
from app.orchestration.state import WorkflowState


class SupervisorAgent:
    """Supervisory orchestrator managing multi-agent verification pipeline."""

    AGENT_NAME = "SupervisorAgent"

    @classmethod
    def evaluate_extraction_state(cls, state: WorkflowState) -> Literal["proceed_to_matching", "retry_extraction", "manual_review"]:
        """Evaluates whether extraction succeeded, requires retry, or demands human manual review."""
        if state.extraction_errors:
            if state.retry_count < state.max_retries:
                return "retry_extraction"
            return "manual_review"

        if not state.extracted_documents:
            return "manual_review"

        return "proceed_to_matching"

    @classmethod
    def evaluate_order_match_state(cls, state: WorkflowState) -> Literal["proceed_to_validation", "human_investigation"]:
        """Evaluates order matching results."""
        if not state.order_match_result:
            return "human_investigation"

        match_type = state.order_match_result.get("match_type")
        if match_type in ("AMBIGUOUS", "UNMATCHED"):
            return "human_investigation"

        if not state.order_id:
            return "human_investigation"

        return "proceed_to_validation"

    @classmethod
    def finalize_workflow(cls, state: WorkflowState, db: Session) -> WorkflowState:
        """Determines final workflow completion status and records supervisor log."""
        start_time = datetime.now(timezone.utc).isoformat()
        logs = list(state.agent_execution_log)

        # Workflows require human review if discrepancies were found or matching required escalation
        if state.discrepancies or state.requires_human_review:
            state.workflow_status = "REVIEW_REQUIRED"
            status_desc = f"Workflow completed with {len(state.discrepancies)} discrepancy(ies). Human review required."
        else:
            state.workflow_status = "REVIEW_REQUIRED"  # Even clean documents require reviewer confirmation!
            status_desc = "Workflow completed. No discrepancies detected --- awaiting reviewer confirmation."

        logs.append({
            "agent_name": cls.AGENT_NAME,
            "action": status_desc,
            "status": state.workflow_status,
            "details": {
                "workflow_status": state.workflow_status,
                "discrepancies_count": len(state.discrepancies),
                "requires_human_review": True,
            },
            "timestamp": start_time,
        })
        state.agent_execution_log = logs

        return state

