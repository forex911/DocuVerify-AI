import React from 'react';
import { Order, CanonicalDocument, Discrepancy } from '../../types';
import { SeverityBadge } from '../common/SeverityBadge';
import { Check, AlertTriangle, ArrowRight } from 'lucide-react';

interface ComparisonTableProps {
  order?: Order | null;
  canonicalDoc?: CanonicalDocument | null;
  discrepancies: Discrepancy[];
  onSelectDiscrepancy?: (discrepancy: Discrepancy) => void;
  selectedDiscrepancyId?: string | null;
}

interface FieldComparisonRow {
  fieldName: string;
  label: string;
  orderValue: string | number | null | undefined;
  docValue: string | number | null | undefined;
  pageNumber?: number | null;
  sourceText?: string | null;
}

export const ComparisonTable: React.FC<ComparisonTableProps> = ({
  order,
  canonicalDoc,
  discrepancies,
  onSelectDiscrepancy,
  selectedDiscrepancyId,
}) => {
  if (!order && !canonicalDoc) {
    return (
      <div className="p-8 text-center text-xs text-slate-400 bg-white rounded-xl border border-slate-200">
        Select a document and order to view field comparison.
      </div>
    );
  }

  // Construct normalized rows
  const rows: FieldComparisonRow[] = [
    {
      fieldName: 'order_reference',
      label: 'Order Reference',
      orderValue: order ? order.order_number || order.id : null,
      docValue: canonicalDoc?.order_reference?.value,
      pageNumber: canonicalDoc?.order_reference?.page_number,
      sourceText: canonicalDoc?.order_reference?.source_text,
    },
    {
      fieldName: 'customer_name',
      label: 'Customer Name',
      orderValue: order?.customer_name,
      docValue: canonicalDoc?.customer_name?.value,
      pageNumber: canonicalDoc?.customer_name?.page_number,
      sourceText: canonicalDoc?.customer_name?.source_text,
    },
    {
      fieldName: 'currency',
      label: 'Currency',
      orderValue: order?.currency,
      docValue: canonicalDoc?.currency?.value,
      pageNumber: canonicalDoc?.currency?.page_number,
      sourceText: canonicalDoc?.currency?.source_text,
    },
    {
      fieldName: 'quantity',
      label: 'Total Quantity',
      orderValue: order ? `${order.quantity} PCS` : null,
      docValue:
        canonicalDoc?.line_items && canonicalDoc.line_items.length > 0
          ? `${canonicalDoc.line_items[0].quantity} ${canonicalDoc.line_items[0].unit}`
          : null,
      pageNumber: canonicalDoc?.line_items?.[0]?.page_number,
      sourceText: canonicalDoc?.line_items?.[0]?.source_text,
    },
    {
      fieldName: 'unit_price',
      label: 'Unit Price',
      orderValue: order ? `$${Number(order.unit_price).toFixed(2)}` : null,
      docValue:
        canonicalDoc?.line_items?.[0]?.unit_price != null
          ? `$${Number(canonicalDoc.line_items[0].unit_price).toFixed(2)}`
          : null,
      pageNumber: canonicalDoc?.line_items?.[0]?.page_number,
    },
    {
      fieldName: 'subtotal',
      label: 'Subtotal',
      orderValue: order ? `$${Number(order.subtotal).toFixed(2)}` : null,
      docValue:
        canonicalDoc?.subtotal?.value != null
          ? `$${Number(canonicalDoc.subtotal.value).toFixed(2)}`
          : null,
      pageNumber: canonicalDoc?.subtotal?.page_number,
      sourceText: canonicalDoc?.subtotal?.source_text,
    },
    {
      fieldName: 'tax',
      label: 'Tax / VAT',
      orderValue: order ? `$${Number(order.tax).toFixed(2)}` : null,
      docValue:
        canonicalDoc?.tax?.value != null
          ? `$${Number(canonicalDoc.tax.value).toFixed(2)}`
          : null,
      pageNumber: canonicalDoc?.tax?.page_number,
      sourceText: canonicalDoc?.tax?.source_text,
    },
    {
      fieldName: 'freight',
      label: 'Freight Charges',
      orderValue: order ? `$${Number(order.freight).toFixed(2)}` : null,
      docValue:
        canonicalDoc?.freight?.value != null
          ? `$${Number(canonicalDoc.freight.value).toFixed(2)}`
          : null,
      pageNumber: canonicalDoc?.freight?.page_number,
      sourceText: canonicalDoc?.freight?.source_text,
    },
    {
      fieldName: 'grand_total',
      label: 'Grand Total Amount',
      orderValue: order ? `$${Number(order.grand_total).toFixed(2)}` : null,
      docValue:
        canonicalDoc?.grand_total?.value != null
          ? `$${Number(canonicalDoc.grand_total.value).toFixed(2)}`
          : null,
      pageNumber: canonicalDoc?.grand_total?.page_number,
      sourceText: canonicalDoc?.grand_total?.source_text,
    },
    {
      fieldName: 'destination',
      label: 'Destination / Port',
      orderValue: order?.destination,
      docValue: canonicalDoc?.destination?.value,
      pageNumber: canonicalDoc?.destination?.page_number,
      sourceText: canonicalDoc?.destination?.source_text,
    },
    {
      fieldName: 'package_count',
      label: 'Package Count',
      orderValue: order?.package_count != null ? `${order.package_count} PKGS` : null,
      docValue:
        canonicalDoc?.package_count?.value != null
          ? `${canonicalDoc.package_count.value} PKGS`
          : null,
      pageNumber: canonicalDoc?.package_count?.page_number,
      sourceText: canonicalDoc?.package_count?.source_text,
    },
  ];

  const findDiscrepancy = (fieldName: string) => {
    return discrepancies.find((d) => {
      const df = (d.field_name || '').toLowerCase();
      const fn = fieldName.toLowerCase();
      return df === fn || (fn === 'grand_total' && df.includes('total')) || (fn === 'quantity' && df.includes('qty'));
    });
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-subtle">
      <div className="px-5 py-3 border-b border-slate-200 bg-slate-50/75 flex items-center justify-between">
        <div>
          <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            Deterministic Field Reconciliation
          </h4>
          <p className="text-[11px] text-slate-500">
            Comparing Approved Order baseline against digital extraction provenance
          </p>
        </div>
        <div className="text-xs font-medium text-slate-500 flex items-center gap-3">
          <span className="flex items-center gap-1 text-emerald-700">
            <Check className="w-3.5 h-3.5 text-emerald-600" /> Match
          </span>
          <span className="flex items-center gap-1 text-red-700">
            <AlertTriangle className="w-3.5 h-3.5 text-red-500" /> Variance Detected
          </span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50/50">
              <th className="py-2.5 px-4 font-semibold text-slate-600 uppercase text-[10px] tracking-wider">
                Field
              </th>
              <th className="py-2.5 px-4 font-semibold text-slate-600 uppercase text-[10px] tracking-wider">
                Approved Baseline (Order)
              </th>
              <th className="py-2.5 px-4 font-semibold text-slate-600 uppercase text-[10px] tracking-wider">
                Extracted Provenance (Document)
              </th>
              <th className="py-2.5 px-4 font-semibold text-slate-600 uppercase text-[10px] tracking-wider">
                Page
              </th>
              <th className="py-2.5 px-4 font-semibold text-slate-600 uppercase text-[10px] tracking-wider">
                Verification Status
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.map((row) => {
              const disc = findDiscrepancy(row.fieldName);
              const isSelected = disc && selectedDiscrepancyId === disc.id;

              return (
                <tr
                  key={row.fieldName}
                  onClick={() => disc && onSelectDiscrepancy && onSelectDiscrepancy(disc)}
                  className={`transition-colors ${
                    disc
                      ? 'bg-red-50/40 hover:bg-red-50/70 cursor-pointer'
                      : 'hover:bg-slate-50/80'
                  } ${isSelected ? 'ring-2 ring-red-500 ring-inset bg-red-100/50' : ''}`}
                >
                  <td className="py-2.5 px-4 font-medium text-slate-800">{row.label}</td>
                  <td className="py-2.5 px-4 font-mono text-slate-700">
                    {row.orderValue ?? <span className="text-slate-300">&mdash;</span>}
                  </td>
                  <td className="py-2.5 px-4 font-mono font-medium text-slate-900">
                    {row.docValue ?? <span className="text-slate-300 italic">Not extracted</span>}
                  </td>
                  <td className="py-2.5 px-4 text-slate-500">
                    {row.pageNumber ? `p. ${row.pageNumber}` : '&mdash;'}
                  </td>
                  <td className="py-2.5 px-4">
                    {disc ? (
                      <div className="flex items-center gap-2">
                        <SeverityBadge severity={disc.severity} size="sm" />
                        <span className="font-mono text-[10px] text-red-600 font-semibold">
                          {disc.rule_id}
                        </span>
                      </div>
                    ) : row.orderValue && row.docValue ? (
                      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700">
                        <Check className="w-3.5 h-3.5 text-emerald-600" /> Validated
                      </span>
                    ) : (
                      <span className="text-slate-400 text-[11px]">N/A</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

