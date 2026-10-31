"""
DocuVerify AI - Commercial Verification Scenario Generator & Test Report Engine.
Creates multi-document commercial test scenarios with PyMuPDF, ingests orders and PDFs,
runs multi-agent verification, and outputs traceable scenario test reports.
"""

import os
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import pymupdf

# Ensure backend root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.database.connection import SessionLocal
from app.database import init_db
from app.database.models import Document, Order, OrderItem, ProcessingJob, Discrepancy
from app.services.workflow_service import WorkflowService
from app.services.field_extractor import FieldExtractor
from app.services.pdf_extractor import PDFExtractor
from app.utils.file_handler import calculate_sha256
from app.core.config import settings

REPORTS_DIR = BASE_DIR.parent / "test_reports"
SAMPLES_DIR = BASE_DIR.parent / "sample_documents"


def create_commercial_pdf(filepath: Path, title: str, lines: list[str]) -> Path:
    """Generates a structured commercial PDF with PyMuPDF."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842) # A4 format

    # Header Banner
    page.draw_rect(pymupdf.Rect(40, 40, 555, 75), color=(0.14, 0.38, 0.92), fill=(0.95, 0.97, 1.0))
    page.insert_text(pymupdf.Point(55, 62), title.upper(), fontsize=14, fontname="helv", color=(0.1, 0.2, 0.6))

    # Document body text
    y = 105
    for line in lines:
        if line.startswith("===") or line.startswith("---"):
            page.draw_line(pymupdf.Point(40, y - 5), pymupdf.Point(555, y - 5), color=(0.8, 0.85, 0.9), width=1)
            y += 8
        elif line.startswith("# "):
            page.insert_text(pymupdf.Point(45, y), line[2:], fontsize=12, fontname="helv", color=(0.1, 0.1, 0.2))
            y += 18
        elif ":" in line:
            parts = line.split(":", 1)
            page.insert_text(pymupdf.Point(45, y), parts[0] + ":", fontsize=9, fontname="helv", color=(0.3, 0.35, 0.45))
            page.insert_text(pymupdf.Point(180, y), parts[1].strip(), fontsize=9, fontname="courier", color=(0.05, 0.05, 0.1))
            y += 16
        else:
            page.insert_text(pymupdf.Point(45, y), line, fontsize=9, fontname="courier", color=(0.1, 0.1, 0.15))
            y += 15

    # Footer
    page.draw_line(pymupdf.Point(40, 790), pymupdf.Point(555, 790), color=(0.85, 0.85, 0.85), width=0.5)
    page.insert_text(pymupdf.Point(45, 805), "DocuVerify AI Authenticated Document Provenance", fontsize=8, fontname="helv", color=(0.5, 0.5, 0.5))
    page.insert_text(pymupdf.Point(480, 805), "Page 1 of 1", fontsize=8, fontname="helv", color=(0.5, 0.5, 0.5))

    doc.save(str(filepath))
    doc.close()
    return filepath


def ingest_file_record(db, filepath: Path, original_filename: str, doc_type: str, order_id: str) -> str:
    """Stores the document in uploads and creates database records."""
    file_bytes = filepath.read_bytes()
    file_hash = calculate_sha256(file_bytes)
    doc_id = f"DOC-{os.urandom(4).hex().upper()}"
    server_filename = f"{doc_id}_{original_filename}"
    target_path = Path(settings.UPLOAD_DIR) / server_filename
    target_path.write_bytes(file_bytes)

    # Extract text with PDFExtractor
    extract_res = PDFExtractor.extract_document(target_path)
    pages_data = extract_res["pages"]
    page_count = extract_res["page_count"]
    method = extract_res["extraction_method"]
    raw_text = extract_res["full_text"]

    doc = Document(
        id=doc_id,
        order_id=order_id,
        filename=server_filename,
        original_filename=original_filename,
        file_path=str(target_path),
        file_hash=file_hash,
        file_size=len(file_bytes),
        mime_type="application/pdf",
        document_type=doc_type,
        status="EXTRACTED",
        page_count=page_count,
    )
    db.add(doc)
    db.flush()

    # DocumentExtraction record
    from app.database.models import DocumentExtraction
    extraction = DocumentExtraction(
        document_id=doc.id,
        raw_text=raw_text,
        pages_json=pages_data,
        page_count=page_count,
        extraction_method=method,
        requires_manual_extraction=False,
    )
    db.add(extraction)
    db.commit()
    return doc.id


def main():
    settings.init_app()
    init_db()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()
    print("=================================================================")
    print("  DocuVerify AI - Generating Commercial Test Scenarios & Reports")
    print("=================================================================")

    scenarios = [
        # SCENARIO 1: Clean Compliance
        {
            "id": "scenario_1",
            "name": "Clean Compliance & Exact Verification (Pass)",
            "order_id": "ORD-CLEAN-2026",
            "order_data": {
                "customer_name": "Apex Global Logistics Inc",
                "currency": "USD",
                "quantity": Decimal("1500.00"),
                "unit_price": Decimal("45.00"),
                "subtotal": Decimal("67500.00"),
                "tax": Decimal("0.00"),
                "freight": Decimal("2500.00"),
                "grand_total": Decimal("70000.00"),
                "destination": "Rotterdam Port, Netherlands",
                "package_count": 60,
                "items": [
                    {"sku": "APEX-SOLAR-01", "description": "High-Efficiency Photovoltaic Inverter", "qty": Decimal("1500"), "unit": "PCS", "price": Decimal("45.00"), "total": Decimal("67500.00")}
                ]
            },
            "documents": [
                {
                    "type": "invoice",
                    "filename": "invoice_clean_ORD-CLEAN-2026.pdf",
                    "title": "Commercial Invoice",
                    "content": [
                        "Order Reference: ORD-CLEAN-2026",
                        "Invoice Number: INV-APEX-9001",
                        "Customer Name: Apex Global Logistics Inc",
                        "Destination Port: Rotterdam Port, Netherlands",
                        "Currency: USD",
                        "---",
                        "# Line Items:",
                        "APEX-SOLAR-01 High-Efficiency Photovoltaic Inverter 1500 PCS @ 45.00 67500.00",
                        "---",
                        "Subtotal: USD 67,500.00",
                        "Freight: USD 2,500.00",
                        "Tax / VAT: USD 0.00",
                        "Grand Total: USD 70,000.00",
                        "Package Count: 60 PKGS",
                    ]
                }
            ],
            "expected_discrepancies": 0,
            "expected_outcome": "PASS: 0 Discrepancies. Commercial invoice strictly satisfies authorized baseline purchase order."
        },

        # SCENARIO 2: Financial Surcharge & Arithmetic Variance
        {
            "id": "scenario_2",
            "name": "Financial Overbilling & Line Arithmetic Mismatch",
            "order_id": "ORD-PRICE-2026",
            "order_data": {
                "customer_name": "Bavaria Tech GmbH",
                "currency": "EUR",
                "quantity": Decimal("2000.00"),
                "unit_price": Decimal("18.50"),
                "subtotal": Decimal("37000.00"),
                "tax": Decimal("0.00"),
                "freight": Decimal("0.00"),
                "grand_total": Decimal("37000.00"),
                "destination": "Hamburg Port, Germany",
                "package_count": 50,
                "items": [
                    {"sku": "BAV-CHIP-400", "description": "Microcontroller Circuit Modules", "qty": Decimal("2000"), "unit": "PCS", "price": Decimal("18.50"), "total": Decimal("37000.00")}
                ]
            },
            "documents": [
                {
                    "type": "invoice",
                    "filename": "invoice_price_variance_ORD-PRICE-2026.pdf",
                    "title": "Commercial Invoice",
                    "content": [
                        "Order Reference: ORD-PRICE-2026",
                        "Invoice Number: INV-BAV-8820",
                        "Customer Name: Bavaria Tech GmbH",
                        "Destination Port: Hamburg Port, Germany",
                        "Currency: EUR",
                        "---",
                        "# Line Items:",
                        "BAV-CHIP-400 Microcontroller Circuit Modules 2000 PCS @ 18.50 39000.00",
                        "---",
                        "Subtotal: EUR 39,000.00",
                        "Freight Surcharge: EUR 2,500.00",
                        "Grand Total: EUR 41,500.00",
                        "Package Count: 50 PKGS",
                    ]
                }
            ],
            "expected_discrepancies": 2,
            "expected_outcome": "FLAGGED: FIN-001 (Grand Total Mismatch €41,500 vs €37,000) and FIN-002 (Line Item Arithmetic Mismatch 2000*18.50=37000 vs 39000)."
        },

        # SCENARIO 3: Cross-Document Short Shipment
        {
            "id": "scenario_3",
            "name": "Cross-Document Short Shipment & Package Shortage",
            "order_id": "ORD-SHIP-2026",
            "order_data": {
                "customer_name": "Pacific Rim Trading Corp",
                "currency": "USD",
                "quantity": Decimal("3000.00"),
                "unit_price": Decimal("30.00"),
                "subtotal": Decimal("90000.00"),
                "tax": Decimal("0.00"),
                "freight": Decimal("0.00"),
                "grand_total": Decimal("90000.00"),
                "destination": "Singapore Port",
                "package_count": 100,
                "items": [
                    {"sku": "PAC-STEEL-50", "description": "Marine Grade Stainless Fasteners", "qty": Decimal("3000"), "unit": "PCS", "price": Decimal("30.00"), "total": Decimal("90000.00")}
                ]
            },
            "documents": [
                {
                    "type": "invoice",
                    "filename": "invoice_ORD-SHIP-2026.pdf",
                    "title": "Commercial Invoice",
                    "content": [
                        "Order Reference: ORD-SHIP-2026",
                        "Invoice Number: INV-PAC-1002",
                        "Customer Name: Pacific Rim Trading Corp",
                        "Destination Port: Singapore Port",
                        "Currency: USD",
                        "---",
                        "# Line Items:",
                        "PAC-STEEL-50 Marine Grade Stainless Fasteners 3000 PCS @ 30.00 90000.00",
                        "---",
                        "Grand Total: USD 90,000.00",
                        "Package Count: 100 PKGS",
                    ]
                },
                {
                    "type": "packing_list",
                    "filename": "packing_list_shortage_ORD-SHIP-2026.pdf",
                    "title": "Packing List (Short Shipment)",
                    "content": [
                        "Order Reference: ORD-SHIP-2026",
                        "Packing List Number: PK-PAC-1002-S",
                        "Customer Name: Pacific Rim Trading Corp",
                        "Destination Port: Singapore Port",
                        "Currency: USD",
                        "---",
                        "# Packed Items:",
                        "PAC-STEEL-50 Marine Grade Stainless Fasteners 2700 PCS @ 30.00 81000.00",
                        "---",
                        "Total Quantity Packed: 2700 PCS",
                        "Total Package Count: 90 PKGS",
                        "Gross Weight: 4,500 KG",
                    ]
                }
            ],
            "expected_discrepancies": 2,
            "expected_outcome": "FLAGGED: XDOC-001 (Cross-Doc Quantity: Invoice 3000 vs Packing List 2700) and XDOC-002 (Package Count: Invoice 100 vs Packing List 90)."
        },

        # SCENARIO 4: Unauthorized Port Diversion
        {
            "id": "scenario_4",
            "name": "Destination Port Divergence & Routing Variance",
            "order_id": "ORD-DEST-2026",
            "order_data": {
                "customer_name": "Nordic Industrial Solutions",
                "currency": "USD",
                "quantity": Decimal("800.00"),
                "unit_price": Decimal("40.00"),
                "subtotal": Decimal("32000.00"),
                "tax": Decimal("0.00"),
                "freight": Decimal("0.00"),
                "grand_total": Decimal("32000.00"),
                "destination": "Oslo Port, Norway",
                "package_count": 30,
                "items": [
                    {"sku": "NOR-PUMP-20", "description": "High Pressure Hydraulic Pumps", "qty": Decimal("800"), "unit": "PCS", "price": Decimal("40.00"), "total": Decimal("32000.00")}
                ]
            },
            "documents": [
                {
                    "type": "invoice",
                    "filename": "invoice_diverted_ORD-DEST-2026.pdf",
                    "title": "Commercial Invoice",
                    "content": [
                        "Order Reference: ORD-DEST-2026",
                        "Invoice Number: INV-NOR-4411",
                        "Customer Name: Nordic Industrial Solutions",
                        "Destination Port: Gothenburg Port, Sweden",
                        "Currency: USD",
                        "---",
                        "# Line Items:",
                        "NOR-PUMP-20 High Pressure Hydraulic Pumps 800 PCS @ 40.00 32000.00",
                        "---",
                        "Grand Total: USD 32,000.00",
                        "Package Count: 30 PKGS",
                    ]
                },
                {
                    "type": "bill_of_lading",
                    "filename": "bill_of_lading_diverted_ORD-DEST-2026.pdf",
                    "title": "Ocean Bill of Lading",
                    "content": [
                        "Order Reference: ORD-DEST-2026",
                        "BOL Number: BOL-NOR-9900",
                        "Consignee: Nordic Industrial Solutions",
                        "Port of Discharge: Gothenburg Port, Sweden",
                        "Currency: USD",
                        "---",
                        "Package Count: 30 PKGS",
                        "Gross Weight: 3,200 KG",
                        "Destination: Gothenburg Port, Sweden",
                    ]
                }
            ],
            "expected_discrepancies": 1,
            "expected_outcome": "FLAGGED: DEST-001 (Destination Mismatch: Approved 'Oslo Port, Norway' vs Actual 'Gothenburg Port, Sweden')."
        },

        # SCENARIO 5: Currency Mismatch & Missing PO
        {
            "id": "scenario_5",
            "name": "Critical Currency Mismatch & Missing Reference",
            "order_id": "ORD-CURR-2026",
            "order_data": {
                "customer_name": "Kyoto Precision Metals",
                "currency": "USD",
                "quantity": Decimal("500.00"),
                "unit_price": Decimal("100.00"),
                "subtotal": Decimal("50000.00"),
                "tax": Decimal("0.00"),
                "freight": Decimal("0.00"),
                "grand_total": Decimal("50000.00"),
                "destination": "Yokohama Port, Japan",
                "package_count": 20,
                "items": [
                    {"sku": "KYO-TITAN-01", "description": "Titanium Precision Flanges", "qty": Decimal("500"), "unit": "PCS", "price": Decimal("100.00"), "total": Decimal("50000.00")}
                ]
            },
            "documents": [
                {
                    "type": "invoice",
                    "filename": "invoice_currency_mismatch_ORD-CURR-2026.pdf",
                    "title": "Commercial Invoice",
                    "content": [
                        "Invoice Number: INV-KYO-7710",
                        "Customer Name: Kyoto Precision Metals",
                        "Destination Port: Yokohama Port, Japan",
                        "Currency: JPY",
                        "---",
                        "# Line Items:",
                        "KYO-TITAN-01 Titanium Precision Flanges 500 PCS @ 10000.00 5000000.00",
                        "---",
                        "Grand Total: JPY 5,000,000",
                        "Package Count: 20 PKGS",
                    ]
                }
            ],
            "expected_discrepancies": 2,
            "expected_outcome": "FLAGGED: CUR-001 (Critical Currency Mismatch: Approved 'USD' vs Actual 'JPY') and REQ-001 (Missing Order Reference)."
        }
    ]

    report_summaries = []

    for scen in scenarios:
        order_id = scen["order_id"]
        print(f"\n---> Processing {scen['id'].upper()}: {scen['name']} ...")

        # 1. Create Order if not exists
        existing_order = db.query(Order).filter(Order.id == order_id).first()
        if not existing_order:
            order_data = scen["order_data"]
            order = Order(
                id=order_id,
                order_number=order_id,
                customer_name=order_data["customer_name"],
                currency=order_data["currency"],
                quantity=order_data["quantity"],
                unit_price=order_data["unit_price"],
                subtotal=order_data["subtotal"],
                tax=order_data["tax"],
                freight=order_data["freight"],
                grand_total=order_data["grand_total"],
                destination=order_data["destination"],
                package_count=order_data["package_count"],
                is_authoritative=True,
                version=1,
            )
            db.add(order)
            db.flush()
            for it in order_data["items"]:
                item_rec = OrderItem(
                    order_id=order.id,
                    sku=it["sku"],
                    description=it["description"],
                    quantity=it["qty"],
                    unit=it["unit"],
                    unit_price=it["price"],
                    line_total=it["total"],
                )
                db.add(item_rec)
            db.commit()
            print(f"  [+] Created approved baseline order: {order_id}")
        else:
            print(f"  [i] Baseline order {order_id} already exists.")

        # 2. Generate and Ingest PDFs
        doc_ids = []
        for doc_cfg in scen["documents"]:
            pdf_path = SAMPLES_DIR / doc_cfg["filename"]
            create_commercial_pdf(pdf_path, doc_cfg["title"], doc_cfg["content"])
            doc_id = ingest_file_record(
                db=db,
                filepath=pdf_path,
                original_filename=doc_cfg["filename"],
                doc_type=doc_cfg["type"],
                order_id=order_id,
            )
            doc_ids.append(doc_id)
            print(f"  [+] Generated and ingested {doc_cfg['filename']} -> ID: {doc_id}")

        # 3. Launch Multi-Agent Verification Workflow
        state = WorkflowService.start_verification_workflow(
            document_ids=doc_ids,
            order_id=order_id,
            run_async=False, # synchronous execution to get results immediately
        )
        workflow_id = state.workflow_id
        print(f"  [+] Multi-Agent verification executed -> Workflow ID: {workflow_id}")

        # 4. Fetch Discrepancies from Database for the exact documents created
        discs = db.query(Discrepancy).filter(Discrepancy.document_id.in_(doc_ids)).all()
        print(f"  [i] Detected discrepancies: {len(discs)} (Expected: {scen['expected_discrepancies']})")

        # 5. Generate Individual Text Report
        report_text = f"""================================================================================
  DocuVerify AI - COMMERCIAL VERIFICATION SCENARIO TEST REPORT
