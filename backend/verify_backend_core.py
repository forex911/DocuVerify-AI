"""
Comprehensive In-Process Verification Suite for DocuVerify AI.
Verifies all core services, agents, rules, database queries, and reconciliation logic.
"""

import sys
import io
from decimal import Decimal
from datetime import datetime, timezone
import pymupdf

print("[1/6] Initializing database and importing modules...", flush=True)
from app.core.config import settings
from app.database import init_db
from app.database.connection import SessionLocal
from app.database.models import Document, Order, OrderItem, Discrepancy, ProcessingJob, ValidationRule
from app.services.pdf_extractor import PDFExtractor
from app.services.field_extractor import FieldExtractor
from app.tools.order_lookup import match_order_reference, lookup_order_by_id
from app.services.discrepancy_engine import DiscrepancyEngine
from app.services.audit_service import AuditService
from app.agents.validation_agent import ValidationAgent
from app.agents.reconciliation_agent import ReconciliationAgent
from app.schemas.document import CanonicalDocument, DocumentItemSchema
from app.orchestration.state import WorkflowState

init_db()
db = SessionLocal()
print(" -> Database initialized successfully.", flush=True)

# -------------------------------------------------------------
# Test 1: PDF Extraction Service
# -------------------------------------------------------------
print("\n[2/6] Testing PDF Extraction Service...", flush=True)
doc = pymupdf.open()
page = doc.new_page()
sample_text = (
    "COMMERCIAL INVOICE\n"
    "Invoice No: INV-TEST-999\n"
    "Order Reference: PO-TEST-999\n"
    "Customer: Global Logistics Inc\n"
    "Destination: Port of Rotterdam\n"
    "Currency: EUR\n"
    "Items:\n"
    "SKU-100 Premium Industrial Valves Qty: 50 Unit Price: 120.00 Total: 6000.00\n"
    "Subtotal: EUR 6,000.00\n"
    "Tax: EUR 600.00\n"
    "Freight: EUR 400.00\n"
    "Grand Total: EUR 7,000.00\n"
)
page.insert_text(pymupdf.Point(50, 100), sample_text)
pdf_bytes = doc.tobytes()
doc.close()

temp_pdf = settings.UPLOAD_DIR / "test_verify_inv.pdf"
temp_pdf.write_bytes(pdf_bytes)

raw_doc = PDFExtractor.extract_document(temp_pdf)
assert raw_doc["page_count"] > 0, "PDF extraction returned 0 pages"

extracted_doc = FieldExtractor.extract_fields("DOC-TEST-1", "test_verify_inv.pdf", raw_doc["pages"])
assert extracted_doc.document_type.upper() == "INVOICE", f"Unexpected doc type: {extracted_doc.document_type}"
assert extracted_doc.order_reference == "PO-TEST-999", f"Unexpected PO ref: {extracted_doc.order_reference}"
assert extracted_doc.currency == "EUR", f"Unexpected currency: {extracted_doc.currency}"
assert extracted_doc.grand_total == Decimal("7000.00"), f"Unexpected grand total: {extracted_doc.grand_total}"
print(f" -> Extraction passed: Doc Type={extracted_doc.document_type}, PO={extracted_doc.order_reference}, Grand Total={extracted_doc.currency} {extracted_doc.grand_total}")
temp_pdf.unlink(missing_ok=True)

# -------------------------------------------------------------
# Test 2: Order Creation & Order Matching
# -------------------------------------------------------------
print("\n[3/6] Testing Order Matching Service...", flush=True)
test_order_id = "ORD-TEST-VERIFY-001"
existing_order = db.query(Order).filter(Order.id == test_order_id).first()
if not existing_order:
    order = Order(
        id=test_order_id,
        order_number="PO-TEST-999",
        customer_name="Global Logistics Inc",
        currency="EUR",
        destination="Port of Rotterdam",
        grand_total=Decimal("7000.00"),
        quantity=Decimal("50.00"),
        unit_price=Decimal("120.00"),
    )
    db.add(order)
    db.commit()

matched = match_order_reference(db, extracted_ref="PO-TEST-999", customer_name="Global Logistics Inc")
assert matched.get("matched_order") is not None, "Order matching failed"
assert matched["matched_order"]["id"] == test_order_id
print(f" -> Order Matching passed: Matched Order={matched['matched_order']['id']}, Type={matched.get('match_type')}, Conf={matched.get('confidence')}")

