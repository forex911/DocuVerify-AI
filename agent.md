# Agentic AI Architecture — DocuVerify AI

Upgrade DocuVerify into a controlled multi-agent document intelligence system using LangGraph.

## Objective

Build a multi-agent workflow that processes invoices, packing lists, and bills of lading against approved customer orders. Agents must collaborate to extract, match, investigate, validate, and explain discrepancies.

Human reviewers retain complete authority over final decisions.

## Agents

1. Supervisor Agent
   - Orchestrates the workflow.
   - Maintains shared state.
   - Assigns specialist tasks.
   - Handles retries and failures.
   - Coordinates parallel tasks.

2. Document Intelligence Agent
   - Classifies document types.
   - Uses PDF/OCR tools.
   - Extracts structured fields.
   - Identifies missing and ambiguous values.
   - Retains page-level evidence.

3. Order Matching Agent
   - Retrieves approved orders.
   - Resolves order-reference formatting differences.
   - Detects ambiguous or duplicate matches.
   - Never arbitrarily selects an order.

4. Validation Agent
   - Invokes deterministic Python validation tools.
   - Checks quantities, financial values, currencies, references, and required fields.
   - Reports discrepancies with rule IDs.
   - Never delegates financial arithmetic to an LLM.

5. Cross-Document Reconciliation Agent
   - Compares invoice, packing list, and BOL.
   - Identifies inconsistencies.
   - Uses configurable document relationship rules.
   - Distinguishes legitimate document-specific values.

6. Explanation and Evidence Agent
   - Generates understandable discrepancy explanations.
   - References existing evidence records.
   - Suggests reviewer investigation actions.
   - Cannot change validation results or severity.

## Orchestration

Use LangGraph to build a stateful workflow.

Workflow:
Document Upload → Supervisor → Parallel Document Extraction and Order Matching → Synchronization → Deterministic Validation → Cross-Document Reconciliation → Evidence Generation → Human Review → Audit Logging.

Use conditional routing:
- Missing or ambiguous extraction → bounded OCR retry or manual review.
- Unmatched order → human investigation.
- Successful extraction and matching → validation.
- Detected discrepancy → evidence and explanation.
- No detected discrepancies → awaiting human confirmation.
- Completed investigation → human reviewer decision.

Use structured Pydantic state models.

## Agent Tool Restrictions

- Agents must use explicitly defined tools.
- No arbitrary code execution.
- No unrestricted filesystem access.
- No direct database writes by LLM agents.
- Use backend services for all database operations.
- Treat document contents as untrusted input.
- Never allow document instructions to override system policies.
- LLM outputs must be schema-validated.
- All financial calculations must use Python Decimal.
- Every finding must reference actual source evidence.

## Human-in-the-Loop

Integrate an explicit human-review stage.

Supported decisions:
- ACCEPT_WITH_JUSTIFICATION
- REQUEST_CORRECTION
- REJECT
- ESCALATE
- KEEP_PENDING

Use LangGraph interruption/checkpoint capabilities only if they can be implemented reliably within the available time. Otherwise, persist a REVIEW_REQUIRED state in the database and resume processing through a reviewer API.

No agent may approve or reject a document.

## High-Volume Processing

- Execute each document group as a background workflow.
- Use Celery/Redis when available.
- Maintain unique workflow IDs.
- Implement idempotency.
- Limit concurrent LLM requests.
- Cache reusable order lookups.
- Retry transient failures with bounded exponential backoff.
- Persist processing state and failures.
- Avoid unnecessary LLM calls.
- Keep deterministic validation independent of agent execution.

## Implementation Priority

1. Get the existing FastAPI backend working.
2. Implement document extraction and canonical schemas.
3. Implement deterministic validation tools.
4. Build LangGraph supervisor and shared workflow state.
5. Integrate document and order agents.
6. Add validation and cross-document agent nodes.
7. Add explanation agent.
8. Implement reviewer decisions and audit persistence.
9. Test the complete multi-agent workflow.
10. Add Gemini only when the deterministic fallback and full workflow work.

Do not create six independent autonomous LLMs unnecessarily. Specialist agents may be lightweight LLM-backed nodes or deterministic tool-driven nodes. The architecture must remain efficient and predictable.

Deliver actual working code, not pseudocode. Run end-to-end tests and document all unimplemented production features.