================================================================================
Report ID       : REP-{scen['id'].upper()}
Scenario Name   : {scen['name']}
Workflow ID     : {workflow_id}
Order Reference : {order_id}
Customer Name   : {scen['order_data']['customer_name']}
Execution Date  : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
Workflow Status : {state.workflow_status}
Human Review    : {'REQUIRED (Strict Policy)' if len(discs) > 0 else 'VERIFIED - READY FOR SIGN-OFF'}
--------------------------------------------------------------------------------

1. AUTHORITATIVE PURCHASE ORDER BASELINE:
   - Order ID       : {order_id}
   - Authorized Total: {scen['order_data']['currency']} {scen['order_data']['grand_total']:,.2f}
   - Quantity       : {scen['order_data']['quantity']} PCS
   - Unit Price     : ${scen['order_data']['unit_price']:.2f}
   - Destination    : {scen['order_data']['destination']}
   - Expected PKGS  : {scen['order_data']['package_count']}

2. INGESTED COMMERCIAL DOCUMENTS ({len(doc_ids)}):
"""
        for doc_cfg, doc_id in zip(scen["documents"], doc_ids):
            report_text += f"   - Document ID : {doc_id}\n     Filename    : {doc_cfg['filename']}\n     Type        : {doc_cfg['type'].upper()}\n"

        report_text += f"""
