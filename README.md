# DocuVerify AI - Backend Architecture & Verification Engine

DocuVerify AI is a **human-in-the-loop** commercial document verification platform. It compares commercial invoices, packing lists, and bills of lading against approved customer purchase orders. It extracts structured data, detects discrepancies deterministically, assigns business severity, provides traceable source evidence with page numbers and exact quotes, and records human reviewer decisions in an immutable audit trail.

> **Strict Architectural Invariant:** AI processes **never** perform autonomous document approvals or rejections. Humans retain exclusive authority over commercial determinations.

---

## 1. System Architecture & Features

### Core Modules Implemented
- **Deterministic Rules Engine**: Explicit rule IDs (`ID-001`, `REQ-001`, `QTY-001`, `FIN-001`, `FIN-002`, `CUR-001`, `DEST-001`, `XDOC-001`, `XDOC-002`, `XDOC-003`) executing exact arithmetic and cross-document validation with Python `Decimal`.
- **PyMuPDF Document Ingestion**: Page-by-page digital text extraction with character-density thresholding.
- **Graceful OCR Fallback**: Integrated Tesseract OCR abstraction via `pytesseract` and Pillow. Reports extraction limitations honestly when external OCR binaries are absent, rather than silently failing.
- **Canonical Normalization**: Standardizes ISO currencies (USD, EUR, GBP, INR), commercial packaging units (PCS, KGS, CTN), and whitespace.
- **Evidence Provenance Tracking**: Discrepancies link directly to source page numbers, exact extracted strings, expected baseline values, mathematical variances, and rule versions.
- **Idempotent Verification**: Re-running verification updates evidence records without generating duplicate entries and preserves previously recorded human decisions.
- **Human-in-the-Loop Review**: Mandatory reviewer rationale comments for all submitted decisions (`ACCEPT_WITH_JUSTIFICATION`, `REQUEST_CORRECTION`, `REJECT`, `ESCALATE`, `KEEP_PENDING`).
- **Immutable Audit Trail**: Append-only audit history tracking all document ingestions, verifications, and reviewer actions.
- **Executive Dashboard API**: Operational summaries, severity breakdowns, pending reviews count, and recent audit activity.
- **Isolated Gemini Assistant (Optional)**: Can optionally rephrase precomputed explanations when `GEMINI_API_KEY` is present. Strictly isolated from modifying numbers, severity, rule IDs, or decisions. Fully operational without an API key.

---

## 2. Implemented Validation Rules

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

## 3. Technology Stack

- **Runtime**: Python 3.12+
- **Framework**: FastAPI + Uvicorn
- **Persistence**: SQLAlchemy 2.0 with SQLite (parameterized queries, index-optimized)
- **Data Validation**: Pydantic v2
- **PDF Extraction**: PyMuPDF (`pymupdf` 2.0)
- **OCR Engine**: Tesseract OCR via `pytesseract` + Pillow (optional external dependency)
- **AI / LLM**: `google-genai` SDK (optional assistant, disabled by default)

---

## 4. Project Structure

```text
DocuVerify AI/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI application entrypoint & middleware
│   │   ├── core/
│   │   │   ├── config.py               # Settings, tolerances, upload limits
│   │   │   └── constants.py            # Rule definitions, document types, severity levels
│   │   ├── database/
│   │   │   ├── connection.py           # SQLite connection & sessionmaker
│   │   │   └── models.py               # SQLAlchemy ORM models (orders, documents, discrepancies, audit)
│   │   ├── schemas/
│   │   │   ├── document.py             # Canonical document & provenance schemas
│   │   │   ├── order.py                # Order & item schemas
│   │   │   ├── discrepancy.py          # Discrepancy & verification schemas
│   │   │   └── review.py               # Review decision & audit schemas
│   │   ├── routes/
│   │   │   ├── health.py               # GET /api/health
│   │   │   ├── orders.py               # POST & GET /api/orders
│   │   │   ├── documents.py            # POST /api/documents/upload, GET /api/documents
│   │   │   ├── verification.py         # POST /api/verification/run
│   │   │   ├── reviews.py              # GET & POST /api/discrepancies, /decision
│   │   │   ├── audit.py                # GET /api/audit
│   │   │   └── dashboard.py            # GET /api/dashboard/summary
│   │   ├── services/
│   │   │   ├── pdf_extractor.py        # PyMuPDF extraction & page thresholding
│   │   │   ├── ocr_service.py          # Graceful Tesseract fallback
│   │   │   ├── field_extractor.py      # Structured parsing & evidence provenance
│   │   │   ├── normalization.py        # Currencies, units, decimal parsing
│   │   │   ├── comparison_engine.py    # Deterministic validation rules
│   │   │   ├── discrepancy_engine.py   # Idempotent persistence & querying
│   │   │   ├── explanation_service.py  # Fact-based natural language generator
│   │   │   └── audit_service.py        # Review decisions & audit logging
│   │   └── utils/
│   │       └── file_handler.py         # Magic bytes check, SHA-256, path-traversal prevention
│   ├── demo_files/                     # Seeded sample commercial PDFs
│   ├── scripts/
│   │   ├── generate_demo_data.py       # Seeds ORD-10245 and generates sample PDFs
│   │   └── run_demo_verification.py    # Interactive end-to-end verification script
│   ├── tests/
│   │   ├── conftest.py                 # Isolated SQLite fixtures & client setup
│   │   ├── test_health.py              # Health check tests
│   │   ├── test_upload.py              # Upload validation & security tests
│   │   ├── test_pdf_extraction.py      # PyMuPDF page extraction & limits
│   │   ├── test_validation_rules.py    # FIN-001, ID-001, QTY-001, CUR-001, clean sample
│   │   ├── test_cross_document.py      # XDOC-001, XDOC-002, XDOC-003 tests
│   │   ├── test_discrepancies.py       # Idempotency & filter tests
│   │   └── test_reviews_audit.py       # Mandatory comment, persistence, audit trail
│   ├── uploads/                        # Server-side safe PDF storage
│   ├── requirements.txt
│   └── .env.example
├── README.md
└── requirements.txt
```

