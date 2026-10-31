import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { documentsService } from '../services/documents.service';
import { PDFViewer } from '../components/verification/PDFViewer';
import { StatusBadge } from '../components/common/StatusBadge';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorBoundary } from '../components/common/ErrorBoundary';
import { LaunchVerificationModal } from '../components/common/LaunchVerificationModal';
import { CanonicalItem } from '../types';
import {
  Layers,
  PlayCircle,
  ArrowLeft,
  FileCheck2,
  FileText,
  Hash,
} from 'lucide-react';

const getVal = (val: any): string | null => {
  if (val == null) return null;
  if (typeof val === 'object' && val.value !== undefined) {
    return val.value != null ? String(val.value) : null;
  }
  return String(val);
};

export const DocumentDetailContent: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [verifyModalOpen, setVerifyModalOpen] = useState(false);
  const [selectedPage, setSelectedPage] = useState<number | null>(null);

  const { data: document, isLoading, error } = useQuery({
    queryKey: ['document', id],
    queryFn: () => documentsService.getDocument(id!),
    enabled: !!id,
  });

  const { data: extraction } = useQuery({
    queryKey: ['document-extraction', id],
    queryFn: () => documentsService.getDocumentExtraction(id!),
    enabled: !!id,
  });

  if (isLoading) {
    return <LoadingState message="Retrieving structured document extraction..." />;
  }

  if (error || !document) {
    return (
      <div className="p-8 text-center text-xs text-red-600 bg-red-50 border border-red-200 rounded-xl">
        Failed to locate document '{id}'.
      </div>
    );
  }

  const canonical = document.canonical_document;
  const items: CanonicalItem[] = canonical?.items || canonical?.line_items || [];

  const orderRef = getVal(canonical?.order_reference) || canonical?.fields?.order_reference?.value;
  const customerName = getVal(canonical?.customer_name) || canonical?.fields?.customer_name?.value;
  const currency = getVal(canonical?.currency) || canonical?.fields?.currency?.value;
  const destination = getVal(canonical?.destination) || canonical?.fields?.destination?.value;
  const grandTotal = getVal(canonical?.grand_total) || canonical?.fields?.grand_total?.value;
  const packageCount = getVal(canonical?.package_count) || canonical?.fields?.package_count?.value;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <Link
            to="/documents"
            className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-slate-800 transition mb-1"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Documents</span>
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold tracking-tight text-slate-900">
              {document.original_filename}
            </h1>
            <StatusBadge status={document.status} size="sm" />
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Document ID: <span className="font-mono">{document.id}</span>
          </p>
        </div>

        <button
          onClick={() => setVerifyModalOpen(true)}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition"
        >
          <PlayCircle className="w-4 h-4" />
          <span>Verify Document</span>
        </button>
      </div>

      {/* Metadata strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="card-subtle p-3 text-xs">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
            Classification
          </span>
          <span className="font-bold text-slate-800 capitalize mt-0.5 block">
            {document.document_type.replace('_', ' ')}
          </span>
        </div>
        <div className="card-subtle p-3 text-xs">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
            Extraction Engine
          </span>
          <span className="font-mono text-slate-800 mt-0.5 block">
            {document.extraction_method || 'PyMuPDF Direct'}
          </span>
        </div>
        <div className="card-subtle p-3 text-xs">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
            File Integrity (SHA-256)
          </span>
          <span className="font-mono text-[11px] text-slate-600 mt-0.5 block truncate" title={document.file_hash}>
            {document.file_hash.slice(0, 16)}...
          </span>
        </div>
        <div className="card-subtle p-3 text-xs">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
            Page Count & Size
          </span>
          <span className="text-slate-800 mt-0.5 block font-medium">
            {document.page_count} {document.page_count === 1 ? 'Page' : 'Pages'} &bull;{' '}
            {(document.file_size / 1024).toFixed(1)} KB
          </span>
        </div>
      </div>

      {/* Main 2-column layout: Left Structured Fields, Right PDF Viewer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left: Structured Canonical Representation */}
        <div className="lg:col-span-6 space-y-5">
          {/* Header Summary */}
          <div className="card-subtle p-5">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 mb-3 flex items-center gap-2">
              <Layers className="w-4 h-4 text-blue-600" />
              <span>Extracted Canonical Fields</span>
            </h3>

            {canonical ? (
              <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-xs">
                <div>
                  <dt className="text-slate-500 text-[10px] uppercase font-bold">Order Reference</dt>
                  <dd className="font-mono font-bold text-slate-900 mt-0.5">
                    {orderRef || <span className="text-slate-300">N/A</span>}
                  </dd>
                </div>
                <div>
                  <dt className="text-slate-500 text-[10px] uppercase font-bold">Customer</dt>
                  <dd className="font-semibold text-slate-900 mt-0.5">
                    {customerName || <span className="text-slate-300">N/A</span>}
                  </dd>
                </div>
                <div>
                  <dt className="text-slate-500 text-[10px] uppercase font-bold">Currency</dt>
                  <dd className="font-mono font-semibold text-slate-900 mt-0.5">
                    {currency || <span className="text-slate-300">N/A</span>}
                  </dd>
                </div>
                <div>
                  <dt className="text-slate-500 text-[10px] uppercase font-bold">Destination</dt>
                  <dd className="font-medium text-slate-900 mt-0.5">
                    {destination || <span className="text-slate-300">N/A</span>}
                  </dd>
                </div>
                <div>
                  <dt className="text-slate-500 text-[10px] uppercase font-bold">Grand Total</dt>
                  <dd className="font-mono font-bold text-slate-900 mt-0.5 text-sm text-blue-700">
                    {grandTotal != null ? `$${Number(grandTotal).toLocaleString()}` : 'N/A'}
                  </dd>
                </div>
                <div>
                  <dt className="text-slate-500 text-[10px] uppercase font-bold">Package Count</dt>
                  <dd className="font-mono font-semibold text-slate-900 mt-0.5">
                    {packageCount || <span className="text-slate-300">N/A</span>}
                  </dd>
                </div>
              </dl>
            ) : (
              <p className="text-xs text-slate-400">Structured data extraction is in progress or unavailable.</p>
            )}
          </div>

          {/* Line Items */}
          <div className="card-subtle overflow-hidden">
            <div className="p-4 border-b border-slate-200 bg-slate-50/75">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                Extracted Line Items ({items.length})
              </h3>
            </div>
            {items.length === 0 ? (
              <p className="p-6 text-xs text-slate-400 text-center">No line items parsed.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-200 bg-slate-50/50">
                      <th className="table-th">SKU</th>
                      <th className="table-th">Description</th>
                      <th className="table-th">Qty</th>
                      <th className="table-th">Unit Price</th>
                      <th className="table-th">Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {items.map((item, idx) => (
                      <tr key={idx} className="hover:bg-slate-50/60">
                        <td className="table-td font-mono font-semibold text-slate-800">
                          {item.sku || 'N/A'}
                        </td>
                        <td className="table-td text-slate-700">{item.description}</td>
                        <td className="table-td font-mono text-slate-800">
                          {item.quantity} {item.unit}
                        </td>
                        <td className="table-td font-mono text-slate-700">
                          {item.unit_price != null ? `$${Number(item.unit_price).toFixed(2)}` : '—'}
                        </td>
                        <td className="table-td font-mono font-semibold text-slate-900">
                          {item.line_total != null ? `$${Number(item.line_total).toFixed(2)}` : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Raw Extraction Pages */}
          {extraction && extraction.pages && (
            <div className="card-subtle p-5 space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                Page-by-Page Extraction Provenance
              </h3>
              <div className="space-y-2">
                {extraction.pages.map((p: any) => (
                  <div
                    key={p.page_number}
                    onClick={() => setSelectedPage(p.page_number)}
                    className="p-3 rounded-lg border border-slate-200 hover:border-blue-400 bg-slate-50 cursor-pointer transition"
                  >
                    <div className="flex items-center justify-between text-xs font-semibold text-slate-800 mb-1">
                      <span>Page {p.page_number}</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-100 text-blue-800">
                        Jump to page in viewer &rarr;
                      </span>
                    </div>
                    <p className="font-mono text-[11px] text-slate-600 line-clamp-3">
                      {p.text}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right: PDF Stream Viewer */}
        <div className="lg:col-span-6 h-[720px] sticky top-6">
          <PDFViewer
            documentId={document.id}
            filename={document.original_filename}
            highlightPage={selectedPage}
          />
        </div>
      </div>

      <LaunchVerificationModal
        isOpen={verifyModalOpen}
        preselectedDocumentId={document.id}
        onClose={() => setVerifyModalOpen(false)}
      />
    </div>
  );
};

export const DocumentDetail: React.FC = () => (
  <ErrorBoundary>
    <DocumentDetailContent />
  </ErrorBoundary>
);
