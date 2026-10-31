"""
Structured Field Extractor for commercial documents: Invoices, Packing Lists, Bills of Lading.
Extracts fields conservatively with exact page number and source text provenance.
Never fabricates missing values.
"""

import re
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from app.core.constants import DocumentType
from app.schemas.document import (
    CanonicalDocument,
    DocumentItemSchema,
    ExtractedFieldProvenance,
)
from app.services.normalization import (
    normalize_currency,
    normalize_unit,
    normalize_whitespace,
    parse_decimal_value,
)


class FieldExtractor:
    """Extracts canonical business fields with evidence provenance from document pages."""

    @classmethod
    def classify_document_type(cls, full_text: str) -> str:
        """Determines whether the document is an Invoice, Packing List, Bill of Lading, or Unknown."""
        text_upper = full_text.upper()

        # Check in priority order
        if any(term in text_upper for term in ["BILL OF LADING", "OCEAN BILL OF LADING", "SEA WAYBILL", "B/L NO"]):
            return DocumentType.BILL_OF_LADING.value
        elif any(term in text_upper for term in ["PACKING LIST", "PACKING SLIP", "DELIVERY NOTE", "CARGO LIST"]):
            return DocumentType.PACKING_LIST.value
        elif any(term in text_upper for term in ["COMMERCIAL INVOICE", "TAX INVOICE", "INVOICE NO", "INVOICE NUMBER", "INVOICE"]):
            return DocumentType.INVOICE.value

        return DocumentType.UNKNOWN.value

    @classmethod
    def extract_fields(
        cls,
        document_id: str,
        filename: str,
        pages: List[Dict[str, Any]],
        document_type_hint: Optional[str] = None,
    ) -> CanonicalDocument:
        """
        Parses pages to build a CanonicalDocument with field provenance.
        """
        full_text = "\n".join([p.get("text", "") for p in pages])
        doc_type = document_type_hint if document_type_hint and document_type_hint != "unknown" else cls.classify_document_type(full_text)

        provenance_fields: Dict[str, ExtractedFieldProvenance] = {}
        source_pages: Dict[str, Optional[int]] = {}

        # 1. Order Reference
        order_ref, ref_page, ref_text = cls._extract_order_reference(pages)
        if order_ref:
            provenance_fields["order_reference"] = ExtractedFieldProvenance(
                field_name="order_reference",
                value=order_ref,
                page_number=ref_page,
                source_text=ref_text,
                source_document_id=document_id,
            )
            source_pages["order_reference"] = ref_page

        # 2. Customer / Buyer Name
        customer, cust_page, cust_text = cls._extract_customer_name(pages)
        if customer:
            provenance_fields["customer_name"] = ExtractedFieldProvenance(
                field_name="customer_name",
                value=customer,
                page_number=cust_page,
                source_text=cust_text,
                source_document_id=document_id,
            )
            source_pages["customer_name"] = cust_page

        # 3. Currency
        currency, curr_page, curr_text = cls._extract_currency(pages)
        if currency:
            provenance_fields["currency"] = ExtractedFieldProvenance(
                field_name="currency",
                value=currency,
                page_number=curr_page,
                source_text=curr_text,
                source_document_id=document_id,
            )
            source_pages["currency"] = curr_page

        # 4. Financial Totals (Grand Total, Subtotal, Tax, Freight)
        totals = cls._extract_financials(pages)
        for field_key in ["grand_total", "subtotal", "tax", "freight"]:
            item = totals.get(field_key)
            if item and item.get("val") is not None:
                dec_val = item["val"]
                provenance_fields[field_key] = ExtractedFieldProvenance(
                    field_name=field_key,
                    value=str(dec_val),
                    numeric_value=dec_val,
                    unit=currency or item.get("curr"),
                    page_number=item.get("page"),
                    source_text=item.get("text"),
                    source_document_id=document_id,
                )
                source_pages[field_key] = item.get("page")

        # 5. Destination (Port of discharge / Delivery address)
        dest, dest_page, dest_text = cls._extract_destination(pages)
        if dest:
            provenance_fields["destination"] = ExtractedFieldProvenance(
                field_name="destination",
                value=dest,
                page_number=dest_page,
                source_text=dest_text,
                source_document_id=document_id,
            )
            source_pages["destination"] = dest_page

        # 6. Package Count
        pkg_count, pkg_page, pkg_text = cls._extract_package_count(pages)
        if pkg_count is not None:
            provenance_fields["package_count"] = ExtractedFieldProvenance(
                field_name="package_count",
                value=str(pkg_count),
                numeric_value=Decimal(pkg_count),
                unit="PKGS",
                page_number=pkg_page,
                source_text=pkg_text,
                source_document_id=document_id,
            )
            source_pages["package_count"] = pkg_page

        # 7. Gross Weight
        weight_str, w_page, w_text = cls._extract_gross_weight(pages)
        if weight_str:
            provenance_fields["gross_weight"] = ExtractedFieldProvenance(
                field_name="gross_weight",
                value=weight_str,
                page_number=w_page,
                source_text=w_text,
                source_document_id=document_id,
            )
            source_pages["gross_weight"] = w_page

        # 8. Items Extraction
        items = cls._extract_items(pages)

        # 9. Total Quantity (either from items sum or explicit label)
        tot_qty, qty_page, qty_text = cls._extract_quantity(pages, items)
        if tot_qty is not None:
            provenance_fields["quantity"] = ExtractedFieldProvenance(
                field_name="quantity",
                value=str(tot_qty),
                numeric_value=tot_qty,
                page_number=qty_page,
                source_text=qty_text,
                source_document_id=document_id,
            )
            source_pages["quantity"] = qty_page

        grand_total_dec = provenance_fields.get("grand_total").numeric_value if "grand_total" in provenance_fields else None
        subtotal_dec = provenance_fields.get("subtotal").numeric_value if "subtotal" in provenance_fields else None
        tax_dec = provenance_fields.get("tax").numeric_value if "tax" in provenance_fields else None
        freight_dec = provenance_fields.get("freight").numeric_value if "freight" in provenance_fields else None

        return CanonicalDocument(
            document_id=document_id,
            filename=filename,
            document_type=doc_type,
            order_reference=provenance_fields.get("order_reference").value if "order_reference" in provenance_fields else None,
            customer_name=provenance_fields.get("customer_name").value if "customer_name" in provenance_fields else None,
            currency=provenance_fields.get("currency").value if "currency" in provenance_fields else None,
            items=items,
            subtotal=subtotal_dec,
            tax=tax_dec,
            freight=freight_dec,
            grand_total=grand_total_dec,
            destination=provenance_fields.get("destination").value if "destination" in provenance_fields else None,
            package_count=pkg_count,
            gross_weight=weight_str,
            fields=provenance_fields,
            source_pages=source_pages,
        )

    # ----------------- Field extractors with regex patterns -----------------

    @classmethod
    def _extract_order_reference(cls, pages: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[int], Optional[str]]:
        patterns = [
            r"(?:Order\s*(?:Ref|Reference|No|Number|#)?|PO\s*(?:No|Number|#)?|Purchase\s*Order(?:\s*No|#)?)\s*[:\-\s]\s*([A-Za-z0-9_\-]+)",
            r"\b(ORD\-[A-Za-z0-9\-]+)\b",
            r"\b(PO\-[A-Za-z0-9\-]+)\b",
        ]
        for p in pages:
            text = p.get("text", "")
            page_num = p.get("page_number", 1)
            for pat in patterns:
                match = re.search(pat, text, re.IGNORECASE)
                if match:
                    order_ref = match.group(1).strip()
                    # Exclude generic labels
                    if order_ref.upper() not in ["NO", "NUMBER", "DATE", "REF"]:
                        full_line = match.group(0).strip()
                        return order_ref, page_num, full_line
        return None, None, None

    @classmethod
    def _extract_customer_name(cls, pages: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[int], Optional[str]]:
        patterns = [
            r"(?:Customer(?:\s*Name)?|Bill\s*To|Buyer|Consignee|Sold\s*To)\s*[:\-]?\s*([A-Za-z0-9\s,\.\-&]{3,50})(?:\n|$)",
        ]
        for p in pages:
            text = p.get("text", "")
            page_num = p.get("page_number", 1)
            for pat in patterns:
                match = re.search(pat, text, re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
                    first_line = name.split("\n")[0].strip()
                    if len(first_line) > 2 and not any(kw in first_line.lower() for kw in ["invoice", "date", "address"]):
                        return first_line, page_num, match.group(0).strip()
        return None, None, None

    @classmethod
    def _extract_currency(cls, pages: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[int], Optional[str]]:
        for p in pages:
            text = p.get("text", "")
            page_num = p.get("page_number", 1)

            # Explicit currency label
            curr_match = re.search(r"Currency\s*[:\-]?\s*([A-Za-z]{3}|\$|€|£|₹)", text, re.IGNORECASE)
            if curr_match:
                norm = normalize_currency(curr_match.group(1))
                if norm:
                    return norm, page_num, curr_match.group(0).strip()

            # Symbol or code near financial numbers
            match = re.search(r"\b(USD|EUR|GBP|INR|CAD|AUD)\b", text, re.IGNORECASE)
            if match:
                norm = normalize_currency(match.group(1))
                return norm, page_num, match.group(0).strip()

            if "$" in text:
                return "USD", page_num, "$"
            elif "€" in text:
                return "EUR", page_num, "€"
            elif "£" in text:
                return "GBP", page_num, "£"

        return None, None, None

    @classmethod
    def _extract_financials(cls, pages: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        results: Dict[str, Dict[str, Any]] = {}

        patterns = {
            "grand_total": [
                r"(?:Grand\s*Total|Total\s*Amount|Invoice\s*Total|Final\s*Total|Balance\s*Due|Total\s*Payable)\s*[:\-]?\s*([$€£₹]?\s*[A-Za-z]{0,3}\s*[\d,]+(?:\.\d{1,4})?)",
                r"(?<!Sub)Total\s*[:\-]?\s*([$€£₹]?\s*[A-Za-z]{0,3}\s*[\d,]+(?:\.\d{1,4})?)",
            ],
            "subtotal": [
                r"(?:Sub\s*Total|Subtotal|Net\s*Amount)\s*[:\-]?\s*([$€£₹]?\s*[A-Za-z]{0,3}\s*[\d,]+(?:\.\d{1,4})?)",
            ],
            "tax": [
                r"(?:Tax|VAT|GST)\s*(?:\([^)]*\))?\s*[:\-]?\s*([$€£₹]?\s*[A-Za-z]{0,3}\s*[\d,]+(?:\.\d{1,4})?)",
            ],
            "freight": [
                r"(?:Freight|Shipping|Handling|Transport)\s*(?:Charges|Cost)?\s*[:\-]?\s*([$€£₹]?\s*[A-Za-z]{0,3}\s*[\d,]+(?:\.\d{1,4})?)",
            ],
        }

        for p in pages:
            text = p.get("text", "")
            page_num = p.get("page_number", 1)

            for key, pat_list in patterns.items():
                if key in results:
                    continue
                for pat in pat_list:
                    match = re.search(pat, text, re.IGNORECASE)
                    if match:
                        raw_str = match.group(1).strip()
                        dec_val, detected_curr = parse_decimal_value(raw_str)
                        if dec_val is not None:
                            results[key] = {
                                "val": dec_val,
                                "curr": detected_curr,
                                "page": page_num,
                                "text": match.group(0).strip(),
                            }
                            break

        return results

    @classmethod
    def _extract_destination(cls, pages: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[int], Optional[str]]:
        patterns = [
            r"(?:Port\s*of\s*Discharge|Destination|Ship\s*To|Deliver\s*To|Final\s*Destination)\s*[:\-]?\s*([A-Za-z0-9\s,\.\-]{3,60})(?:\n|$)",
        ]
        for p in pages:
            text = p.get("text", "")
            page_num = p.get("page_number", 1)
            for pat in patterns:
                match = re.search(pat, text, re.IGNORECASE)
                if match:
                    dest = match.group(1).strip()
                    first_line = dest.split("\n")[0].strip()
                    if len(first_line) > 2:
                        return first_line, page_num, match.group(0).strip()
        return None, None, None

    @classmethod
    def _extract_package_count(cls, pages: List[Dict[str, Any]]) -> Tuple[Optional[int], Optional[int], Optional[str]]:
        patterns = [
            r"(?:Total\s*Packages?|Package\s*Count|No\.?\s*of\s*Packages?|Cartons?|Boxes?|Packages?)\s*[:\-]?\s*(\d+)",
        ]
        for p in pages:
            text = p.get("text", "")
            page_num = p.get("page_number", 1)
            for pat in patterns:
                match = re.search(pat, text, re.IGNORECASE)
                if match:
                    try:
                        val = int(match.group(1))
                        return val, page_num, match.group(0).strip()
                    except ValueError:
                        pass
        return None, None, None

    @classmethod
    def _extract_gross_weight(cls, pages: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[int], Optional[str]]:
        patterns = [
            r"(?:Gross\s*Weight|G\.?W\.?|Total\s*Weight)\s*[:\-]?\s*([\d,]+(?:\.\d+)?\s*(?:KG|KGS|MT|LBS|TONS?))",
        ]
        for p in pages:
            text = p.get("text", "")
            page_num = p.get("page_number", 1)
            for pat in patterns:
                match = re.search(pat, text, re.IGNORECASE)
                if match:
                    return match.group(1).strip(), page_num, match.group(0).strip()
        return None, None, None

    @classmethod
    def _extract_quantity(
        cls, pages: List[Dict[str, Any]], items: List[DocumentItemSchema]
    ) -> Tuple[Optional[Decimal], Optional[int], Optional[str]]:
        if items:
            total_qty = sum((item.quantity for item in items), Decimal("0"))
            return total_qty, items[0].page_number or 1, f"Sum of {len(items)} line item(s): {total_qty}"

        patterns = [
            r"(?:Total\s*Qty|Total\s*Quantity|Quantity|Qty)\s*[:\-]?\s*([\d,]+(?:\.\d+)?)",
        ]
        for p in pages:
            text = p.get("text", "")
            page_num = p.get("page_number", 1)
            for pat in patterns:
                match = re.search(pat, text, re.IGNORECASE)
                if match:
                    raw_str = match.group(1).strip()
                    dec_val, _ = parse_decimal_value(raw_str)
                    if dec_val is not None:
                        return dec_val, page_num, match.group(0).strip()
        return None, None, None

    @classmethod
    def _extract_items(cls, pages: List[Dict[str, Any]]) -> List[DocumentItemSchema]:
        """
        Extracts structured item rows from tabular/line sections.
        Conservative pattern looking for line items with description, quantity, price, line total.
        """
        items: List[DocumentItemSchema] = []
        # Pattern: SKU (opt) Description Qty Unit UnitPrice LineTotal
        line_item_pattern = re.compile(
            r"(?:(?P<sku>[A-Za-z0-9\-]{3,15})\s+)?(?P<desc>[A-Za-z0-9\s\.\-]{3,40})\s+(?P<qty>[\d,]+(?:\.\d+)?)\s*(?P<unit>[A-Za-z]{2,5})?\s+[@$€£]?\s*(?P<price>[\d,]+(?:\.\d{1,4})?)\s+[$€£]?\s*(?P<total>[\d,]+(?:\.\d{1,4})?)",
            re.IGNORECASE,
        )

        for p in pages:
            text = p.get("text", "")
            page_num = p.get("page_number", 1)
            for line in text.split("\n"):
                line_str = line.strip()
                if not line_str or any(kw in line_str.upper() for kw in ["TOTAL", "SUBTOTAL", "DATE", "INVOICE NO", "DESCRIPTION"]):
                    continue

                m = line_item_pattern.search(line_str)
                if m:
                    qty_val, _ = parse_decimal_value(m.group("qty"))
                    price_val, _ = parse_decimal_value(m.group("price"))
                    tot_val, _ = parse_decimal_value(m.group("total"))

                    if qty_val is not None and price_val is not None and tot_val is not None:
                        sku_val = m.group("sku")
                        desc_val = m.group("desc").strip()
                        unit_val = normalize_unit(m.group("unit")) or "PCS"

                        items.append(
                            DocumentItemSchema(
                                sku=sku_val,
                                description=desc_val,
                                quantity=qty_val,
                                unit=unit_val,
                                unit_price=price_val,
                                line_total=tot_val,
                                page_number=page_num,
                                source_text=line_str,
                            )
                        )
        return items

