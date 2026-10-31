# DocuVerify AI - Enterprise Multi-Agent Document Intelligence & Verification Platform

DocuVerify AI is an evidence-driven, **human-in-the-loop** commercial document verification platform powered by a **LangGraph Multi-Agent Orchestration Architecture**. It ingests commercial invoices, packing lists, and bills of lading, matches them to approved customer purchase orders, extracts structured information with page-level provenance, deterministically detects discrepancies with Python `Decimal`, and maintains an immutable audit trail.

> **Non-Negotiable Core Principle:** AI agents **NEVER** independently approve, reject, or modify commercial documents. Human reviewers retain exclusive final decision authority.

---

## 1. Multi-Agent Architecture

The platform coordinates **one supervisor orchestrator** and **five specialized agents** using a stateful **LangGraph `StateGraph`**:

```
                         Document Upload
                                |
                                v
                      [Supervisor Agent]
                                |
             +------------------+------------------+
             |                                     |
             v                                     v
[Document Intelligence Agent]            [Order Matching Agent]
             |                                     |
             +------------------+------------------+
                                |
                                v
                     [State Synchronization]
                                |
                                v
                        [Validation Agent]
                                |
                                v
              [Cross-Document Reconciliation Agent]
                                |
                                v
                 [Evidence & Explanation Agent]
                                |
                                v
                      [Finalize / Supervisor]
                                |
                                v
                   Workflow Status: REVIEW_REQUIRED
                                |
                                v
                      [Human Reviewer Action]
                                |
                                v
                     [Immutable Audit Trail]
```

### Specialist Agent Responsibilities

1. **Supervisor / Orchestrator Agent (`agents/supervisor_agent.py`)**:
   - Maintains typed `WorkflowState`.
   - Coordinates specialist agent execution and handles conditional branch routing.
   - Enforces bounded retry limits (`max_retries = 2`) to prevent infinite loops.
   - Guarantees that workflows finalize in `REVIEW_REQUIRED`, never in automated approval.

2. **Document Intelligence Agent (`agents/document_agent.py`)**:
   - Classifies document types (Commercial Invoice, Packing List, Bill of Lading).
   - Extracts structured canonical fields with exact page number and source quote provenance.
   - Coordinates with `pdf_tools` and `ocr_tools` with honest reporting when OCR is unavailable.

3. **Order Matching Agent (`agents/order_matching_agent.py`)**:
   - Matches documents against approved customer purchase orders.
   - Enforces hierarchical matching priority:
     1. Exact Order ID
     2. Exact Customer Reference
     3. Normalized Reference Matching
     4. Contextual Candidate Search
   - Never guesses: flags ambiguous or unmatched orders for human investigation.

4. **Validation Agent (`agents/validation_agent.py`)**:
   - Executes deterministic Python verification tools using `Decimal` precision.
   - Computes exact monetary and quantity differences against configurable tolerances.
   - Implements rules: `ID-001`, `CUR-001`, `QTY-001`, `FIN-001`, `FIN-002`, `REQ-001`, `DEST-001`.

5. **Cross-Document Reconciliation Agent (`agents/reconciliation_agent.py`)**:
   - Reconciles multi-document shipments (Invoice vs. Packing List vs. Bill of Lading).
   - Validates quantity consistency (`XDOC-001`), package counts (`XDOC-002`), and destinations (`XDOC-003`).

6. **Explanation and Evidence Agent (`agents/explanation_agent.py`)**:
   - Correlates structured evidence for every detected discrepancy.
   - Formulates clear, audit-ready explanations and provides concrete reviewer investigation steps.
   - Optionally integrates with Gemini via `google-genai` strictly for wording refinement; never changes numbers, severity, rule IDs, or decisions.

---

## 2. Technology Stack

- **Runtime**: Python 3.12+
- **Agent Orchestration**: LangGraph 1.2+ (`StateGraph`) & `langchain-core`
- **API Framework**: FastAPI + Uvicorn
- **Persistence**: SQLAlchemy 2.0 ORM with SQLite (PostgreSQL migration-ready architecture)
- **Data Validation**: Pydantic v2
- **PDF Extraction**: PyMuPDF (`pymupdf` 2.0)
- **OCR Engine**: Tesseract OCR via `pytesseract` + Pillow (graceful fallback)
- **LLM / AI (Optional)**: `google-genai` SDK (strictly isolated behind service interface)
- **Asynchronous Execution**: ThreadPool worker abstraction with Celery + Redis migration path
- **Test Framework**: Pytest 9.1+ with isolated test databases

