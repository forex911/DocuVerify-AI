import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { workflowsService } from '../services/workflows.service';
import { StatusBadge } from '../components/common/StatusBadge';
import { LoadingState } from '../components/common/LoadingState';
import { EmptyState } from '../components/common/EmptyState';
import { LaunchVerificationModal } from '../components/common/LaunchVerificationModal';
import {
  CheckCircle2,
  PlayCircle,
  Clock,
  AlertCircle,
  FileText,
  Package,
  Bot,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const VerificationQueue: React.FC = () => {
  const [modalOpen, setModalOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState('');

  const { data: workflows = [], isLoading, refetch } = useQuery({
    queryKey: ['workflows', statusFilter],
    queryFn: () => workflowsService.getWorkflows(statusFilter || undefined),
    refetchInterval: 10000,
  });

  return (
    <div className="space-y-5">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">
            Verification Queue
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Active and completed multi-agent verification workflows awaiting reviewer sign-off.
          </p>
        </div>

        <button
          onClick={() => setModalOpen(true)}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition"
        >
          <PlayCircle className="w-4 h-4" />
          <span>Launch Verification</span>
        </button>
      </div>

      {/* Filter Strip */}
      <div className="card-subtle p-3 bg-white flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs">
          <span className="font-semibold text-slate-600">Filter Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs rounded-lg border border-slate-200 bg-slate-50/50 px-2.5 py-1.5 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600"
          >
            <option value="">All Workflows</option>
            <option value="COMPLETED">Completed</option>
            <option value="RUNNING">Running</option>
            <option value="PENDING">Pending</option>
            <option value="ESCALATED">Escalated</option>
            <option value="FAILED">Failed</option>
          </select>
        </div>

        <span className="text-xs text-slate-400">
          Auto-refreshes every 10s &bull; {workflows.length} jobs
        </span>
      </div>

      {/* Workflows Table */}
      {isLoading ? (
        <LoadingState message="Loading verification queue..." />
      ) : workflows.length === 0 ? (
        <EmptyState
          icon={CheckCircle2}
          title="No verification workflows found"
          description="Start a multi-agent verification run to evaluate commercial documents against approved orders."
          actionText="Start Verification"
          onAction={() => setModalOpen(true)}
        />
      ) : (
        <div className="card-subtle overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/75">
                  <th className="table-th">Workflow ID</th>
                  <th className="table-th">Target / Order Reference</th>
                  <th className="table-th">Multi-Agent Status</th>
                  <th className="table-th">Discrepancy Summary</th>
                  <th className="table-th">Human Review Requirement</th>
                  <th className="table-th">Initiated</th>
                  <th className="table-th text-right">Workspace</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {workflows.map((wf) => {
                  const details = wf.details || {};
                  const discrepancyCount =
                    details.discrepancies?.length ||
                    (details.final_investigation_report?.total_discrepancies ?? 0);
                  const requiresHumanReview =
                    details.requires_human_review !== false;

                  return (
                    <tr key={wf.workflow_id} className="hover:bg-slate-50/60 transition">
                      <td className="table-td">
                        <div className="flex items-center gap-2">
                          <Bot className="w-4 h-4 text-blue-600 shrink-0" />
                          <span className="font-mono font-bold text-slate-900">
                            {wf.workflow_id.slice(0, 16)}...
                          </span>
                        </div>
                      </td>

                      <td className="table-td">
                        <span className="font-mono text-slate-700">
                          {wf.target_id || details.order_id || 'Auto-Matched Order'}
                        </span>
                      </td>

                      <td className="table-td">
                        <StatusBadge status={wf.status} size="sm" />
                      </td>

                      <td className="table-td">
                        {discrepancyCount > 0 ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-700 bg-rose-50 border border-rose-200 px-2 py-0.5 rounded-full">
                            <ShieldAlert className="w-3 h-3 text-rose-600" />
                            {discrepancyCount} {discrepancyCount === 1 ? 'Variance' : 'Variances'}
                          </span>
                        ) : (
                          <span className="text-emerald-700 font-medium text-[11px]">
                            0 Variances Detected
                          </span>
                        )}
                      </td>

                      <td className="table-td">
                        {requiresHumanReview ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-700">
                            <Clock className="w-3.5 h-3.5 text-amber-600" /> Reviewer Sign-Off Needed
                          </span>
                        ) : (
                          <span className="text-slate-400 text-[11px]">Auto-reconciled</span>
                        )}
                      </td>

                      <td className="table-td text-slate-400 text-[11px]">
                        {new Date(wf.created_at).toLocaleString()}
                      </td>

                      <td className="table-td text-right">
                        <Link
                          to={`/verification/${wf.workflow_id}`}
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition shadow-sm"
                        >
                          <span>Open Workspace</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <LaunchVerificationModal
        isOpen={modalOpen}
        onClose={() => {
          setModalOpen(false);
          refetch();
        }}
      />
    </div>
  );
};

