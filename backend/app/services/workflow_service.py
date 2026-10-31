"""
Workflow Service: coordinates asynchronous background execution of multi-agent verification graphs.
Provides job tracking, retry-safety, and bounded concurrency.
"""

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.database.connection import SessionLocal
from app.database.models import AgentExecutionLog, Discrepancy, Document, Order, ProcessingJob
from app.orchestration.graph import verification_workflow_graph
from app.orchestration.state import WorkflowState
from app.schemas.discrepancy import DiscrepancyCreate
from app.services.audit_service import AuditService
from app.services.discrepancy_engine import DiscrepancyEngine

logger = logging.getLogger(__name__)

# Bounded concurrency background worker pool (local execution & Celery compatibility bridge)
_worker_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="docuverify_agent_worker")

# In-memory fast cache for active workflow states
_active_workflows: Dict[str, WorkflowState] = {}


class WorkflowService:
    """Manages asynchronous workflow lifecycle, agent orchestration, and state persistence."""

    @classmethod
    def start_verification_workflow(
        cls,
        document_ids: List[str],
        order_id: Optional[str] = None,
        run_async: bool = True,
    ) -> WorkflowState:
        """
        Initializes a verification workflow and dispatches it to background worker.
        Returns initial state immediately.
        """
        workflow_id = f"WF-{uuid.uuid4().hex[:10].upper()}"
        initial_state = WorkflowState(
            workflow_id=workflow_id,
            order_id=order_id,
            document_ids=document_ids,
            workflow_status="PENDING",
            requires_human_review=False,
        )
        _active_workflows[workflow_id] = initial_state

        # Persist ProcessingJob record in database
        db: Session = SessionLocal()
        try:
            job = ProcessingJob(
                id=workflow_id,
                job_type="MULTI_AGENT_VERIFICATION",
                target_id=order_id or (document_ids[0] if document_ids else "BATCH"),
                status="PENDING",
                details={"document_ids": document_ids, "order_id": order_id},
            )
            db.add(job)
            db.commit()
        finally:
            db.close()

        if run_async:
            _worker_pool.submit(cls._run_graph_worker, initial_state)
            return initial_state
        else:
            # Synchronous execution for deterministic tests
            return cls._run_graph_worker(initial_state)

    @classmethod
    def _run_graph_worker(cls, state: WorkflowState) -> WorkflowState:
        """Worker thread entrypoint executing the compiled LangGraph workflow."""
        workflow_id = state.workflow_id
        logger.info("Executing multi-agent verification graph for workflow: %s", workflow_id)

        db: Session = SessionLocal()
        try:
            # Update job status to PROCESSING
            job = db.query(ProcessingJob).filter(ProcessingJob.id == workflow_id).first()
            if job:
                job.status = "PROCESSING"
                db.commit()

            # Execute compiled LangGraph StateGraph
            final_output = verification_workflow_graph.invoke(state)

            if isinstance(final_output, dict):
                final_state = WorkflowState.model_validate(final_output)
            else:
                final_state = final_output

            _active_workflows[workflow_id] = final_state

            # Persist generated discrepancies idempotently into database
            if final_state.discrepancies:
                discrepancy_creates = [
                    DiscrepancyCreate(
                        document_id=d.get("document_id"),
                        order_id=final_state.order_id,
                        field_name=d.get("field_name"),
                        discrepancy_type=d.get("discrepancy_type"),
                        severity=d.get("severity"),
                        expected_value=d.get("expected_value"),
                        actual_value=d.get("actual_value"),
                        difference=d.get("difference"),
                        rule_id=d.get("rule_id"),
                        rule_version=d.get("rule_version", "1.0.0"),
                        source_page=d.get("source_page"),
                        source_text=d.get("source_text"),
                        explanation=d.get("explanation"),
                    )
                    for d in final_state.discrepancies
                    if d.get("document_id") and d.get("rule_id") and d.get("field_name")
                ]
                DiscrepancyEngine.persist_discrepancies(db, discrepancy_creates)

            # Update Document status to VERIFIED
            for d_id in final_state.document_ids:
                doc = db.query(Document).filter(Document.id == d_id).first()
                if doc:
                    doc.status = "VERIFIED"
                    if final_state.order_id:
                        doc.order_id = final_state.order_id

            # Update Job status to REVIEW_REQUIRED
            if job:
                job.status = final_state.workflow_status
                job.details = final_state.final_investigation_report
                job.completed_at = datetime.now(timezone.utc)
                db.commit()

            # Audit log
            AuditService.log_event(
                db=db,
                event_type="WORKFLOW_COMPLETED",
                entity_type="WORKFLOW",
                entity_id=workflow_id,
                actor_id="supervisor_agent",
                details={
                    "order_id": final_state.order_id,
                    "documents_count": len(final_state.document_ids),
                    "discrepancies_count": len(final_state.discrepancies),
                    "status": final_state.workflow_status,
                },
            )

            return final_state

        except Exception as e:
            logger.error("Workflow %s failed during graph execution: %s", workflow_id, str(e), exc_info=True)
            job = db.query(ProcessingJob).filter(ProcessingJob.id == workflow_id).first()
            if job:
                job.status = "FAILED"
                job.error = str(e)
                job.completed_at = datetime.now(timezone.utc)
                db.commit()

            state.workflow_status = "FAILED"
            _active_workflows[workflow_id] = state
            return state
        finally:
            db.close()

    @classmethod
    def get_workflow_state(cls, workflow_id: str, db: Session) -> Optional[Dict[str, Any]]:
        """Retrieves current workflow state and investigation report."""
        if workflow_id in _active_workflows:
            return _active_workflows[workflow_id].model_dump()

        job = db.query(ProcessingJob).filter(ProcessingJob.id == workflow_id).first()
        if job:
            return {
                "workflow_id": job.id,
                "workflow_status": job.status,
                "error": job.error,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "final_investigation_report": job.details,
            }
        return None

    @classmethod
    def get_agent_logs(cls, workflow_id: str, db: Session) -> List[Dict[str, Any]]:
        """Retrieves execution traces of each agent for this workflow."""
        if workflow_id in _active_workflows:
            return _active_workflows[workflow_id].agent_execution_log

        logs = (
            db.query(AgentExecutionLog)
            .filter(AgentExecutionLog.workflow_id == workflow_id)
            .order_by(AgentExecutionLog.created_at.asc())
            .all()
        )
        return [
            {
                "agent_name": l.agent_name,
                "action": l.action,
                "status": l.status,
                "details": l.output_summary,
                "timestamp": l.created_at.isoformat() if l.created_at else "",
            }
            for l in logs
        ]