---

## 3. Implemented Business Rules

| Rule ID | Check Description | Default Severity | Target Document |
| :--- | :--- | :--- | :--- |
| **`ID-001`** | Order Reference Mismatch | **CRITICAL** | Invoice, Packing List, Bill of Lading |
| **`REQ-001`** | Required Field Missing | **HIGH** | All commercial documents |
| **`QTY-001`** | Quantity Mismatch against Order | **HIGH** | Invoices & Packing Lists |
| **`FIN-001`** | Grand Total Mismatch | **HIGH** | Commercial Invoices |
| **`FIN-002`** | Line Arithmetic / Subtotal Mismatch | **HIGH** | Commercial Invoices |
| **`CUR-001`** | Currency Mismatch | **CRITICAL** | Commercial Invoices |
| **`DEST-001`** | Destination / Port of Discharge Mismatch | **MEDIUM** | Bills of Lading, Invoices |
| **`XDOC-001`** | Cross-Document Quantity Variance | **HIGH** | Invoice vs. Packing List vs. B/L |
| **`XDOC-002`** | Cross-Document Package Count Variance | **MEDIUM** | Packing List vs. Bill of Lading |
| **`XDOC-003`** | Cross-Document Destination Variance | **MEDIUM** | Invoice vs. Bill of Lading |

---

## 4. Project Structure

```text
DocuVerify AI/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI application entrypoint & middleware
│   │   ├── agents/
│   │   │   ├── supervisor_agent.py     # Agent 1: Supervisor / Orchestrator
│   │   │   ├── document_agent.py       # Agent 2: Document Intelligence
│   │   │   ├── order_matching_agent.py # Agent 3: Order Matching
│   │   │   ├── validation_agent.py     # Agent 4: Validation Engine
│   │   │   ├── reconciliation_agent.py # Agent 5: Cross-Document Reconciliation
│   │   │   └── explanation_agent.py    # Agent 6: Evidence & Explanation
│   │   ├── orchestration/
│   │   │   ├── state.py                # Typed WorkflowState Pydantic model
│   │   │   └── graph.py                # LangGraph StateGraph & conditional routing
│   │   ├── tools/
│   │   │   ├── pdf_tools.py            # Page-by-page extraction & density tools
│   │   │   ├── ocr_tools.py            # Tesseract fallback tools
│   │   │   ├── order_lookup.py         # Hierarchical order matching tools
│   │   │   ├── validation_tools.py     # Deterministic Decimal validation tools
│   │   │   ├── document_search.py      # Metadata retrieval tools
│   │   │   └── evidence_tools.py       # Evidence lookup & snippet tools
│   │   ├── core/
│   │   │   ├── config.py               # Settings, tolerances, upload limits
│   │   │   └── constants.py            # Rule definitions, document types, severity levels
│   │   ├── database/
│   │   │   ├── connection.py           # SQLite connection & sessionmaker
│   │   │   └── models.py               # SQLAlchemy ORM models
│   │   ├── schemas/
│   │   │   ├── document.py             # Canonical document & provenance schemas
│   │   │   ├── order.py                # Order & item schemas
│   │   │   ├── discrepancy.py          # Discrepancy & verification schemas
│   │   │   └── review.py               # Review decision & audit schemas
│   │   ├── routes/
│   │   │   ├── health.py               # GET /api/health
│   │   │   ├── orders.py               # POST & GET /api/orders
│   │   │   ├── documents.py            # POST /api/documents/upload, GET /documents
│   │   │   ├── workflows.py            # POST /api/workflows/verify, GET /workflows/{id}
│   │   │   ├── verification.py         # POST /api/verification/run
│   │   │   ├── reviews.py              # GET & POST /api/discrepancies, /decision
│   │   │   ├── audit.py                # GET /api/audit
│   │   │   └── dashboard.py            # GET /api/dashboard/summary
│   │   └── services/
│   │       ├── workflow_service.py     # Asynchronous worker & state management
│   │       ├── pdf_extractor.py        # PyMuPDF extraction engine
│   │       ├── field_extractor.py      # Canonical field parser
│   │       ├── comparison_engine.py    # Deterministic rule engine
│   │       ├── discrepancy_engine.py   # Idempotent persistence
│   │       └── audit_service.py        # Human decisions & audit logging
│   ├── demo_files/                     # Seeded sample commercial PDFs
│   ├── scripts/
│   │   ├── generate_demo_data.py       # Seeds ORD-10245 and generates sample PDFs
│   │   ├── run_demo_verification.py    # End-to-end verification demo script
│   │   └── run_multi_agent_demo.py     # Live multi-agent LangGraph demo script
│   ├── tests/
│   │   ├── conftest.py                 # Isolated SQLite fixtures & client setup
│   │   ├── test_multi_agent_workflow.py# Multi-agent routing, retry limits, LangGraph
│   │   ├── test_health.py              # Health check tests
│   │   ├── test_upload.py              # Upload validation & security tests
│   │   ├── test_pdf_extraction.py      # PyMuPDF page extraction & limits
│   │   ├── test_validation_rules.py    # FIN-001, ID-001, QTY-001, clean sample
│   │   ├── test_cross_document.py      # XDOC-001, XDOC-002, XDOC-003 tests
│   │   ├── test_discrepancies.py       # Idempotency & filter tests
│   │   └── test_reviews_audit.py       # Mandatory comment, persistence, audit trail
│   ├── uploads/                        # Server-side safe PDF storage
│   ├── requirements.txt
│   └── .env.example
├── README.md
├── requirements.txt
└── .env.example
```