--------------------------------------------------------------------------------
3. DETERMINISTIC VERIFICATION FINDINGS ({len(discs)} Discrepancy Records):
"""
        if not discs:
            report_text += "   [✓] 0 DISCREPANCIES DETECTED.\n   All extracted commercial values match the approved baseline.\n"
        else:
            for idx, d in enumerate(discs, 1):
                report_text += f"""   [{idx}] Rule ID: {d.rule_id} ({d.severity}) - Field: '{d.field_name}'
       Condition   : {d.explanation}
       Expected    : {d.expected_value}
       Actual      : {d.actual_value}
       Difference  : {d.difference or 'N/A'}
       Source Page : Page {d.source_page or 1}
       Source Text : "{d.source_text or 'Missing'}"
       Review State: {d.review_status}

"""

        report_text += f"""--------------------------------------------------------------------------------
4. HOW TO TEST THIS SCENARIO IN THE UI:
   1. Open: http://localhost:5173/verification/{workflow_id}
   2. Pane 1 (Left)   : Verify that '{scen['order_data']['customer_name']}' is selected.
   3. Pane 2 (Center) : Review the digital PDF and switch to 'Extracted Text' mode.
   4. Pane 3 (Right)  : Review the Field Reconciliation table and Variances list.
   5. Action          : Click 'Decide' on any variance, enter mandatory justification,
                        and record your human reviewer determination.
