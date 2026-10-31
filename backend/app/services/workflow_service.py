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
                details = dict(final_state.final_investigation_report or {})
                details["document_ids"] = list(final_state.document_ids)
                details["order_id"] = final_state.order_id
                job.details = details
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
            details = job.details or {}
            order_id = details.get("order_id") or (
                job.target_id if job.target_id and not job.target_id.startswith("DOC-") else None
            )

            # Resolve document_ids
            doc_ids = details.get("document_ids") or []
            if not doc_ids and order_id:
                docs = db.query(Document.id).filter(Document.order_id == order_id).all()
                doc_ids = [d[0] for d in docs]
                if not doc_ids:
                    disc_doc_ids = db.query(Discrepancy.document_id).filter(Discrepancy.order_id == order_id).distinct().all()
                    doc_ids = [d[0] for d in disc_doc_ids if d[0]]
            elif not doc_ids and job.target_id and job.target_id.startswith("DOC-"):
                doc_ids = [job.target_id]

            if not order_id and doc_ids:
                first_doc = db.query(Document).filter(Document.id == doc_ids[0]).first()
                if first_doc and first_doc.order_id:
                    order_id = first_doc.order_id

            # Resolve discrepancies from database
            discs = []
            if doc_ids:
                for did in doc_ids:
                    discs.extend(DiscrepancyEngine.list_discrepancies(db, document_id=did))
            elif order_id:
                discs = DiscrepancyEngine.list_discrepancies(db, order_id=order_id)

            unique_discs: Dict[str, Any] = {}
            for d in discs:
                d_dict = d.model_dump() if hasattr(d, "model_dump") else d
                unique_discs[d_dict["id"]] = d_dict

            return {
                "workflow_id": job.id,
                "workflow_status": job.status,
                "order_id": order_id,
                "document_ids": doc_ids,
                "requires_human_review": job.status == "REVIEW_REQUIRED" or len(unique_discs) > 0,
                "discrepancies": list(unique_discs.values()),
                "error": job.error,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "final_investigation_report": details,
            }
        return None

    @classmethod
    def get_agent_logs(cls, workflow_id: str, db: Session) -> List[Dict[str, Any]]:
        """Retrieves execution traces of each agent for this workflow with full step details."""
        db_logs = (
            db.query(AgentExecutionLog)
            .filter(AgentExecutionLog.workflow_id == workflow_id)
            .order_by(AgentExecutionLog.created_at.asc())
            .all()
        )
        if db_logs:
            return [
                {
                    "id": l.id,
                    "workflow_id": l.workflow_id,
                    "agent_name": l.agent_name,
                    "step_name": l.action,
                    "action": l.action,
                    "status": l.status,
                    "input_summary": l.action,
                    "output_summary": str(l.output_summary) if l.output_summary else "",
                    "details": l.output_summary or {},
                    "duration_ms": l.duration_ms,
                    "created_at": l.created_at.isoformat() if l.created_at else datetime.now(timezone.utc).isoformat(),
                    "timestamp": l.created_at.isoformat() if l.created_at else datetime.now(timezone.utc).isoformat(),
                }
                for l in db_logs
            ]

        # Fallback to in-memory active workflow cache if DB not yet flushed
        if workflow_id in _active_workflows:
            active_logs = _active_workflows[workflow_id].agent_execution_log or []
            return [
                {
                    "id": f"trace-{idx}",
                    "workflow_id": workflow_id,
                    "agent_name": l.get("agent_name", "UnknownAgent"),
                    "step_name": l.get("action", "Agent Action"),
                    "action": l.get("action", "Agent Action"),
                    "status": l.get("status", "SUCCESS"),
                    "input_summary": str(l.get("action", "")),
                    "output_summary": str(l.get("details", "")),
                    "details": l.get("details", {}),
                    "duration_ms": None,
                    "created_at": l.get("timestamp") or datetime.now(timezone.utc).isoformat(),
                    "timestamp": l.get("timestamp") or datetime.now(timezone.utc).isoformat(),
                }
                for idx, l in enumerate(active_logs)
            ]

        return []