---

## 5. Installation & Setup (Windows PowerShell)

### Step 1: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 2: Environment Configuration
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
*(Optional)* Add `GEMINI_API_KEY` to `.env` if you want contextual narrative refinement. The application operates with full fidelity without an API key.

### Step 3: Run the Server
From the workspace root:
```powershell
$env:PYTHONPATH="backend"
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive Swagger UI: 👉 **`http://127.0.0.1:8000/docs`**

---

## 6. Multi-Agent Demonstration Scenario

### Seed Baseline Data and Sample PDFs
```powershell
$env:PYTHONPATH="backend"
python backend/scripts/generate_demo_data.py
```

### Run Live Multi-Agent Verification Trace
```powershell
$env:PYTHONPATH="backend"
python backend/scripts/run_multi_agent_demo.py
```

### Example Multi-Agent Execution Trace Output
```text
================================================================================
DOCUVERIFY AI: ENTERPRISE MULTI-AGENT VERIFICATION DEMONSTRATION
================================================================================

[1] System Online: HEALTHY (Version: 1.0.0, Database: connected)

[2] Authoritative Baseline Order: ORD-10245
    Customer: ABC Industries | Currency: USD
    Expected Total: $25,000.00 | Quantity: 1000.0000 PCS

[3] Ingested Document: invoice_mismatch_ORD-10245.pdf (ID: DOC-B91FEDB6)

[4] Dispatching to LangGraph Multi-Agent Orchestrator...
    Workflow ID: WF-2BE5DB7941

[5] Multi-Agent Execution Trace (7 Steps):
    Step 1: [DocumentIntelligenceAgent] -> Extracted 1 document(s) (Status: SUCCESS)
    Step 2: [OrderMatchingAgent] -> Verified explicit order ORD-10245 (Status: SUCCESS)
    Step 3: [SupervisorAgent] -> Synchronized extracted documents and matched order baseline. (Status: SUCCESS)
    Step 4: [ValidationAgent] -> Evaluated validation rules across 1 document(s): 2 issue(s) detected (Status: DISCREPANCIES_DETECTED)
    Step 5: [ReconciliationAgent] -> Skipped cross-document reconciliation (fewer than 2 documents in workflow). (Status: SKIPPED)
    Step 6: [ExplanationAgent] -> Formulated evidence and explanations for 2 issue(s). (Status: SUCCESS)
    Step 7: [SupervisorAgent] -> Workflow completed with 2 discrepancy(ies). Human review required. (Status: REVIEW_REQUIRED)

[6] Final Investigation Report:
    Workflow Status: REVIEW_REQUIRED
    Requires Human Review: True
    Total Discrepancies: 2
    Summary Conclusion: 2 commercial discrepancy(ies) identified. Human reviewer determination required.

[7] Traceable Evidence & Investigation Recommendations:
    * Rule: FIN-001 (Grand Total Mismatch) | Severity: HIGH
      Expected: 25000.00 | Actual: 24000.00 | Variance: 1000.00
      Source Page: 1 | Quote: 'Grand Total: USD 24,000.00'
      Explanation: The invoice grand total is USD 24,000.00, which is USD 1,000.00 lower than the approved order total of USD 25,000.00.
```

---

## 7. API Reference

### Multi-Agent Workflows
- **`POST /api/workflows/verify`**: Initiates asynchronous LangGraph verification workflow. Returns `202 Accepted` with `workflow_id` immediately.
- **`GET /api/workflows/{workflow_id}`**: Retrieves current workflow status, document counts, discrepancies, and final investigation report.
- **`GET /api/workflows/{workflow_id}/agents`**: Retrieves complete agent execution traces (which agent executed, timestamp, action, and outputs).

