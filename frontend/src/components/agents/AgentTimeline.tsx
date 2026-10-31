import React, { useState } from 'react';
import { AgentTrace } from '../../types';
import {
  Bot,
  CheckCircle2,
  Clock,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Workflow,
  Cpu,
} from 'lucide-react';

interface AgentTimelineProps {
  traces: AgentTrace[];
  workflowStatus?: string;
}

export const AgentTimeline: React.FC<AgentTimelineProps> = ({ traces, workflowStatus }) => {
  const [expandedTraceId, setExpandedTraceId] = useState<string | null>(null);

  const toggleExpand = (id: string) => {
    setExpandedTraceId((curr) => (curr === id ? null : id));
  };

  const agentCatalog = [
    {
      name: 'Supervisor Agent',
      code: 'SUPERVISOR',
      desc: 'Orchestrates the LangGraph state machine, routes work, handles retries, and tracks workflow state.',
    },
    {
      name: 'Document Intelligence Agent',
      code: 'DOCUMENT_INTELLIGENCE',
      desc: 'Extracts digital text page-by-page, classifies document types, structures canonical schemas.',
    },
    {
      name: 'Order Matching Agent',
      code: 'ORDER_MATCHING',
      desc: 'Correlates documents against customer orders, resolves PO references, loads authoritative baseline.',
    },
    {
      name: 'Validation Agent',
      code: 'VALIDATION',
      desc: 'Applies deterministic rules (QTY-001, FIN-001, DEST-001) using Decimal precision and tolerances.',
    },
    {
      name: 'Reconciliation Agent',
      code: 'RECONCILIATION',
      desc: 'Cross-checks multi-document commercial sets (Invoices, Packing Lists, Bills of Lading).',
    },
    {
      name: 'Explanation Agent',
      code: 'EXPLANATION',
      desc: 'Synthesizes traceable evidence, root cause explanations, and human reviewer briefings.',
    },
  ];

  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-subtle">
      <div className="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Workflow className="w-4 h-4 text-blue-600" />
          <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            Multi-Agent Execution Pipeline
          </h4>
        </div>
        <span className="text-[11px] font-medium text-slate-500">
          {traces.length} Agent Steps Recorded
        </span>
      </div>

      {traces.length === 0 ? (
        <div className="p-8 text-center text-xs text-slate-400">
          No agent traces recorded yet for this verification workflow.
        </div>
      ) : (
        <div className="p-5 space-y-4">
          {traces.map((trace, idx) => {
            const isExpanded = expandedTraceId === trace.id;
            const isCompleted = trace.status === 'COMPLETED' || trace.status === 'SUCCESS';
            const isFailed = trace.status === 'FAILED';

            return (
              <div
                key={trace.id || idx}
                className={`border rounded-lg transition-all ${
                  isExpanded ? 'border-blue-300 bg-blue-50/20' : 'border-slate-200 bg-white'
                }`}
              >
                {/* Step Header */}
                <div
                  onClick={() => toggleExpand(trace.id)}
                  className="flex items-center justify-between p-3.5 cursor-pointer hover:bg-slate-50/80 transition rounded-lg"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div
                      className={`p-2 rounded-lg shrink-0 ${
                        isCompleted
                          ? 'bg-emerald-50 text-emerald-600'
                          : isFailed
                          ? 'bg-red-50 text-red-600'
                          : 'bg-blue-50 text-blue-600'
                      }`}
                    >
                      <Bot className="w-4 h-4" />
                    </div>

                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-900 truncate">
                          {trace.agent_name}
                        </span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 font-mono">
                          {trace.step_name}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 mt-0.5 truncate">
                        {trace.input_summary || 'Task step executed in workflow'}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <span
                      className={`inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                        isCompleted
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : isFailed
                          ? 'bg-rose-50 text-rose-700 border border-rose-200'
                          : 'bg-blue-50 text-blue-700 border border-blue-200'
                      }`}
                    >
                      {isCompleted ? (
                        <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                      ) : isFailed ? (
                        <AlertCircle className="w-3 h-3 text-rose-600" />
                      ) : (
                        <Clock className="w-3 h-3 text-blue-600" />
                      )}
                      <span>{trace.status}</span>
                    </span>

                    <span className="text-[10px] text-slate-400">
                      {trace.created_at ? new Date(trace.created_at).toLocaleTimeString() : ''}
                    </span>

                    <button className="text-slate-400 hover:text-slate-600">
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Expanded Details Drawer */}
                {isExpanded && (
                  <div className="px-4 pb-4 pt-1 border-t border-slate-100 space-y-3 text-xs">
                    {trace.input_summary && (
                      <div>
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                          Agent Input Summary
                        </span>
                        <p className="p-2.5 rounded bg-slate-50 border border-slate-200 text-slate-700 font-mono text-[11px] break-words">
                          {trace.input_summary}
                        </p>
                      </div>
                    )}

                    {trace.output_summary && (
                      <div>
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                          Agent Output & Structured Findings
                        </span>
                        <pre className="p-2.5 rounded bg-slate-900 text-emerald-400 font-mono text-[11px] overflow-x-auto whitespace-pre-wrap">
                          {trace.output_summary}
                        </pre>
                      </div>
                    )}

                    {trace.error_message && (
                      <div className="p-2.5 rounded bg-red-50 border border-red-200 text-red-800 text-[11px]">
                        <strong>Agent Error:</strong> {trace.error_message}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

