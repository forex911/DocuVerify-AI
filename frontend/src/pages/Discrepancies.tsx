import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { discrepanciesService } from '../services/discrepancies.service';
import { SeverityBadge } from '../components/common/SeverityBadge';
import { StatusBadge } from '../components/common/StatusBadge';
import { LoadingState } from '../components/common/LoadingState';
import { EmptyState } from '../components/common/EmptyState';
import { ReviewDecisionModal } from '../components/review/ReviewDecisionModal';
import { Discrepancy } from '../types';
import {
  AlertTriangle,
  UserCheck,
  Search,
  Filter,
  Eye,
  FileText,
  ShieldAlert,
  ArrowRight,
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const Discrepancies: React.FC = () => {
  const [search, setSearch] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedDiscrepancy, setSelectedDiscrepancy] = useState<Discrepancy | null>(null);

  const { data: discrepancies = [], isLoading, refetch } = useQuery({
    queryKey: ['discrepancies', severityFilter, statusFilter],
    queryFn: () =>
      discrepanciesService.getDiscrepancies({
        severity: severityFilter || undefined,
        review_status: statusFilter || undefined,
      }),
  });

  const filtered = discrepancies.filter((d) => {
    const q = search.toLowerCase();
    return (
      d.description.toLowerCase().includes(q) ||
      d.rule_id.toLowerCase().includes(q) ||
      d.field_name.toLowerCase().includes(q) ||
      (d.order_id && d.order_id.toLowerCase().includes(q))
    );
  });

  return (
    <div className="space-y-5">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">
            Discrepancies & Variances Ledger
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Deterministic anomalies detected across commercial documents and baseline purchase orders.
          </p>
        </div>

        <div className="p-2.5 rounded-lg bg-amber-50 border border-amber-200/80 text-amber-900 text-xs flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0" />
          <span>Requires Human Review: Reviewers hold sole authority to approve or reject</span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="card-subtle p-3.5 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 bg-white">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search by rule ID (e.g. FIN-001), description, field..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 text-xs rounded-lg border border-slate-200 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400 shrink-0" />
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="text-xs rounded-lg border border-slate-200 bg-slate-50/50 px-2.5 py-1.5 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs rounded-lg border border-slate-200 bg-slate-50/50 px-2.5 py-1.5 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600"
          >
            <option value="">All Review Statuses</option>
            <option value="PENDING">Pending Review</option>
            <option value="APPROVED">Approved</option>
            <option value="ACCEPTED_WITH_EXCEPTION">Accepted w/ Exception</option>
            <option value="REJECTED">Rejected</option>
          </select>
        </div>
      </div>

      {/* Discrepancies Table */}
      {isLoading ? (
        <LoadingState message="Loading discrepancy ledger..." />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={AlertTriangle}
          title="No discrepancies found"
          description="There are currently no discrepancy records matching the active filters."
        />
      ) : (
        <div className="card-subtle overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/75">
                  <th className="table-th">Rule & Severity</th>
                  <th className="table-th">Condition Description</th>
                  <th className="table-th">Expected (Order)</th>
                  <th className="table-th">Actual (Document)</th>
                  <th className="table-th">Source Page</th>
                  <th className="table-th">Review Status</th>
                  <th className="table-th text-right">Human Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filtered.map((disc) => (
                  <tr key={disc.id} className="hover:bg-slate-50/60 transition">
                    <td className="table-td">
                      <div className="flex items-center gap-2">
                        <SeverityBadge severity={disc.severity} size="sm" />
                        <span className="font-mono font-bold text-slate-900">
                          {disc.rule_id}
                        </span>
                      </div>
                    </td>

                    <td className="table-td font-semibold text-slate-800 max-w-sm">
                      {disc.description}
                    </td>

                    <td className="table-td font-mono text-slate-700">
                      {disc.expected_value || '—'}
                    </td>

                    <td className="table-td font-mono font-semibold text-red-700">
                      {disc.actual_value || 'Missing'}
                    </td>

                    <td className="table-td text-slate-500">
                      {disc.page_number ? `Page ${disc.page_number}` : '—'}
                    </td>

                    <td className="table-td">
                      <StatusBadge status={disc.review_status} size="sm" />
                    </td>

                    <td className="table-td text-right space-x-1">
                      {disc.workflow_id && (
                        <Link
                          to={`/verification/${disc.workflow_id}`}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium text-[11px] transition"
                          title="Open Verification Workspace"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>Workspace</span>
                        </Link>
                      )}

                      <button
                        onClick={() => setSelectedDiscrepancy(disc)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-blue-600 hover:bg-blue-700 text-white font-semibold text-[11px] transition shadow-sm"
                      >
                        <UserCheck className="w-3.5 h-3.5" />
                        <span>{disc.review_status === 'PENDING' ? 'Decide' : 'Edit'}</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Decision Modal */}
      <ReviewDecisionModal
        isOpen={!!selectedDiscrepancy}
        discrepancy={selectedDiscrepancy}
        onClose={() => setSelectedDiscrepancy(null)}
        onSuccess={() => refetch()}
      />
    </div>
  );
};