--------------------------------------------------------------------------------
Outcome Evaluation:
{scen['expected_outcome']}
================================================================================
"""

        report_file = REPORTS_DIR / f"{scen['id']}_report.txt"
        report_file.write_text(report_text, encoding="utf-8")
        print(f"  [+] Wrote text report: {report_file.name}")

        report_summaries.append({
            "scenario": scen["name"],
            "workflow_id": workflow_id,
            "order_id": order_id,
            "doc_count": len(doc_ids),
            "discrepancies": len(discs),
            "status": state.workflow_status,
            "report_file": report_file.name,
        })

    # 6. Generate Consolidated Markdown Report
    summary_md = """# DocuVerify AI - Commercial Verification Scenario Test Reports

This directory contains standalone test reports and commercial scenario documents designed for end-to-end verification and human-in-the-loop audit validation.

| Scenario | Workflow ID | Order ID | Ingested Docs | Variances | Status | Detailed Report |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for s in report_summaries:
        summary_md += f"| **{s['scenario']}** | `{s['workflow_id']}` | `{s['order_id']}` | {s['doc_count']} | **{s['discrepancies']}** | `{s['status']}` | [`{s['report_file']}`]({s['report_file']}) |\n"

    summary_md += """
---

## Scenario Descriptions & UI Test Links

### 1. Clean Compliance & Exact Verification (Pass)
- **Goal**: Verifies an authorized transaction with zero variances.
- **Workflow**: Direct Link: `http://localhost:5173/verification/` (See table above for Workflow ID)
- **Expected**: 0 Discrepancies, all fields validated green.

### 2. Financial Overbilling & Line Arithmetic Mismatch
- **Goal**: Detects invoice overbilling (`FIN-001`) and line calculation discrepancies (`FIN-002`).
- **Expected**: Flagged with High/Medium severity. Expected €37,000.00 vs billed €41,500.00.

### 3. Cross-Document Short Shipment & Package Shortage
- **Goal**: Cross-checks multi-document sets across Commercial Invoice, Packing List, and Bill of Lading.
- **Expected**: `XDOC-001` (Quantity short shipped by 300 PCS) and `XDOC-002` (Package count mismatch: 100 vs 90 PKGS).

### 4. Destination Port Divergence & Routing Variance
- **Goal**: Detects unauthorized shipping diversion from Oslo Port to Gothenburg Port (`DEST-001`).
- **Expected**: Flagged for human reviewer routing review.

### 5. Critical Currency Mismatch & Missing Reference
- **Goal**: Detects billing in unapproved foreign currency (`CUR-001`) and missing reference (`REQ-001`).
- **Expected**: Critical flag: Billed in JPY instead of contract USD.

---
*Generated by DocuVerify AI Test Scenario Suite.*
"""
    (REPORTS_DIR / "SCENARIOS_SUMMARY.md").write_text(summary_md, encoding="utf-8")
    print(f"\n[OK] Generated consolidated summary: {REPORTS_DIR / 'SCENARIOS_SUMMARY.md'}")
    db.close()


if __name__ == "__main__":
    main()