### Core Verification & Review
- **`GET /api/health`**: Diagnostic health check.
- **`POST /api/orders`**: Create authoritative approved purchase order.
- **`POST /api/documents/upload`**: Secure multipart PDF upload, validation, and PyMuPDF text extraction.
- **`GET /api/discrepancies`**: Query discrepancies with filters (severity, review status, order, document).
- **`POST /api/discrepancies/{id}/decision`**: Record human review decision with mandatory justification comment.
- **`GET /api/audit`**: Fetch immutable audit trail.
- **`GET /api/dashboard/summary`**: Operational dashboard counts and metrics.

---

## 8. Test Suite & Validation Results

Run the complete test suite (24 automated tests):
```powershell
$env:PYTHONPATH="backend"
pytest backend/tests -v
```

### Actual Test Execution Output
```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\nov\DocuVerify AI
plugins: anyio-4.15.1, langsmith-0.14.16
collected 24 items

backend/tests/test_cross_document.py::test_cross_document_quantity_mismatch PASSED [  4%]
backend/tests/test_cross_document.py::test_cross_document_package_count_mismatch PASSED [  8%]
backend/tests/test_discrepancies.py::test_idempotent_verification_no_duplicates PASSED [ 12%]
backend/tests/test_discrepancies.py::test_discrepancy_filtering PASSED   [ 16%]
backend/tests/test_health.py::test_health_check PASSED                   [ 20%]
backend/tests/test_multi_agent_workflow.py::test_multi_agent_workflow_full_execution PASSED [ 25%]
backend/tests/test_multi_agent_workflow.py::test_ambiguous_order_matching_routes_to_human PASSED [ 29%]
backend/tests/test_multi_agent_workflow.py::test_evidence_completeness PASSED [ 33%]
backend/tests/test_multi_agent_workflow.py::test_no_agent_can_approve_or_reject PASSED [ 37%]
backend/tests/test_multi_agent_workflow.py::test_workflow_api_endpoints PASSED [ 41%]
backend/tests/test_pdf_extraction.py::test_pdf_extraction_page_provenance PASSED [ 45%]
backend/tests/test_pdf_extraction.py::test_scanned_page_honest_limitations PASSED [ 50%]
backend/tests/test_reviews_audit.py::test_mandatory_comment_validation PASSED [ 54%]
backend/tests/test_reviews_audit.py::test_decision_persistence_and_audit PASSED [ 58%]
backend/tests/test_upload.py::test_valid_pdf_upload PASSED               [ 62%]
backend/tests/test_upload.py::test_reject_non_pdf_extension PASSED       [ 66%]
backend/tests/test_upload.py::test_reject_fake_pdf_header PASSED         [ 70%]
backend/tests/test_upload.py::test_reject_empty_file PASSED              [ 75%]
backend/tests/test_upload.py::test_path_traversal_prevention PASSED      [ 79%]
backend/tests/test_validation_rules.py::test_fin_001_grand_total_mismatch PASSED [ 83%]
backend/tests/test_validation_rules.py::test_id_001_order_reference_mismatch PASSED [ 87%]
backend/tests/test_validation_rules.py::test_qty_001_quantity_mismatch PASSED [ 91%]
backend/tests/test_validation_rules.py::test_cur_001_currency_mismatch PASSED [ 95%]
backend/tests/test_validation_rules.py::test_clean_sample_no_discrepancies PASSED [100%]

======================== 24 passed in 8.67s ========================
```

---

## 9. Production Migration & Security Plan

1. **Authentication & Multi-Tenancy**: The current release accepts reviewer identities via API payloads. In production, connect an OAuth2/OIDC provider (Auth0, Okta, Keycloak) and implement tenant schema isolation in PostgreSQL.
2. **Distributed Queue (Celery + Redis)**: The current implementation utilizes an in-process ThreadPool worker abstraction with database status synchronization. The service interface is designed for drop-in migration to Celery workers with a Redis message broker for high-throughput multi-node clusters.
3. **Cloud Storage**: Replace local `uploads/` directory with AWS S3 or Google Cloud Storage using pre-signed upload URLs and server-side encryption.
4. **LLM Safety Guardrails**: PDF document content is treated as untrusted data; prompt instructions strip embedded command injection attempts. LLMs cannot modify calculated values, rule IDs, severities, or document approval statuses.
