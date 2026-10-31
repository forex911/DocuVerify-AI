"""
LangGraph Multi-Agent Verification Workflow.
Orchestrates specialized agents in a stateful, conditional, retry-safe directed graph.
"""

from typing import Any, Dict
from langgraph.graph import StateGraph, START, END
from sqlalchemy.orm import Session
from app.agents.document_agent import DocumentIntelligenceAgent
from app.agents.explanation_agent import ExplanationAgent
from app.agents.order_matching_agent import OrderMatchingAgent
from app.agents.reconciliation_agent import ReconciliationAgent
from app.agents.supervisor_agent import SupervisorAgent
from app.agents.validation_agent import ValidationAgent
from app.database.connection import SessionLocal
from app.database.models import AgentExecutionLog
from app.orchestration.state import WorkflowState


def build_verification_graph():
    """Constructs and compiles the LangGraph StateGraph for multi-agent verification."""

    builder = StateGraph(WorkflowState)

    # ---------------- Node Definitions ----------------

    def node_document_intelligence(state: WorkflowState) -> Dict[str, Any]:
        db: Session = SessionLocal()
        try:
            updated_state = DocumentIntelligenceAgent.execute(state, db)
            _persist_agent_logs(db, updated_state.workflow_id, updated_state.agent_execution_log)
            return updated_state.model_dump()
        finally:
            db.close()

    def node_order_matching(state: WorkflowState) -> Dict[str, Any]:
        db: Session = SessionLocal()
        try:
            updated_state = OrderMatchingAgent.execute(state, db)
            _persist_agent_logs(db, updated_state.workflow_id, updated_state.agent_execution_log)
            return updated_state.model_dump()
        finally:
            db.close()

    def node_synchronize(state: WorkflowState) -> Dict[str, Any]:
        logs = list(state.agent_execution_log)
        sync_log = {
            "agent_name": "SupervisorAgent",
            "action": "Synchronized extracted documents and matched order baseline.",
            "status": "SUCCESS",
            "details": {
                "order_id": state.order_id,
                "document_count": len(state.extracted_documents),
            },
            "timestamp": "",
        }
        logs.append(sync_log)
        db: Session = SessionLocal()
        try:
            _persist_agent_logs(db, state.workflow_id, logs)
        finally:
            db.close()
        return {"agent_execution_log": logs}

    def node_validation(state: WorkflowState) -> Dict[str, Any]:
        db: Session = SessionLocal()
        try:
            updated_state = ValidationAgent.execute(state, db)
            _persist_agent_logs(db, updated_state.workflow_id, updated_state.agent_execution_log)
            return updated_state.model_dump()
        finally:
            db.close()

    def node_reconciliation(state: WorkflowState) -> Dict[str, Any]:
        db: Session = SessionLocal()
        try:
            updated_state = ReconciliationAgent.execute(state, db)
            _persist_agent_logs(db, updated_state.workflow_id, updated_state.agent_execution_log)
            return updated_state.model_dump()
        finally:
            db.close()

    def node_explanation_evidence(state: WorkflowState) -> Dict[str, Any]:
        db: Session = SessionLocal()
        try:
            updated_state = ExplanationAgent.execute(state, db)
            _persist_agent_logs(db, updated_state.workflow_id, updated_state.agent_execution_log)
            return updated_state.model_dump()
        finally:
            db.close()

    def node_finalize(state: WorkflowState) -> Dict[str, Any]:
        db: Session = SessionLocal()
        try:
            updated_state = SupervisorAgent.finalize_workflow(state, db)
            _persist_agent_logs(db, updated_state.workflow_id, updated_state.agent_execution_log)
            return updated_state.model_dump()
        finally:
            db.close()

    # Add Nodes
    builder.add_node("document_intelligence", node_document_intelligence)
    builder.add_node("order_matching", node_order_matching)
    builder.add_node("synchronize", node_synchronize)
    builder.add_node("validation", node_validation)
    builder.add_node("reconciliation", node_reconciliation)
    builder.add_node("explanation_evidence", node_explanation_evidence)
    builder.add_node("finalize", node_finalize)

    # ---------------- Conditional Routing ----------------

    def route_after_extraction(state: WorkflowState) -> str:
        decision = SupervisorAgent.evaluate_extraction_state(state)
        if decision == "proceed_to_matching":
            return "order_matching"
        elif decision == "retry_extraction":
            return "document_intelligence"
        return "explanation_evidence"

    def route_after_matching(state: WorkflowState) -> str:
        decision = SupervisorAgent.evaluate_order_match_state(state)
        if decision == "proceed_to_validation":
            return "synchronize"
        return "explanation_evidence"

    # Add Edges
    builder.add_edge(START, "document_intelligence")
    builder.add_conditional_edges("document_intelligence", route_after_extraction)
    builder.add_conditional_edges("order_matching", route_after_matching)
    builder.add_edge("synchronize", "validation")
    builder.add_edge("validation", "reconciliation")
    builder.add_edge("reconciliation", "explanation_evidence")
    builder.add_edge("explanation_evidence", "finalize")
    builder.add_edge("finalize", END)

    return builder.compile()


def _persist_agent_logs(db: Session, workflow_id: str, logs: list):
    """Persists newly generated agent execution logs into SQLite."""
    for log in logs:
        action_name = log.get("action", "unknown")
        # Check if already saved in DB for this workflow
        exists = (
            db.query(AgentExecutionLog)
            .filter(
                AgentExecutionLog.workflow_id == workflow_id,
                AgentExecutionLog.agent_name == log.get("agent_name"),
                AgentExecutionLog.action == action_name,
            )
            .first()
        )
        if not exists:
            db_log = AgentExecutionLog(
                workflow_id=workflow_id,
                agent_name=log.get("agent_name", "UnknownAgent"),
                action=action_name,
                input_summary={"step": action_name},
                output_summary=log.get("details", {}),
                status=log.get("status", "SUCCESS"),
            )
            db.add(db_log)
    db.commit()


# Compiled Singleton Graph
verification_workflow_graph = build_verification_graph()
