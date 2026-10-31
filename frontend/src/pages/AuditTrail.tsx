import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { auditService } from '../services/audit.service';
import { LoadingState } from '../components/common/LoadingState';
import { EmptyState } from '../components/common/EmptyState';
import {
  ScrollText,
  Search,
  Filter,
  UserCheck,
  ShieldCheck,
  FileText,
  Package,
  AlertTriangle,
  Clock,
} from 'lucide-react';

export const AuditTrail: React.FC = () => {
  const [search, setSearch] = useState('');
  const [entityFilter, setEntityFilter] = useState('');
  const [eventFilter, setEventFilter] = useState('');

  const { data: logs = [], isLoading } = useQuery({
    queryKey: ['audit-logs', entityFilter, eventFilter],
    queryFn: () =>
      auditService.getAuditLogs({
        entity_type: entityFilter || undefined,
        event_type: eventFilter || undefined,
        limit: 200,
      }),
  });

  const filteredLogs = logs.filter((l) => {
    const q = search.toLowerCase();
    return (
      l.event_type.toLowerCase().includes(q) ||
      l.entity_id.toLowerCase().includes(q) ||
      l.actor_id.toLowerCase().includes(q) ||
      JSON.stringify(l.details).toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-5">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">
            Immutable Audit Trail
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Append-only, legally defensible event log of human determinations and verification executions.
          </p>
        </div>

        <div className="p-2.5 rounded-lg bg-emerald-50 border border-emerald-200/80 text-emerald-900 text-xs flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>Non-repudiable log: records human reviewer signatures and rationale</span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="card-subtle p-3.5 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 bg-white">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search audit trail by actor, entity ID, or keyword..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 text-xs rounded-lg border border-slate-200 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400 shrink-0" />
          <select
            value={entityFilter}
            onChange={(e) => setEntityFilter(e.target.value)}
            className="text-xs rounded-lg border border-slate-200 bg-slate-50/50 px-2.5 py-1.5 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600"
          >
            <option value="">All Entities</option>
            <option value="DISCREPANCY">Discrepancy</option>
            <option value="DOCUMENT">Document</option>
            <option value="ORDER">Order</option>
            <option value="VERIFICATION">Verification</option>
          </select>

          <select
            value={eventFilter}
            onChange={(e) => setEventFilter(e.target.value)}
            className="text-xs rounded-lg border border-slate-200 bg-slate-50/50 px-2.5 py-1.5 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600"
          >
            <option value="">All Events</option>
            <option value="DECISION_RECORDED">Human Decision Recorded</option>
            <option value="DOCUMENT_UPLOADED">Document Ingested</option>
            <option value="DOCUMENT_EXTRACTED">Document Extracted</option>
            <option value="ORDER_CREATED">Order Created</option>
            <option value="VERIFICATION_COMPLETED">Verification Completed</option>
          </select>
        </div>
      </div>

      {/* Audit Log Table */}
      {isLoading ? (
        <LoadingState message="Loading immutable audit logs..." />
      ) : filteredLogs.length === 0 ? (
        <EmptyState
          icon={ScrollText}
          title="No audit log entries found"
          description="Actions performed by reviewers and verification agents will appear here chronologically."
        />
      ) : (
        <div className="card-subtle overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/75">
                  <th className="table-th">Event Type</th>
                  <th className="table-th">Entity Reference</th>
                  <th className="table-th">Authorized Actor</th>
                  <th className="table-th">Audit Details & Rationale</th>
                  <th className="table-th">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredLogs.map((log) => {
                  const isDecision = log.event_type.includes('DECISION');
                  return (
                    <tr
                      key={log.id}
                      className={`hover:bg-slate-50/60 transition ${
                        isDecision ? 'bg-emerald-50/20' : ''
                      }`}
                    >
                      <td className="table-td">
                        <span
                          className={`font-mono text-[11px] font-semibold px-2 py-0.5 rounded-full inline-block ${
                            isDecision
                              ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                              : 'bg-slate-100 text-slate-700'
                          }`}
                        >
                          {log.event_type}
                        </span>
                      </td>

                      <td className="table-td font-medium text-slate-800">
                        <span className="font-mono text-slate-500 block text-[10px]">
                          {log.entity_type}
                        </span>
                        <span className="font-mono font-semibold text-slate-900">
                          {log.entity_id}
                        </span>
                      </td>

                      <td className="table-td">
                        <div className="flex items-center gap-1.5">
                          {isDecision ? (
                            <UserCheck className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                          ) : (
                            <Clock className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                          )}
                          <span className="font-semibold text-slate-800">
                            {log.actor_id}
                          </span>
                        </div>
                      </td>

                      <td className="table-td max-w-md">
                        {log.details?.comment ? (
                          <div className="space-y-1">
                            <span className="text-[10px] uppercase font-bold text-slate-500 block">
                              Reviewer Rationale:
                            </span>
                            <p className="p-2 rounded bg-white border border-slate-200 text-slate-900 text-xs italic">
                              "{log.details.comment}"
                            </p>
                            <span className="text-[10px] text-slate-500 block font-mono">
                              Action: {log.details.action}
                            </span>
                          </div>
                        ) : (
                          <pre className="font-mono text-[10px] text-slate-600 p-1.5 rounded bg-slate-50 border border-slate-200/80 overflow-x-auto whitespace-pre-wrap max-h-24">
                            {JSON.stringify(log.details, null, 2)}
                          </pre>
                        )}
                      </td>

                      <td className="table-td text-slate-400 font-mono text-[11px]">
                        {new Date(log.created_at).toLocaleString()}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

