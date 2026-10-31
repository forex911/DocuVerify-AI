"""
Typed Shared Agent State for LangGraph Workflow.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentLogEntry(BaseModel):
    agent_name: str
    action: str
    status: str = "SUCCESS"
    details: Optional[Dict[str, Any]] = None
    timestamp: str


class WorkflowState(BaseModel):
    """
    Immutable shared state passed across specialized verification agents in the LangGraph workflow.
    """
    workflow_id: str
    order_id: Optional[str] = None
    document_ids: List[str] = Field(default_factory=list)
    document_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Specialist Agent Outputs
    extracted_documents: Dict[str, Any] = Field(default_factory=dict)
    extraction_errors: List[Dict[str, Any]] = Field(default_factory=list)
    
    order_match_result: Optional[Dict[str, Any]] = None
    matching_candidates: List[Dict[str, Any]] = Field(default_factory=list)
    
    validation_results: List[Dict[str, Any]] = Field(default_factory=list)
    cross_document_results: List[Dict[str, Any]] = Field(default_factory=list)
    discrepancies: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_references: Dict[str, Any] = Field(default_factory=dict)
    
    # Execution Tracking & Guardrails
    agent_execution_log: List[Dict[str, Any]] = Field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 2
    workflow_status: str = "PENDING"  # PENDING, PROCESSING, REVIEW_REQUIRED, COMPLETED, FAILED
    requires_human_review: bool = False
    
    final_investigation_report: Optional[Dict[str, Any]] = None