---

## 5. Installation & Setup (Windows PowerShell)

### Prerequisites
- Python 3.12 installed and accessible via PATH.

### Step 1: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 2: Environment Configuration
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
*(Optional)* If you wish to enable the Gemini explanation rewriter, add your API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```
*Note: The platform is completely functional without any API key.*

### Step 3: Run the Server
From the project root:
```powershell
$env:PYTHONPATH="backend"
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive Swagger UI documentation is available at:
👉 **`http://127.0.0.1:8000/docs`**

---

## 6. Demo Scenario & Verification Workflow

A pre-configured dataset is included to demonstrate the full end-to-end verification and human review cycle.

### Seed Baseline Data and Sample PDFs
```powershell
$env:PYTHONPATH="backend"
python backend/scripts/generate_demo_data.py
```
This generates:
1. **Approved Customer Order (`ORD-10245`)**:
   - Customer: `ABC Industries`
   - Currency: `USD`
   - Item: `Industrial Steel Rod` (1,000 PCS @ $25.00)
   - Grand Total: `$25,000.00`
   - Destination: `Chennai Port`, Packages: `40`
2. **`invoice_mismatch_ORD-10245.pdf`**:
   - Invoiced Grand Total: `$24,000.00` (Mismatch vs. `$25,000.00`)
3. **`invoice_clean_ORD-10245.pdf`**:
   - Invoiced Grand Total: `$25,000.00` (Clean match)
4. **`packing_list_ORD-10245.pdf`** & **`bill_of_lading_ORD-10245.pdf`** for cross-document validation.

### Run Automated End-to-End Demo
```powershell
$env:PYTHONPATH="backend"
python backend/scripts/run_demo_verification.py
```

### Expected Output Breakdown
1. **Ingestion**: Ingests `invoice_mismatch_ORD-10245.pdf` and hashes file via SHA-256.
2. **Deterministic Detection**:
   - Flags **`FIN-001` (Grand Total Mismatch)**: Expected `25000.00`, Actual `24000.00`, Difference `1000.00`, Severity `HIGH`.
   - Extracted Evidence: `Source Page: 1`, `Source Text: 'Grand Total: USD 24,000.00'`.
   - Flags **`FIN-002` (Line Item Arithmetic Mismatch)**: Expected `25000.00`, Actual `24000.00`.
3. **Human Review Decision**:
   - Auditor submits `ACCEPT_WITH_JUSTIFICATION` with mandatory comment:
     `"Commercial variance of $1,000.00 approved per volume incentive discount agreement #VIA-2026."`
4. **Audit Trail**: Append-only event `HUMAN_REVIEW_DECISION` recorded with previous and new status.
5. **Clean Scenario**: Verified clean invoice yields `0 discrepancies` (`"No discrepancies detected --- awaiting reviewer confirmation."`).

---

## 7. API Contract & Example Requests

### 1. Ingest Commercial PDF
`POST /api/documents/upload` (Multipart form-data)
```bash
curl -X POST "http://127.0.0.1:8000/api/documents/upload" \
  -F "file=@backend/demo_files/invoice_mismatch_ORD-10245.pdf" \
  -F "order_id=ORD-10245"
```

### 2. Execute Deterministic Verification
`POST /api/verification/run`
```bash
curl -X POST "http://127.0.0.1:8000/api/verification/run" \
  -H "Content-Type: application/json" \
  -d '{"order_id": "ORD-10245"}'
```

