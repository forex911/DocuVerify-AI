import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { dashboardService } from '../services/dashboard.service';
import { MetricCard } from '../components/common/MetricCard';
import { SeverityBadge } from '../components/common/SeverityBadge';
import { StatusBadge } from '../components/common/StatusBadge';
import { LoadingState } from '../components/common/LoadingState';
import {
  FileText,
  AlertTriangle,
  CheckCircle2,
  Package,
  Clock,
  ArrowRight,
  ShieldCheck,
  Bot,
  ScrollText,
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
} from 'recharts';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { data: summary, isLoading, error } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: dashboardService.getSummary,
    refetchInterval: 15000,
  });

  if (isLoading) {
    return <LoadingState message="Loading operational verification metrics..." />;
  }

  if (error || !summary) {
    return (
      <div className="p-8 text-center text-xs text-red-600 bg-red-50 border border-red-200 rounded-xl">
        Failed to load dashboard metrics. Please ensure the backend is running.
      </div>
    );
  }

  // Chart data
  const severityData = [
    { name: 'Critical', value: summary.critical_discrepancies, color: '#dc2626' },
    { name: 'High', value: summary.high_discrepancies, color: '#ea580c' },
    { name: 'Medium', value: summary.medium_discrepancies, color: '#d97706' },
    { name: 'Low', value: summary.low_discrepancies, color: '#2563eb' },
  ];
  const activeSeverityData = severityData.filter((d) => d.value > 0);

  const typeData = Object.entries(summary.document_type_breakdown || {}).map(([type, count]) => ({
    name:
      type === 'packing_list'
        ? 'Packing List'
        : type === 'bill_of_lading'
        ? 'Bill of Lading'
        : type === 'invoice'
        ? 'Invoice'
        : 'Unknown',
    count,
  }));

  return (
    <div className="space-y-6">
      {/* Top Banner Notice */}
      <div className="card-subtle p-4 bg-gradient-to-r from-blue-50/70 via-white to-slate-50 border-blue-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-blue-600 text-white rounded-xl shadow-sm">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900">
              Commercial Document Intelligence & Verification
            </h2>
            <p className="text-xs text-slate-500">
              Deterministic rule validation across Invoices, Packing Lists, Bills of Lading, and Approved Orders.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Link
            to="/verification"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition"
          >
            <span>Verification Queue</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* Operational Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Documents"
          value={summary.total_documents}
          subtitle="Ingested commercial PDFs"
          icon={FileText}
          iconColor="text-blue-600 bg-blue-50"
          onClick={() => navigate('/documents')}
        />
        <MetricCard
          title="Awaiting Human Review"
          value={summary.documents_awaiting_review}
          subtitle="Documents with pending flags"
          icon={Clock}
          iconColor="text-amber-600 bg-amber-50"
          onClick={() => navigate('/verification')}
        />
        <MetricCard
          title="Open Discrepancies"
          value={summary.open_discrepancies}
          subtitle={`${summary.critical_discrepancies} Critical, ${summary.high_discrepancies} High`}
          icon={AlertTriangle}
          iconColor="text-rose-600 bg-rose-50"
          onClick={() => navigate('/discrepancies')}
        />
        <MetricCard
          title="Resolved Discrepancies"
          value={summary.resolved_discrepancies}
          subtitle="Decided with reviewer rationale"
          icon={CheckCircle2}
          iconColor="text-emerald-600 bg-emerald-50"
          onClick={() => navigate('/discrepancies?review_status=APPROVED')}
        />
      </div>

      {/* Visual Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Discrepancy Severity Distribution */}
        <div className="card-subtle p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                Pending Discrepancies by Severity
              </h3>
              <p className="text-[11px] text-slate-500">
                Prioritized queue of anomalies awaiting reviewer decision
              </p>
            </div>
            <Link
              to="/discrepancies"
              className="text-xs font-medium text-blue-600 hover:text-blue-700"
            >
              View all &rarr;
            </Link>
          </div>

          <div className="h-56 flex items-center justify-center">
            {summary.open_discrepancies === 0 ? (
              <div className="text-center text-xs text-slate-400">
                <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2 opacity-80" />
                <p>No open discrepancies pending review!</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={activeSeverityData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={activeSeverityData.length > 1 ? 4 : 0}
                    dataKey="value"
                  >
                    {activeSeverityData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#ffffff',
                      borderColor: '#e2e8f0',
                      borderRadius: '8px',
                      fontSize: '11px',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="grid grid-cols-4 gap-2 pt-3 border-t border-slate-100 text-center text-xs">
            {severityData.map((item) => (
              <div key={item.name} className="p-1.5 rounded-lg bg-slate-50">
                <span className="text-[10px] text-slate-500 block">{item.name}</span>
                <span className="font-bold text-slate-800 text-sm">{item.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Document Ingestion Breakdown */}
        <div className="card-subtle p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                Documents by Commercial Category
              </h3>
              <p className="text-[11px] text-slate-500">
                Ingested Invoices, Packing Lists, and BOLs
              </p>
            </div>
            <Link to="/documents" className="text-xs font-medium text-blue-600 hover:text-blue-700">
              View documents &rarr;
            </Link>
          </div>

          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={typeData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    borderColor: '#e2e8f0',
                    borderRadius: '8px',
                    fontSize: '11px',
                  }}
                />
                <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="flex items-center justify-between pt-3 border-t border-slate-100 text-xs text-slate-500">
            <span>Authoritative Baseline Orders:</span>
            <strong className="text-slate-800">{summary.total_orders} Orders Registered</strong>
          </div>
        </div>
      </div>

      {/* Recent Activity Audit Trail */}
      <div className="card-subtle overflow-hidden">
        <div className="px-5 py-3.5 border-b border-slate-200 bg-slate-50/75 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ScrollText className="w-4 h-4 text-slate-500" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
              Recent Immutable Audit Events
            </h3>
          </div>
          <Link to="/audit" className="text-xs font-medium text-blue-600 hover:text-blue-700">
            View full audit trail &rarr;
          </Link>
        </div>

        {summary.recent_activity.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-400">
            No audit records logged yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/50 border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-4 font-semibold text-slate-600 uppercase text-[10px]">
                    Event Type
                  </th>
                  <th className="py-2.5 px-4 font-semibold text-slate-600 uppercase text-[10px]">
                    Entity
                  </th>
                  <th className="py-2.5 px-4 font-semibold text-slate-600 uppercase text-[10px]">
                    Actor
                  </th>
                  <th className="py-2.5 px-4 font-semibold text-slate-600 uppercase text-[10px]">
                    Details
                  </th>
                  <th className="py-2.5 px-4 font-semibold text-slate-600 uppercase text-[10px]">
                    Timestamp
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {summary.recent_activity.slice(0, 6).map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/60 transition">
                    <td className="py-2.5 px-4 font-semibold text-slate-800">
                      <span className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-700">
                        {log.event_type}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-slate-600">
                      {log.entity_type}: <span className="font-mono">{log.entity_id ? `${log.entity_id.slice(0, 8)}...` : 'N/A'}</span>
                    </td>
                    <td className="py-2.5 px-4 font-medium text-slate-700">
                      {log.actor_id || 'System'}
                    </td>
                    <td className="py-2.5 px-4 text-slate-500 max-w-xs truncate">
                      {log.details ? (typeof log.details === 'string' ? log.details : JSON.stringify(log.details)) : '—'}
                    </td>
                    <td className="py-2.5 px-4 text-slate-400 text-[11px]">
                      {log.created_at ? new Date(log.created_at).toLocaleString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

