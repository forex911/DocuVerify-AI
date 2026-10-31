import React, { useState } from 'react';
import { AgentTrace } from '../../types';
import {
  Bot,
  CheckCircle2,
  Clock,
  AlertCircle,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Workflow,
  Cpu,
  Terminal,
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

  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-subtle">
      <div className="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Workflow className="w-4 h-4 text-blue-600" />
          <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            Multi-Agent Execution Pipeline Trace
          </h4>
        </div>
        <span className="text-[11px] font-medium text-slate-500">
          {traces.length} Specialist Actions Recorded
        </span>
      </div>

      {traces.length === 0 ? (
        <div className="p-8 text-center text-xs text-slate-400">
          No agent traces recorded yet for this verification workflow.
        </div>
      ) : (
        <div className="p-5 space-y-3.5">
          {traces.map((trace, idx) => {
            const traceKey = trace.id || `trace-${idx}`;
            const isExpanded = expandedTraceId === traceKey;
            const st = (trace.status || '').toUpperCase();
            const isCompleted = st === 'COMPLETED' || st === 'SUCCESS';
            const isWarning = st === 'DISCREPANCIES_DETECTED';
            const isSkipped = st === 'SKIPPED';
            const isFailed = st === 'FAILED' || st === 'ERROR';

            return (
              <div
                key={traceKey}
                className={`border rounded-lg transition-all ${
                  isExpanded ? 'border-blue-300 bg-blue-50/20 shadow-sm' : 'border-slate-200 bg-white hover:border-slate-300'
                }`}
              >
                {/* Step Header */}
                <div
                  onClick={() => toggleExpand(traceKey)}
                  className="flex items-center justify-between p-3.5 cursor-pointer hover:bg-slate-50/80 transition rounded-lg"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div
                      className={`p-2 rounded-lg shrink-0 ${
                        isCompleted
                          ? 'bg-emerald-50 text-emerald-600'
                          : isWarning
                          ? 'bg-amber-50 text-amber-600'
                          : isFailed
                          ? 'bg-red-50 text-red-600'
                          : isSkipped
                          ? 'bg-slate-100 text-slate-500'
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
                          {trace.step_name || trace.action || 'Agent Step'}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 mt-0.5 truncate">
                        {trace.input_summary || trace.action || 'Task step executed in workflow'}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <span
                      className={`inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                        isCompleted
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : isWarning
                          ? 'bg-amber-50 text-amber-800 border border-amber-200'
                          : isFailed
                          ? 'bg-rose-50 text-rose-700 border border-rose-200'
                          : isSkipped
                          ? 'bg-slate-100 text-slate-600 border border-slate-200'
                          : 'bg-blue-50 text-blue-700 border border-blue-200'
                      }`}
                    >
                      {isCompleted ? (
                        <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                      ) : isWarning ? (
                        <AlertTriangle className="w-3 h-3 text-amber-600" />
                      ) : isFailed ? (
                        <AlertCircle className="w-3 h-3 text-rose-600" />
                      ) : isSkipped ? (
                        <Clock className="w-3 h-3 text-slate-400" />
                      ) : (
                        <Clock className="w-3 h-3 text-blue-600" />
                      )}
                      <span>{trace.status || 'SUCCESS'}</span>
                    </span>

                    <span className="text-[10px] text-slate-400 font-mono">
                      {trace.created_at || trace.timestamp
                        ? new Date(trace.created_at || trace.timestamp || '').toLocaleTimeString()
                        : ''}
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
                  <div className="px-4 pb-4 pt-2 border-t border-slate-100 space-y-3 text-xs">
                    {trace.input_summary && (
                      <div>
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                          Task Action Summary
                        </span>
                        <p className="p-2.5 rounded bg-slate-50 border border-slate-200 text-slate-700 font-mono text-[11px] break-words">
                          {trace.input_summary}
                        </p>
                      </div>
                    )}

                    <div>
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                        Agent Payload Output & Details
                      </span>
                      <pre className="p-3 rounded-lg bg-slate-900 text-slate-200 font-mono text-[11px] overflow-x-auto max-h-60 leading-relaxed">
                        {typeof trace.details === 'object'
                          ? JSON.stringify(trace.details, null, 2)
                          : trace.output_summary || JSON.stringify(trace, null, 2)}
                      </pre>
                    </div>
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