### 3. Retrieve Discrepancy Evidence
`GET /api/discrepancies?document_id=DOC-XXXXX`
```bash
curl -X GET "http://127.0.0.1:8000/api/discrepancies?order_id=ORD-10245"
```
**Response Sample**:
```json
[
  {
    "id": "DISC-673089E8",
    "document_id": "DOC-428B6FFB",
    "order_id": "ORD-10245",
    "field_name": "grand_total",
    "discrepancy_type": "FINANCIAL_MISMATCH",
    "severity": "HIGH",
    "expected_value": "25000.00",
    "actual_value": "24000.00",
    "difference": "1000.00",
    "rule_id": "FIN-001",
    "rule_version": "1.0.0",
    "source_page": 1,
    "source_text": "Grand Total: USD 24,000.00",
    "explanation": "The invoice grand total is USD 24,000.00, which is USD 1,000.00 lower than the approved order total of USD 25,000.00.",
    "review_status": "PENDING"
  }
]
```

### 4. Record Human Review Decision
`POST /api/discrepancies/{id}/decision`
```bash
curl -X POST "http://127.0.0.1:8000/api/discrepancies/DISC-673089E8/decision" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "ACCEPT_WITH_JUSTIFICATION",
    "comment": "Approved variance per incentive agreement.",
    "reviewer_id": "auditor_jane"
  }'
```

### 5. Fetch Immutable Audit Trail
`GET /api/audit?entity_id=DISC-673089E8`
```bash
curl -X GET "http://127.0.0.1:8000/api/audit?entity_id=DISC-673089E8"
```

### 6. Operational Dashboard
`GET /api/dashboard/summary`
```bash
curl -X GET "http://127.0.0.1:8000/api/dashboard/summary"
```

---

## 8. Test Suite & Validation Results

The entire backend suite is tested using `pytest` with isolated in-memory/temporary SQLite databases.

### Run Tests
```powershell
$env:PYTHONPATH="backend"
pytest backend/tests -v
```

### Actual Test Execution Output
```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\nov\DocuVerify AI
collected 19 items

backend/tests/test_cross_document.py::test_cross_document_quantity_mismatch PASSED [  5%]
backend/tests/test_cross_document.py::test_cross_document_package_count_mismatch PASSED [ 10%]
backend/tests/test_discrepancies.py::test_idempotent_verification_no_duplicates PASSED [ 15%]
backend/tests/test_discrepancies.py::test_discrepancy_filtering PASSED   [ 21%]
backend/tests/test_health.py::test_health_check PASSED                   [ 26%]
backend/tests/test_pdf_extraction.py::test_pdf_extraction_page_provenance PASSED [ 31%]
backend/tests/test_pdf_extraction.py::test_scanned_page_honest_limitations PASSED [ 36%]
backend/tests/test_reviews_audit.py::test_mandatory_comment_validation PASSED [ 42%]
backend/tests/test_reviews_audit.py::test_decision_persistence_and_audit PASSED [ 47%]
backend/tests/test_upload.py::test_valid_pdf_upload PASSED               [ 52%]
backend/tests/test_upload.py::test_reject_non_pdf_extension PASSED       [ 57%]
backend/tests/test_upload.py::test_reject_fake_pdf_header PASSED         [ 63%]
backend/tests/test_upload.py::test_reject_empty_file PASSED              [ 68%]
backend/tests/test_upload.py::test_path_traversal_prevention PASSED      [ 73%]
backend/tests/test_validation_rules.py::test_fin_001_grand_total_mismatch PASSED [ 78%]
backend/tests/test_validation_rules.py::test_id_001_order_reference_mismatch PASSED [ 84%]
backend/tests/test_validation_rules.py::test_qty_001_quantity_mismatch PASSED [ 89%]
backend/tests/test_validation_rules.py::test_cur_001_currency_mismatch PASSED [ 94%]
backend/tests/test_validation_rules.py::test_clean_sample_no_discrepancies PASSED [100%]

======================= 19 passed in 7.24s ========================
```

---

## 9. Security & Local MVP Limitations

To maintain engineering transparency, the following design boundaries and future requirements are documented:
1. **Single-Tenant Local MVP**: The system is designed for single-tenant local deployment. Multi-tenant database schema isolation (e.g., PostgreSQL row-level security or tenant IDs on all foreign keys) is a future production requirement.
2. **Authentication & Authorization**: The MVP accepts reviewer identities via request payloads (`reviewer_id`). In production, this must be replaced with JWT-based OAuth2/OIDC (e.g., Auth0 or enterprise SSO) and Role-Based Access Control (RBAC).
3. **File Storage**: Uploaded PDFs are stored in the local `uploads/` directory with collision-proof UUID filenames and path-traversal prevention. In production, this should integrate with private S3/GCS buckets using pre-signed URLs.
4. **OCR Dependency**: Tesseract OCR is handled gracefully: if the host does not have the binary installed, scanned pages are honestly flagged with `requires_manual_extraction = True` rather than hallucinating text.
5. **No AI Final Decisions**: AI assistance is strictly constrained. An LLM may assist in narrative clarity, but can never alter validation outcomes, difference amounts, severity ratings, or document approvals.

