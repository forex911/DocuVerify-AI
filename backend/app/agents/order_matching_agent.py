"""
Agent 3: Order Matching Agent.
Resolves and correlates documents to approved customer orders using strict hierarchical matching.
Routes ambiguous or missing matches to human review.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.orchestration.state import WorkflowState
from app.tools.order_lookup import lookup_order_by_id, match_order_reference


class OrderMatchingAgent:
    """Specialist agent responsible for ground-truth order identification and reference resolution."""

    AGENT_NAME = "OrderMatchingAgent"

    @classmethod
    def execute(cls, state: WorkflowState, db: Session) -> WorkflowState:
        start_time = datetime.now(timezone.utc).isoformat()
        logs = list(state.agent_execution_log)

        # 1. If order_id is already explicitly specified in state, verify it exists
        if state.order_id:
            order_data = lookup_order_by_id(db, state.order_id)
            if order_data:
                match_result = {
                    "matched_order": order_data,
                    "match_type": "EXPLICIT_ORDER_ID",
                    "candidates": [order_data],
                    "confidence": 1.0,
                    "requires_human_investigation": False,
                    "explanation": f"Authoritative order {state.order_id} verified from request context.",
                }
                state.order_match_result = match_result
                state.matching_candidates = [order_data]
                logs.append({
                    "agent_name": cls.AGENT_NAME,
                    "action": f"Verified explicit order {state.order_id}",
                    "status": "SUCCESS",
                    "details": match_result,
                    "timestamp": start_time,
                })
                state.agent_execution_log = logs
                return state

        # 2. Inspect extracted documents for references
        extracted_ref: Optional[str] = None
        extracted_cust: Optional[str] = None

        for doc_id, doc_dict in state.extracted_documents.items():
            if doc_dict.get("order_reference"):
                extracted_ref = doc_dict["order_reference"]
            if doc_dict.get("customer_name"):
                extracted_cust = doc_dict["customer_name"]
            if extracted_ref:
                break

        # 3. Match reference using hierarchical matching tool
        match_result = match_order_reference(db, extracted_ref=extracted_ref, customer_name=extracted_cust)

        state.order_match_result = match_result
        state.matching_candidates = match_result.get("candidates", [])

        if match_result.get("matched_order"):
            state.order_id = match_result["matched_order"]["id"]
            action_desc = f"Matched order {state.order_id} via {match_result['match_type']}"
            status = "SUCCESS"
        else:
            state.requires_human_review = True
            action_desc = f"Order matching unresolved ({match_result['match_type']})"
            status = "ESCALATED"

        logs.append({
            "agent_name": cls.AGENT_NAME,
            "action": action_desc,
            "status": status,
            "details": match_result,
            "timestamp": start_time,
        })
        state.agent_execution_log = logs

        return state

