"""
Workflows API: Multi-Agent Orchestration Endpoints.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/workflows", tags=["Multi-Agent Workflows"])


class WorkflowInitiateRequest(BaseModel):
    document_ids: List[str] = Field(..., min_length=1, description="List of uploaded document IDs to verify")
    order_id: Optional[str] = Field(None, description="Optional approved customer order ID")
    run_async: bool = Field(True, description="Whether to execute asynchronously in the background")


class WorkflowStatusResponse(BaseModel):
    workflow_id: str
    workflow_status: str
    order_id: Optional[str] = None
    document_ids: List[str] = []
    requires_human_review: bool = False
    discrepancies: List[Dict[str, Any]] = []
    final_investigation_report: Optional[Dict[str, Any]] = None
    agent_logs_count: int = 0


@router.post("/verify", status_code=status.HTTP_202_ACCEPTED, summary="Initiate Multi-Agent Document Verification")
def initiate_verification_workflow(payload: WorkflowInitiateRequest, db: Session = Depends(get_db)):
    """
    Launches the LangGraph multi-agent verification pipeline.
    Returns immediately with workflow_id; processing proceeds in background workers.
    """
    initial_state = WorkflowService.start_verification_workflow(
        document_ids=payload.document_ids,
        order_id=payload.order_id,
        run_async=payload.run_async,
    )
    return {
        "workflow_id": initial_state.workflow_id,
        "workflow_status": initial_state.workflow_status,
        "order_id": initial_state.order_id,
        "document_ids": initial_state.document_ids,
        "message": "Multi-agent verification workflow initiated. Monitor status via /api/workflows/{workflow_id}.",
    }


@router.get("/{workflow_id}", response_model=WorkflowStatusResponse, summary="Get Workflow Status & Results")
def get_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """Retrieves full workflow progress, intermediate outputs, and final investigation report."""
    state_dict = WorkflowService.get_workflow_state(workflow_id, db)
    if not state_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found.",
        )

    logs = WorkflowService.get_agent_logs(workflow_id, db)

    return WorkflowStatusResponse(
        workflow_id=state_dict.get("workflow_id", workflow_id),
        workflow_status=state_dict.get("workflow_status", "UNKNOWN"),
        order_id=state_dict.get("order_id"),
        document_ids=state_dict.get("document_ids", []),
        requires_human_review=state_dict.get("requires_human_review", False),
        discrepancies=state_dict.get("discrepancies", []),
        final_investigation_report=state_dict.get("final_investigation_report"),
        agent_logs_count=len(logs),
    )


@router.get("/{workflow_id}/agents", summary="Get Multi-Agent Execution Trace")
def get_workflow_agents(workflow_id: str, db: Session = Depends(get_db)):
    """
    Retrieves the execution trace of each specialized agent involved in this verification workflow.
    """
    logs = WorkflowService.get_agent_logs(workflow_id, db)
    if not logs:
        # Check if workflow exists
        state_dict = WorkflowService.get_workflow_state(workflow_id, db)
        if not state_dict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow '{workflow_id}' not found.",
            )

    return {
        "workflow_id": workflow_id,
        "agent_execution_count": len(logs),
        "agent_traces": logs,
    }

