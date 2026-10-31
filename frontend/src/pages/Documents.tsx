import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { documentsService } from '../services/documents.service';
import { StatusBadge } from '../components/common/StatusBadge';
import { LoadingState } from '../components/common/LoadingState';
import { EmptyState } from '../components/common/EmptyState';
import { UploadDocumentModal } from '../components/common/UploadDocumentModal';
import { LaunchVerificationModal } from '../components/common/LaunchVerificationModal';
import {
  FileText,
  UploadCloud,
  PlayCircle,
  ExternalLink,
  Search,
  Filter,
  Eye,
  FileCheck2,
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const Documents: React.FC = () => {
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [verifyModalDocId, setVerifyModalDocId] = useState<string | null>(null);

  const { data: documents = [], isLoading, refetch } = useQuery({
    queryKey: ['documents', typeFilter, statusFilter],
    queryFn: () =>
      documentsService.getDocuments({
        document_type: typeFilter || undefined,
        status: statusFilter || undefined,
      }),
  });

  const filteredDocuments = documents.filter((doc) => {
    const q = search.toLowerCase();
    return (
      doc.original_filename.toLowerCase().includes(q) ||
      doc.id.toLowerCase().includes(q) ||
      (doc.order_id && doc.order_id.toLowerCase().includes(q))
    );
  });

  return (
    <div className="space-y-5">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">Commercial Documents</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Ingested digital PDFs, parsed line items, and structured canonical schemas.
          </p>
        </div>

        <button
          onClick={() => setUploadModalOpen(true)}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition"
        >
          <UploadCloud className="w-4 h-4" />
          <span>Upload Commercial PDF</span>
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="card-subtle p-3.5 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 bg-white">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search by filename, document ID, order..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 text-xs rounded-lg border border-slate-200 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600"
          />
        </div>

        {/* Type Filter */}
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400 shrink-0" />
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="text-xs rounded-lg border border-slate-200 bg-slate-50/50 px-2.5 py-1.5 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600"
          >
            <option value="">All Document Types</option>
            <option value="invoice">Invoices</option>
            <option value="packing_list">Packing Lists</option>
            <option value="bill_of_lading">Bills of Lading</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs rounded-lg border border-slate-200 bg-slate-50/50 px-2.5 py-1.5 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600"
          >
            <option value="">All Statuses</option>
            <option value="EXTRACTED">Extracted</option>
            <option value="VERIFIED">Verified</option>
            <option value="REVIEW_REQUIRED">Review Required</option>
            <option value="PENDING">Pending</option>
          </select>
        </div>
      </div>

      {/* Documents Table */}
      {isLoading ? (
        <LoadingState message="Loading commercial documents..." />
      ) : filteredDocuments.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No commercial documents found"
          description="Upload an Invoice, Packing List, or Bill of Lading to begin digital verification."
          actionText="Upload Document"
          onAction={() => setUploadModalOpen(true)}
        />
      ) : (
        <div className="card-subtle overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/75">
                  <th className="table-th">Document / File</th>
                  <th className="table-th">Type</th>
                  <th className="table-th">Pages</th>
                  <th className="table-th">Associated Order</th>
                  <th className="table-th">Verification Status</th>
                  <th className="table-th">Ingested At</th>
                  <th className="table-th text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredDocuments.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/60 transition">
                    <td className="table-td">
                      <div className="flex items-center gap-2.5">
                        <div className="p-2 rounded-lg bg-blue-50 text-blue-600">
                          <FileText className="w-4 h-4" />
                        </div>
                        <div>
                          <Link
                            to={`/documents/${doc.id}`}
                            className="font-semibold text-slate-900 hover:text-blue-600 block transition"
                          >
                            {doc.original_filename}
                          </Link>
                          <span className="font-mono text-[10px] text-slate-400">
                            ID: {doc.id.slice(0, 12)}... &bull; {(doc.file_size / 1024).toFixed(1)} KB
                          </span>
                        </div>
                      </div>
                    </td>

                    <td className="table-td">
                      <span className="capitalize font-medium text-slate-700 px-2 py-0.5 bg-slate-100 rounded text-[11px]">
                        {doc.document_type.replace('_', ' ')}
                      </span>
                    </td>

                    <td className="table-td text-slate-600 font-mono">
                      {doc.page_count} {doc.page_count === 1 ? 'page' : 'pages'}
                    </td>

                    <td className="table-td">
                      {doc.order_id ? (
                        <Link
                          to={`/orders/${doc.order_id}`}
                          className="font-mono text-blue-600 hover:underline font-medium"
                        >
                          {doc.order_id}
                        </Link>
                      ) : (
                        <span className="text-slate-400 italic">Auto-match on verify</span>
                      )}
                    </td>

                    <td className="table-td">
                      <StatusBadge status={doc.status} size="sm" />
                    </td>

                    <td className="table-td text-slate-500 text-[11px]">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </td>

                    <td className="table-td text-right space-x-1">
                      <Link
                        to={`/documents/${doc.id}`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium text-[11px] transition"
                        title="Inspect Extracted Fields"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Inspect</span>
                      </Link>

                      <button
                        onClick={() => setVerifyModalDocId(doc.id)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-blue-50 hover:bg-blue-100 text-blue-700 font-medium text-[11px] transition"
                        title="Launch Verification"
                      >
                        <PlayCircle className="w-3.5 h-3.5 text-blue-600" />
                        <span>Verify</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modals */}
      <UploadDocumentModal
        isOpen={uploadModalOpen}
        onClose={() => {
          setUploadModalOpen(false);
          refetch();
        }}
      />

      {verifyModalDocId && (
        <LaunchVerificationModal
          isOpen={true}
          preselectedDocumentId={verifyModalDocId}
          onClose={() => setVerifyModalDocId(null)}
        />
      )}
    </div>
  );
};

