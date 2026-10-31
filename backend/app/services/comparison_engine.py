"""
Deterministic Comparison Engine for DocuVerify AI.
Executes business rules against approved orders and canonical document extractions.
Uses Decimal precision and explicit configurable tolerances.
"""

from decimal import Decimal
from typing import List, Optional
from app.core.config import settings
from app.core.constants import RuleID, Severity, RULE_DEFINITIONS
from app.schemas.discrepancy import DiscrepancyCreate
from app.schemas.document import CanonicalDocument
from app.schemas.order import OrderResponse
from app.services.explanation_service import ExplanationService
from app.services.normalization import normalize_currency, normalize_text_semantic


class ComparisonEngine:
    """Executes rule-based verification between orders and canonical documents."""

    @classmethod
    def compare_document_to_order(
        cls, document: CanonicalDocument, order: OrderResponse
    ) -> List[DiscrepancyCreate]:
        """
        Evaluates a single commercial document against the approved customer order.
        """
        discrepancies: List[DiscrepancyCreate] = []

        # 1. ID-001: Order Reference Mismatch
        id_disc = cls._check_order_reference(document, order)
        if id_disc:
            discrepancies.append(id_disc)

        # 2. REQ-001: Required Fields Missing
        req_discs = cls._check_required_fields(document)
        discrepancies.extend(req_discs)

        # 3. CUR-001: Currency Mismatch
        cur_disc = cls._check_currency(document, order)
        if cur_disc:
            discrepancies.append(cur_disc)

        # 4. FIN-001: Grand Total Mismatch
        fin_disc = cls._check_grand_total(document, order)
        if fin_disc:
            discrepancies.append(fin_disc)

        # 5. QTY-001: Quantity Mismatch
        qty_disc = cls._check_quantity(document, order)
        if qty_disc:
            discrepancies.append(qty_disc)

        # 6. FIN-002: Line Item Arithmetic Mismatch
        arith_discs = cls._check_line_arithmetic(document)
        discrepancies.extend(arith_discs)

        # 7. DEST-001: Destination Mismatch
        dest_disc = cls._check_destination(document, order)
        if dest_disc:
            discrepancies.append(dest_disc)

        return discrepancies

    @classmethod
    def compare_cross_documents(
        cls, documents: List[CanonicalDocument], order_id: Optional[str] = None
    ) -> List[DiscrepancyCreate]:
        """
        Executes cross-document consistency checks:
        XDOC-001 (Quantity), XDOC-002 (Package Count), XDOC-003 (Destination).
        """
        cross_discrepancies: List[DiscrepancyCreate] = []
        if len(documents) < 2:
            return cross_discrepancies

        # XDOC-001: Quantity differs across related documents
        qty_docs = [d for d in documents if d.fields.get("quantity") and d.fields["quantity"].numeric_value is not None]
        for i in range(len(qty_docs)):
            for j in range(i + 1, len(qty_docs)):
                doc_a, doc_b = qty_docs[i], qty_docs[j]
                val_a = doc_a.fields["quantity"].numeric_value
                val_b = doc_b.fields["quantity"].numeric_value
                diff = abs(val_a - val_b)
                if diff > settings.QUANTITY_TOLERANCE:
                    rule = RULE_DEFINITIONS[RuleID.XDOC_001.value]
                    expl = ExplanationService.generate_explanation(
                        rule_id=RuleID.XDOC_001.value,
                        field_name="quantity",
                        expected_val=f"{val_a} ({doc_a.document_type})",
                        actual_val=f"{val_b} ({doc_b.document_type})",
                        difference=str(diff),
                        extra_context=f"{doc_a.filename} states {val_a} whereas {doc_b.filename} states {val_b}.",
                    )
                    cross_discrepancies.append(
                        DiscrepancyCreate(
                            document_id=doc_b.document_id,
                            order_id=order_id,
                            field_name="quantity",
                            discrepancy_type="CROSS_DOC_QUANTITY_MISMATCH",
                            severity=rule["default_severity"],
                            expected_value=f"{val_a} [{doc_a.filename}]",
                            actual_value=f"{val_b} [{doc_b.filename}]",
                            difference=str(diff),
                            rule_id=RuleID.XDOC_001.value,
                            rule_version=rule["version"],
                            source_page=doc_b.fields["quantity"].page_number,
                            source_text=doc_b.fields["quantity"].source_text,
                            explanation=expl,
                        )
                    )

        # XDOC-002: Package count differs across related documents
        pkg_docs = [d for d in documents if d.package_count is not None]
        for i in range(len(pkg_docs)):
            for j in range(i + 1, len(pkg_docs)):
                doc_a, doc_b = pkg_docs[i], pkg_docs[j]
                if doc_a.package_count != doc_b.package_count:
                    diff = abs(doc_a.package_count - doc_b.package_count)
                    rule = RULE_DEFINITIONS[RuleID.XDOC_002.value]
                    expl = ExplanationService.generate_explanation(
                        rule_id=RuleID.XDOC_002.value,
                        field_name="package_count",
                        expected_val=f"{doc_a.package_count} ({doc_a.filename})",
                        actual_val=f"{doc_b.package_count} ({doc_b.filename})",
                        difference=str(diff),
                        extra_context=f"{doc_a.filename} lists {doc_a.package_count} packages, but {doc_b.filename} lists {doc_b.package_count} packages.",
                    )
                    cross_discrepancies.append(
                        DiscrepancyCreate(
                            document_id=doc_b.document_id,
                            order_id=order_id,
                            field_name="package_count",
                            discrepancy_type="CROSS_DOC_PACKAGE_MISMATCH",
                            severity=rule["default_severity"],
                            expected_value=f"{doc_a.package_count} [{doc_a.filename}]",
                            actual_value=f"{doc_b.package_count} [{doc_b.filename}]",
                            difference=str(diff),
                            rule_id=RuleID.XDOC_002.value,
                            rule_version=rule["version"],
                            source_page=doc_b.source_pages.get("package_count"),
                            source_text=doc_b.fields.get("package_count").source_text if "package_count" in doc_b.fields else None,
                            explanation=expl,
                        )
                    )

        # XDOC-003: Destination differs across related documents
        dest_docs = [d for d in documents if d.destination]
        for i in range(len(dest_docs)):
            for j in range(i + 1, len(dest_docs)):
                doc_a, doc_b = dest_docs[i], dest_docs[j]
                norm_a = normalize_text_semantic(doc_a.destination)
                norm_b = normalize_text_semantic(doc_b.destination)
                if norm_a and norm_b and norm_a != norm_b:
                    rule = RULE_DEFINITIONS[RuleID.XDOC_003.value]
                    expl = ExplanationService.generate_explanation(
                        rule_id=RuleID.XDOC_003.value,
                        field_name="destination",
                        expected_val=doc_a.destination,
                        actual_val=doc_b.destination,
                        difference="Non-matching destination addresses",
                        extra_context=f"Destination '{doc_a.destination}' in {doc_a.filename} differs from '{doc_b.destination}' in {doc_b.filename}.",
                    )
                    cross_discrepancies.append(
                        DiscrepancyCreate(
                            document_id=doc_b.document_id,
                            order_id=order_id,
                            field_name="destination",
                            discrepancy_type="CROSS_DOC_DESTINATION_MISMATCH",
                            severity=rule["default_severity"],
                            expected_value=f"{doc_a.destination} [{doc_a.filename}]",
                            actual_value=f"{doc_b.destination} [{doc_b.filename}]",
                            difference="Values differ",
                            rule_id=RuleID.XDOC_003.value,
                            rule_version=rule["version"],
                            source_page=doc_b.source_pages.get("destination"),
                            source_text=doc_b.fields.get("destination").source_text if "destination" in doc_b.fields else None,
                            explanation=expl,
                        )
                    )

        return cross_discrepancies

    # ---------------- Rule Implementation Helpers ----------------

    @classmethod
    def _check_order_reference(cls, doc: CanonicalDocument, order: OrderResponse) -> Optional[DiscrepancyCreate]:
        """ID-001: Verifies extracted order reference against approved order."""
        rule = RULE_DEFINITIONS[RuleID.ID_001.value]
        doc_ref = doc.order_reference
        expected_ref = order.order_number or order.id

        if not doc_ref:
            # If completely missing, handled by REQ-001
            return None

        clean_doc_ref = normalize_text_semantic(doc_ref)
        clean_exp_ref = normalize_text_semantic(expected_ref)

        if clean_doc_ref != clean_exp_ref and clean_doc_ref not in clean_exp_ref and clean_exp_ref not in clean_doc_ref:
            prov = doc.fields.get("order_reference")
            expl = ExplanationService.generate_explanation(
                rule_id=RuleID.ID_001.value,
                field_name="order_reference",
                expected_val=expected_ref,
                actual_val=doc_ref,
                difference="Identifier mismatch",
                doc_type=doc.document_type,
            )
            return DiscrepancyCreate(
                document_id=doc.document_id,
                order_id=order.id,
                field_name="order_reference",
                discrepancy_type="ORDER_IDENTITY_MISMATCH",
                severity=rule["default_severity"],
                expected_value=expected_ref,
                actual_value=doc_ref,
                difference="Does not match approved order",
                rule_id=RuleID.ID_001.value,
                rule_version=rule["version"],
                source_page=prov.page_number if prov else None,
                source_text=prov.source_text if prov else None,
                explanation=expl,
            )
        return None

    @classmethod
    def _check_required_fields(cls, doc: CanonicalDocument) -> List[DiscrepancyCreate]:
        """REQ-001: Checks required fields per document type."""
        discs: List[DiscrepancyCreate] = []
        rule = RULE_DEFINITIONS[RuleID.REQ_001.value]

        required_per_type = {
            "invoice": ["order_reference", "grand_total"],
            "packing_list": ["order_reference"],
            "bill_of_lading": ["order_reference", "destination"],
        }
        needed = required_per_type.get(doc.document_type, ["order_reference"])

        for field_name in needed:
            prov = doc.fields.get(field_name)
            is_missing = prov is None or prov.value is None or prov.value == ""
            if is_missing:
                expl = ExplanationService.generate_explanation(
                    rule_id=RuleID.REQ_001.value,
                    field_name=field_name,
                    expected_val="Required field present",
                    actual_val="Missing / Null",
                    difference="Field absent",
                    doc_type=doc.document_type,
                )
                discs.append(
                    DiscrepancyCreate(
                        document_id=doc.document_id,
                        order_id=None,
                        field_name=field_name,
                        discrepancy_type="REQUIRED_FIELD_MISSING",
                        severity=rule["default_severity"],
                        expected_value="Present in document",
                        actual_value="Missing/Not found",
                        difference="Missing",
                        rule_id=RuleID.REQ_001.value,
                        rule_version=rule["version"],
                        source_page=None,
                        source_text=None,
                        explanation=expl,
                    )
                )
        return discs

    @classmethod
    def _check_currency(cls, doc: CanonicalDocument, order: OrderResponse) -> Optional[DiscrepancyCreate]:
        """CUR-001: Verifies currency matches."""
        rule = RULE_DEFINITIONS[RuleID.CUR_001.value]
        if not doc.currency or not order.currency:
            return None

        norm_doc_cur = normalize_currency(doc.currency)
        norm_order_cur = normalize_currency(order.currency)

        if norm_doc_cur and norm_order_cur and norm_doc_cur != norm_order_cur:
            prov = doc.fields.get("currency")
            expl = ExplanationService.generate_explanation(
                rule_id=RuleID.CUR_001.value,
                field_name="currency",
                expected_val=norm_order_cur,
                actual_val=norm_doc_cur,
                difference="Currency mismatch",
                doc_type=doc.document_type,
            )
            return DiscrepancyCreate(
                document_id=doc.document_id,
                order_id=order.id,
                field_name="currency",
                discrepancy_type="CURRENCY_MISMATCH",
                severity=rule["default_severity"],
                expected_value=norm_order_cur,
                actual_value=norm_doc_cur,
                difference=f"Expected {norm_order_cur}, found {norm_doc_cur}",
                rule_id=RuleID.CUR_001.value,
                rule_version=rule["version"],
                source_page=prov.page_number if prov else None,
                source_text=prov.source_text if prov else None,
                explanation=expl,
            )
        return None

    @classmethod
    def _check_grand_total(cls, doc: CanonicalDocument, order: OrderResponse) -> Optional[DiscrepancyCreate]:
        """FIN-001: Checks grand total against order with Decimal precision."""
        rule = RULE_DEFINITIONS[RuleID.FIN_001.value]
        if doc.grand_total is None or order.grand_total is None:
            return None

        doc_total = Decimal(str(doc.grand_total))
        order_total = Decimal(str(order.grand_total))
        diff = abs(order_total - doc_total)

        if diff > settings.FINANCIAL_TOLERANCE:
            prov = doc.fields.get("grand_total")
            expl = ExplanationService.generate_explanation(
                rule_id=RuleID.FIN_001.value,
                field_name="grand_total",
                expected_val=str(order_total),
                actual_val=str(doc_total),
                difference=str(diff),
                doc_type=doc.document_type,
                currency=order.currency or "USD",
            )
            return DiscrepancyCreate(
                document_id=doc.document_id,
                order_id=order.id,
                field_name="grand_total",
                discrepancy_type="FINANCIAL_MISMATCH",
                severity=rule["default_severity"],
                expected_value=f"{order_total:.2f}",
                actual_value=f"{doc_total:.2f}",
                difference=f"{diff:.2f}",
                rule_id=RuleID.FIN_001.value,
                rule_version=rule["version"],
                source_page=prov.page_number if prov else None,
                source_text=prov.source_text if prov else None,
                explanation=expl,
            )
        return None

    @classmethod
    def _check_quantity(cls, doc: CanonicalDocument, order: OrderResponse) -> Optional[DiscrepancyCreate]:
        """QTY-001: Checks quantity against order with Decimal precision."""
        rule = RULE_DEFINITIONS[RuleID.QTY_001.value]
        qty_prov = doc.fields.get("quantity")
        if not qty_prov or qty_prov.numeric_value is None or order.quantity is None:
            return None

        doc_qty = Decimal(str(qty_prov.numeric_value))
        order_qty = Decimal(str(order.quantity))
        diff = abs(order_qty - doc_qty)

        if diff > settings.QUANTITY_TOLERANCE:
            expl = ExplanationService.generate_explanation(
                rule_id=RuleID.QTY_001.value,
                field_name="quantity",
                expected_val=str(order_qty),
                actual_val=str(doc_qty),
                difference=str(diff),
                doc_type=doc.document_type,
            )
            return DiscrepancyCreate(
                document_id=doc.document_id,
                order_id=order.id,
                field_name="quantity",
                discrepancy_type="QUANTITY_MISMATCH",
                severity=rule["default_severity"],
                expected_value=f"{order_qty:.2f}",
                actual_value=f"{doc_qty:.2f}",
                difference=f"{diff:.2f}",
                rule_id=RuleID.QTY_001.value,
                rule_version=rule["version"],
                source_page=qty_prov.page_number,
                source_text=qty_prov.source_text,
                explanation=expl,
            )
        return None

    @classmethod
    def _check_line_arithmetic(cls, doc: CanonicalDocument) -> List[DiscrepancyCreate]:
        """FIN-002: Verifies line item multiplication and sum against subtotal."""
        discs: List[DiscrepancyCreate] = []
        rule = RULE_DEFINITIONS[RuleID.FIN_002.value]

        # 1. Check item line calculation: qty * unit_price == line_total
        sum_lines = Decimal("0.00")
        for item in doc.items:
            expected_line_total = item.quantity * item.unit_price
            diff = abs(expected_line_total - item.line_total)
            if diff > Decimal("0.01"):
                expl = ExplanationService.generate_explanation(
                    rule_id=RuleID.FIN_002.value,
                    field_name="line_total",
                    expected_val=f"{expected_line_total:.2f}",
                    actual_val=f"{item.line_total:.2f}",
                    difference=f"{diff:.2f}",
                    doc_type=doc.document_type,
                    extra_context=f"Item '{item.description}' ({item.quantity} * {item.unit_price} = {expected_line_total:.2f}) does not match line total {item.line_total:.2f}.",
                )
                discs.append(
                    DiscrepancyCreate(
                        document_id=doc.document_id,
                        order_id=None,
                        field_name="line_total",
                        discrepancy_type="ARITHMETIC_MISMATCH",
                        severity=rule["default_severity"],
                        expected_value=f"{expected_line_total:.2f}",
                        actual_value=f"{item.line_total:.2f}",
                        difference=f"{diff:.2f}",
                        rule_id=RuleID.FIN_002.value,
                        rule_version=rule["version"],
                        source_page=item.page_number,
                        source_text=item.source_text,
                        explanation=expl,
                    )
                )
            sum_lines += item.line_total

        # 2. Check sum of lines vs subtotal (if subtotal exists)
        if doc.subtotal is not None and doc.items:
            diff_subtotal = abs(sum_lines - doc.subtotal)
            if diff_subtotal > Decimal("0.01"):
                subtotal_prov = doc.fields.get("subtotal")
                expl = ExplanationService.generate_explanation(
                    rule_id=RuleID.FIN_002.value,
                    field_name="subtotal",
                    expected_val=f"{sum_lines:.2f}",
                    actual_val=f"{doc.subtotal:.2f}",
                    difference=f"{diff_subtotal:.2f}",
                    doc_type=doc.document_type,
                    extra_context=f"Sum of item lines ({sum_lines:.2f}) does not equal document subtotal ({doc.subtotal:.2f}).",
                )
                discs.append(
                    DiscrepancyCreate(
                        document_id=doc.document_id,
                        order_id=None,
                        field_name="subtotal",
                        discrepancy_type="ARITHMETIC_MISMATCH",
                        severity=rule["default_severity"],
                        expected_value=f"{sum_lines:.2f}",
                        actual_value=f"{doc.subtotal:.2f}",
                        difference=f"{diff_subtotal:.2f}",
                        rule_id=RuleID.FIN_002.value,
                        rule_version=rule["version"],
                        source_page=subtotal_prov.page_number if subtotal_prov else None,
                        source_text=subtotal_prov.source_text if subtotal_prov else None,
                        explanation=expl,
                    )
                )

        return discs

    @classmethod
    def _check_destination(cls, doc: CanonicalDocument, order: OrderResponse) -> Optional[DiscrepancyCreate]:
        """DEST-001: Verifies destination delivery location."""
        rule = RULE_DEFINITIONS[RuleID.DEST_001.value]
        if not doc.destination or not order.destination:
            return None

        norm_doc_dest = normalize_text_semantic(doc.destination)
        norm_order_dest = normalize_text_semantic(order.destination)

        if norm_doc_dest != norm_order_dest and norm_order_dest not in norm_doc_dest and norm_doc_dest not in norm_order_dest:
            prov = doc.fields.get("destination")
            expl = ExplanationService.generate_explanation(
                rule_id=RuleID.DEST_001.value,
                field_name="destination",
                expected_val=order.destination,
                actual_val=doc.destination,
                difference="Destination differs",
                doc_type=doc.document_type,
            )
            return DiscrepancyCreate(
                document_id=doc.document_id,
                order_id=order.id,
                field_name="destination",
                discrepancy_type="DESTINATION_MISMATCH",
                severity=rule["default_severity"],
                expected_value=order.destination,
                actual_value=doc.destination,
                difference="Differs from approved order destination",
                rule_id=RuleID.DEST_001.value,
                rule_version=rule["version"],
                source_page=prov.page_number if prov else None,
                source_text=prov.source_text if prov else None,
                explanation=expl,
            )
        return None

