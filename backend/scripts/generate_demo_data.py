"""
Demo Data and PDF Sample Generator for DocuVerify AI.
Creates:
1. Approved Order ORD-10245 in the database (or JSON).
2. Sample PDF invoice with 24000.00 total (triggers FIN-001 High discrepancy against 25000.00).
3. Sample PDF invoice with clean 25000.00 total (all checks pass).
4. Sample Packing List and Bill of Lading for cross-document verification.
"""

from pathlib import Path
import pymupdf
from app.core.config import settings
from app.database import init_db
from app.database.connection import SessionLocal
from app.database.models import Order, OrderItem
from app.services.audit_service import AuditService

DEMO_DIR = Path(__file__).resolve().parent.parent / "demo_files"
DEMO_DIR.mkdir(parents=True, exist_ok=True)


def create_demo_pdf(filename: str, title: str, lines: list) -> Path:
    """Generates a real PDF file with digital text layout using PyMuPDF."""
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)  # A4 size

    # Header
    page.insert_text(pymupdf.Point(50, 50), title, fontsize=18, fontname="helv", color=(0.1, 0.2, 0.4))
    page.insert_text(pymupdf.Point(50, 75), "[DEMO SAMPLE DATASET - FOR TESTING PURPOSES ONLY]", fontsize=9, fontname="helv", color=(0.5, 0.5, 0.5))
    page.draw_line(pymupdf.Point(50, 85), pymupdf.Point(545, 85), color=(0.7, 0.7, 0.7), width=1)

    # Content lines
    y = 120
    for label, val in lines:
        if label == "---":
            page.draw_line(pymupdf.Point(50, y - 10), pymupdf.Point(545, y - 10), color=(0.85, 0.85, 0.85), width=0.5)
            y += 10
            continue
        page.insert_text(pymupdf.Point(50, y), f"{label}:", fontsize=11, fontname="helv", color=(0.2, 0.2, 0.2))
        page.insert_text(pymupdf.Point(220, y), str(val), fontsize=11, fontname="helv", color=(0.0, 0.0, 0.0))
        y += 24

    output_path = DEMO_DIR / filename
    doc.save(str(output_path))
    doc.close()
    return output_path


def seed_demo_data():
    """Seeds the demo order ORD-10245 and generates sample demo PDFs."""
    init_db()
    db = SessionLocal()

    try:
        # 1. Seed Authoritative Order ORD-10245
        order_id = "ORD-10245"
        existing = db.query(Order).filter(Order.id == order_id).first()
        if not existing:
            order = Order(
                id=order_id,
                order_number=order_id,
                customer_name="ABC Industries",
                currency="USD",
                quantity=1000,
                unit_price=25.00,
                subtotal=25000.00,
                tax=0.00,
                freight=0.00,
                grand_total=25000.00,
                destination="Chennai Port",
                package_count=40,
                notes="Authoritative baseline order for demo verification scenario",
                is_authoritative=True,
                version=1,
            )
            db.add(order)
            db.flush()

            item = OrderItem(
                order_id=order.id,
                sku="STEEL-001",
                description="Industrial Steel Rod",
                quantity=1000,
                unit="PCS",
                unit_price=25.00,
                line_total=25000.00,
            )
            db.add(item)
            db.commit()

            AuditService.log_event(
                db=db,
                event_type="DEMO_SEED_CREATED",
                entity_type="ORDER",
                entity_id=order.id,
                actor_id="system_demo_seeder",
                details={"scenario": "ABC Industries Baseline Order"},
            )
            print(f"[+] Seeded Demo Order {order_id} (ABC Industries, Total: USD 25,000.00)")
        else:
            print(f"[*] Demo Order {order_id} already exists in database.")

        # 2. Generate Demo Invoice with Mismatch (24000.00 vs 25000.00 -> triggers FIN-001)
        invoice_mismatch_lines = [
            ("Document Type", "Commercial Invoice"),
            ("Invoice Number", "INV-2026-901"),
            ("Order Reference", "ORD-10245"),
            ("Customer Name", "ABC Industries"),
            ("Currency", "USD"),
            ("---", ""),
            ("Line Item", "STEEL-001 Industrial Steel Rod 1000 PCS @ 25.00 24000.00"),
            ("Subtotal", "24000.00"),
            ("Tax (0%)", "0.00"),
            ("Grand Total", "USD 24,000.00"),
            ("---", ""),
            ("Destination", "Chennai Port"),
            ("Total Packages", "40"),
        ]
        p1 = create_demo_pdf("invoice_mismatch_ORD-10245.pdf", "COMMERCIAL INVOICE", invoice_mismatch_lines)
        print(f"[+] Created mismatch sample PDF: {p1.name}")

        # 3. Generate Clean Invoice (25000.00 matches ORD-10245 exactly)
        invoice_clean_lines = [
            ("Document Type", "Commercial Invoice"),
            ("Invoice Number", "INV-2026-902"),
            ("Order Reference", "ORD-10245"),
            ("Customer Name", "ABC Industries"),
            ("Currency", "USD"),
            ("---", ""),
            ("Line Item", "STEEL-001 Industrial Steel Rod 1000 PCS @ 25.00 25000.00"),
            ("Subtotal", "25000.00"),
            ("Tax (0%)", "0.00"),
            ("Grand Total", "USD 25,000.00"),
            ("---", ""),
            ("Destination", "Chennai Port"),
            ("Total Packages", "40"),
        ]
        p2 = create_demo_pdf("invoice_clean_ORD-10245.pdf", "COMMERCIAL INVOICE", invoice_clean_lines)
        print(f"[+] Created clean sample PDF: {p2.name}")

        # 4. Generate Demo Packing List
        packing_list_lines = [
            ("Document Type", "Packing List"),
            ("Packing List No", "PL-2026-440"),
            ("Order Reference", "ORD-10245"),
            ("Customer Name", "ABC Industries"),
            ("---", ""),
            ("Total Packages", "40"),
            ("Total Quantity", "1000 PCS"),
            ("Gross Weight", "25,000 KGS"),
            ("Destination", "Chennai Port"),
        ]
        p3 = create_demo_pdf("packing_list_ORD-10245.pdf", "PACKING LIST", packing_list_lines)
        print(f"[+] Created packing list sample PDF: {p3.name}")

        # 5. Generate Demo Bill of Lading
        bl_lines = [
            ("Document Type", "Ocean Bill of Lading"),
            ("B/L Number", "MSCU-8849201"),
            ("Order Reference", "ORD-10245"),
            ("Consignee", "ABC Industries"),
            ("---", ""),
            ("Port of Discharge", "Chennai Port"),
            ("Total Packages", "40"),
            ("Gross Weight", "25,000 KGS"),
        ]
        p4 = create_demo_pdf("bill_of_lading_ORD-10245.pdf", "OCEAN BILL OF LADING", bl_lines)
        print(f"[+] Created bill of lading sample PDF: {p4.name}")

    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()

