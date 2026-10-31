import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { workflowsService } from '../services/workflows.service';
import { AgentTimeline } from '../components/agents/AgentTimeline';
import { LoadingState } from '../components/common/LoadingState';
import { StatusBadge } from '../components/common/StatusBadge';
import {
  Bot,
  Cpu,
  Layers,
  ArrowRight,
  Workflow,
  CheckCircle2,
  RefreshCw,
  GitBranch,
} from 'lucide-react';

export const AgentActivity: React.FC = () => {
  const { workflowId: paramWorkflowId } = useParams<{ workflowId?: string }>();
  const navigate = useNavigate();

  // List all workflows to populate selector
  const { data: workflows = [], isLoading: isWorkflowsLoading } = useQuery({
    queryKey: ['workflows'],
    queryFn: () => workflowsService.getWorkflows(),
  });

  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string>('');

  useEffect(() => {
    if (paramWorkflowId) {
      setSelectedWorkflowId(paramWorkflowId);
    } else if (workflows.length > 0 && !selectedWorkflowId) {
      setSelectedWorkflowId(workflows[0].workflow_id);
    }
  }, [paramWorkflowId, workflows]);

  // Fetch agent execution traces for the selected workflow
  const {
    data: traceData,
    isLoading: isTracesLoading,
    refetch,
  } = useQuery({
    queryKey: ['workflow-agents', selectedWorkflowId],
    queryFn: () => workflowsService.getWorkflowAgents(selectedWorkflowId),
    enabled: !!selectedWorkflowId,
    refetchInterval: 5000,
  });

  const traces = traceData?.agent_traces || [];

  const handleSelectWorkflow = (id: string) => {
    setSelectedWorkflowId(id);
    navigate(`/agents/${id}`);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">
            Multi-Agent Execution & State Traces
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Observability into the LangGraph state machine, specialist agent calls, and deterministic validations.
          </p>
        </div>

        <button
          onClick={() => refetch()}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 shadow-subtle transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Traces</span>
        </button>
      </div>

      {/* Workflow Selector & Status Strip */}
      <div className="card-subtle p-4 bg-white flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3 w-full md:w-auto">
          <Workflow className="w-5 h-5 text-blue-600 shrink-0" />
          <div className="flex-1 md:flex-initial">
            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
              Select Verification Workflow
            </label>
            <select
              value={selectedWorkflowId}
              onChange={(e) => handleSelectWorkflow(e.target.value)}
              className="text-xs font-mono rounded-lg border border-slate-200 bg-slate-50/50 px-3 py-1.5 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 min-w-[280px]"
            >
              {workflows.map((wf) => (
                <option key={wf.workflow_id} value={wf.workflow_id}>
                  {wf.workflow_id.slice(0, 18)}... &mdash; {wf.status} ({new Date(wf.created_at).toLocaleTimeString()})
                </option>
              ))}
            </select>
          </div>
        </div>

        {selectedWorkflowId && (
          <div className="flex items-center gap-3 text-xs">
            <span className="text-slate-500">
              Steps Executed: <strong className="text-slate-800">{traces.length}</strong>
            </span>
            <button
              onClick={() => navigate(`/verification/${selectedWorkflowId}`)}
              className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-700 font-semibold"
            >
              <span>Open in Verification Workspace</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>

      {/* Agent Architecture Overview Strip */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-2 text-xs">
        {[
          { name: 'Supervisor', role: 'State Orchestration' },
          { name: 'Document Intel', role: 'PDF Text & Classification' },
          { name: 'Order Matching', role: 'Baseline PO Resolution' },
          { name: 'Validation', role: 'Deterministic Rules' },
          { name: 'Reconciliation', role: 'Cross-Doc Reconciliation' },
          { name: 'Explanation', role: 'Audit Evidence Briefing' },
        ].map((ag) => (
          <div key={ag.name} className="card-subtle p-2.5 bg-slate-50/50">
            <div className="flex items-center gap-1.5 text-blue-700 font-bold text-[11px]">
              <Bot className="w-3.5 h-3.5" />
              <span>{ag.name}</span>
            </div>
            <p className="text-[10px] text-slate-500 mt-0.5">{ag.role}</p>
          </div>
        ))}
      </div>

      {/* Main Timeline View */}
      {isTracesLoading ? (
        <LoadingState message="Retrieving multi-agent execution steps..." />
      ) : (
        <AgentTimeline traces={traces} />
      )}
    </div>
  );
};

