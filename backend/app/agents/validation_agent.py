"""
Agent 4: Validation Agent.
Coordinates deterministic Python validation tools with Decimal monetary calculations.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from app.orchestration.state import WorkflowState
from app.tools.validation_tools import (
    validate_currency,
    validate_customer,
    validate_destination,
    validate_line_arithmetic,
    validate_order_reference,
    validate_quantity,
    validate_required_fields,
    validate_total_amount,
    validate_unit_price,
)


class ValidationAgent:
    """Specialist agent responsible for executing deterministic business rules."""

    AGENT_NAME = "ValidationAgent"

    @classmethod
    def execute(cls, state: WorkflowState, db: Session) -> WorkflowState:
        start_time = datetime.now(timezone.utc).isoformat()
        logs = list(state.agent_execution_log)
        all_discrepancies: List[Dict[str, Any]] = list(state.discrepancies)
        validation_results: List[Dict[str, Any]] = []

        order_data = state.order_match_result.get("matched_order") if state.order_match_result else None
        if not order_data:
            logs.append({
                "agent_name": cls.AGENT_NAME,
                "action": "Skipped validation: No authoritative order matched.",
                "status": "SKIPPED",
                "details": {},
                "timestamp": start_time,
            })
            state.agent_execution_log = logs
            return state

        # Extract order baseline values
        order_ref = order_data.get("order_number") or order_data.get("id")
        order_cust = order_data.get("customer_name")
        order_curr = order_data.get("currency")
        order_qty = Decimal(str(order_data["quantity"])) if order_data.get("quantity") is not None else None
        order_total = Decimal(str(order_data["grand_total"])) if order_data.get("grand_total") is not None else None
        order_dest = order_data.get("destination")
        order_price = Decimal(str(order_data["unit_price"])) if order_data.get("unit_price") is not None else None

        for doc_id, doc_dict in state.extracted_documents.items():
            doc_type = doc_dict.get("document_type", "document")
            fields = doc_dict.get("fields", {})

            # 1. ID-001: Order reference mismatch
            if doc_dict.get("order_reference"):
                ref_prov = fields.get("order_reference", {})
                d_id = validate_order_reference(
                    expected_ref=order_ref,
                    actual_ref=doc_dict.get("order_reference"),
                    document_id=doc_id,
                    page_number=ref_prov.get("page_number"),
                    source_text=ref_prov.get("source_text"),
                    doc_type=doc_type,
                )
                if d_id:
                    all_discrepancies.append(d_id)
                    validation_results.append(d_id)

            # 2. CUR-001: Currency mismatch
            if doc_dict.get("currency") and order_curr:
                curr_prov = fields.get("currency", {})
                d_cur = validate_currency(
                    expected_currency=order_curr,
                    actual_currency=doc_dict.get("currency"),
                    document_id=doc_id,
                    page_number=curr_prov.get("page_number"),
                    source_text=curr_prov.get("source_text"),
                    doc_type=doc_type,
                )
                if d_cur:
                    all_discrepancies.append(d_cur)
                    validation_results.append(d_cur)

            # 3. FIN-001: Grand total mismatch
            if doc_dict.get("grand_total") is not None and order_total is not None:
                tot_prov = fields.get("grand_total", {})
                doc_total_dec = Decimal(str(doc_dict["grand_total"]))
                d_fin = validate_total_amount(
                    expected_total=order_total,
                    actual_total=doc_total_dec,
                    document_id=doc_id,
                    currency=order_curr or "USD",
                    page_number=tot_prov.get("page_number"),
                    source_text=tot_prov.get("source_text"),
                    doc_type=doc_type,
                )
                if d_fin:
                    all_discrepancies.append(d_fin)
                    validation_results.append(d_fin)

            # 4. QTY-001: Quantity mismatch
            qty_prov = fields.get("quantity", {})
            if qty_prov.get("numeric_value") is not None and order_qty is not None:
                doc_qty_dec = Decimal(str(qty_prov["numeric_value"]))
                d_qty = validate_quantity(
                    expected_qty=order_qty,
                    actual_qty=doc_qty_dec,
                    document_id=doc_id,
                    page_number=qty_prov.get("page_number"),
                    source_text=qty_prov.get("source_text"),
                    doc_type=doc_type,
                )
                if d_qty:
                    all_discrepancies.append(d_qty)
                    validation_results.append(d_qty)

            # 5. FIN-002: Line item arithmetic
            items = doc_dict.get("items", [])
            subtotal = Decimal(str(doc_dict["subtotal"])) if doc_dict.get("subtotal") is not None else None
            arith_discs = validate_line_arithmetic(items, subtotal=subtotal, document_id=doc_id, doc_type=doc_type)
            all_discrepancies.extend(arith_discs)
            validation_results.extend(arith_discs)

            # 6. REQ-001: Required fields missing
            req_discs = validate_required_fields(
                doc_type=doc_type,
                present_fields={k: v.get("value") for k, v in fields.items()},
                document_id=doc_id,
            )
            all_discrepancies.extend(req_discs)
            validation_results.extend(req_discs)

            # 7. DEST-001: Destination mismatch
            if doc_dict.get("destination") and order_dest:
                dest_prov = fields.get("destination", {})
                d_dest = validate_destination(
                    expected_dest=order_dest,
                    actual_dest=doc_dict.get("destination"),
                    document_id=doc_id,
                    page_number=dest_prov.get("page_number"),
                    source_text=dest_prov.get("source_text"),
                    doc_type=doc_type,
                )
                if d_dest:
                    all_discrepancies.append(d_dest)
                    validation_results.append(d_dest)

        action_desc = f"Evaluated validation rules across {len(state.extracted_documents)} document(s): {len(validation_results)} issue(s) detected"
        logs.append({
            "agent_name": cls.AGENT_NAME,
            "action": action_desc,
            "status": "SUCCESS" if not validation_results else "DISCREPANCIES_DETECTED",
            "details": {"discrepancies_found": len(validation_results)},
            "timestamp": start_time,
        })

        state.discrepancies = all_discrepancies
        state.validation_results = validation_results
        state.agent_execution_log = logs
        if validation_results:
            state.requires_human_review = True

        return state