# -------------------------------------------------------------
# Test 3: Deterministic Validation Rules
# -------------------------------------------------------------
print("\n[4/6] Testing Validation Agent & Rule Triggers...", flush=True)
# Test a document with a variance (e.g. currency mismatch and grand total mismatch)
faulty_doc = CanonicalDocument(
    filename="DOC-FAULTY-01.pdf",
    document_type="INVOICE",
    document_id="DOC-FAULTY-01",
    order_reference="PO-TEST-999",
    customer_name="Global Logistics Inc",
    currency="USD",  # Mismatch: Order is EUR
    grand_total=Decimal("8500.00"),  # Mismatch: Order is 7000.00
    destination="Port of Hamburg",  # Mismatch: Order is Port of Rotterdam
    items=[
        DocumentItemSchema(
            sku="SKU-100",
            description="Valves",
            quantity=Decimal("60.00"),  # Mismatch: Order is 50.00
            unit_price=Decimal("120.00"),
            line_total=Decimal("7200.00"),
        )
    ],
)

state = WorkflowState(
    workflow_id="WF-TEST-VERIFY-01",
    order_id=test_order_id,
    document_ids=["DOC-FAULTY-01"],
    extracted_documents={"DOC-FAULTY-01": faulty_doc.model_dump()},
)

updated_state = ValidationAgent.execute(state, db)
rule_ids = [d.get("rule_id") for d in updated_state.discrepancies]
print(f" -> Validation Agent detected {len(updated_state.discrepancies)} discrepancies: {rule_ids}")

assert "CUR-001" in rule_ids, "CUR-001 Currency mismatch rule was not triggered!"
assert "FIN-001" in rule_ids, "FIN-001 Grand total mismatch rule was not triggered!"
assert "QTY-001" in rule_ids, "QTY-001 Quantity mismatch rule was not triggered!"
assert "DEST-001" in rule_ids, "DEST-001 Destination mismatch rule was not triggered!"
print(" -> All deterministic validation rules correctly triggered with zero false negatives!")

# -------------------------------------------------------------
# Test 4: Cross-Document Reconciliation
# -------------------------------------------------------------
print("\n[5/6] Testing Cross-Document Reconciliation Agent...", flush=True)
# Add a packing list that has weight or quantity discrepancies vs invoice
pl_doc = CanonicalDocument(
    filename="DOC-PL-01.pdf",
    document_type="PACKING_LIST",
    document_id="DOC-PL-01",
    order_reference="PO-TEST-999",
    items=[
        DocumentItemSchema(
            sku="SKU-100",
            description="Valves",
            quantity=Decimal("45.00"),  # Discrepancy vs Invoice 60.00
            unit_price=Decimal("120.00"),
            line_total=Decimal("5400.00"),
        )
    ],
)
state.extracted_documents["DOC-PL-01"] = pl_doc.model_dump()
recon_state = ReconciliationAgent.execute(state, db)
recon_rule_ids = [d.get("rule_id") for d in recon_state.discrepancies]
print(f" -> Reconciliation Agent discrepancies: {recon_rule_ids}")
assert any("RECON" in r or "QTY" in r for r in recon_rule_ids), "Reconciliation rule failed!"
print(" -> Cross-document reconciliation passed.")

# -------------------------------------------------------------
# Test 5: Audit Trail Service
# -------------------------------------------------------------
print("\n[6/6] Testing Audit Trail Event Logging...", flush=True)
log_entry = AuditService.log_event(
    db=db,
    event_type="DISCREPANCY_REVIEWED",
    entity_type="DISCREPANCY",
    entity_id="DISC-TEST-001",
    actor_id="lead_reviewer_sarah",
    details={"review_decision": "ACCEPT_WITH_JUSTIFICATION", "comment": "Approved tolerance waiver."},
)
assert log_entry.id is not None
print(f" -> Audit Trail logging passed: ID={log_entry.id}, Timestamp={log_entry.created_at}")

db.close()
print("\n=======================================================")
print("ALL DOCUVERIFY AI CORE IN-PROCESS VERIFICATIONS PASSED!")
print("=======================================================")
