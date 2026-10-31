import React from 'react';
import { AgentTrace } from '../../types';
import {
  Bot,
  Layers,
  FileCheck2,
  ShieldCheck,
  GitCompare,
  Sparkles,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Loader2,
  ChevronRight,
  Info,
} from 'lucide-react';

interface AgentProgressPipelineProps {
  traces: AgentTrace[];
  workflowStatus?: string;
  discrepanciesCount?: number;
  onSelectAgent?: (agentName: string) => void;
}

interface AgentStage {
  id: string;
  name: string;
  role: string;
  agentClass: string;
  icon: React.FC<{ className?: string }>;
}

type StageStatus = 'completed' | 'warning' | 'running' | 'pending' | 'skipped' | 'failed';

interface StageState {
  stage: AgentStage;
  state: StageStatus;
  label: string;
  latestTrace?: AgentTrace;
}

const AGENT_STAGES: AgentStage[] = [
  {
    id: 'supervisor',
    name: 'Supervisor',
    role: 'State & Orchestration',
    agentClass: 'SupervisorAgent',
    icon: Bot,
  },
  {
    id: 'document_intel',
    name: 'Document Intel',
    role: 'Extraction & Schema',
    agentClass: 'DocumentIntelligenceAgent',
    icon: Layers,
  },
  {
    id: 'order_matching',
    name: 'Order Match',
    role: 'Baseline PO Resolution',
    agentClass: 'OrderMatchingAgent',
    icon: FileCheck2,
  },
  {
    id: 'validation',
    name: 'Validation',
    role: 'Deterministic Rules',
    agentClass: 'ValidationAgent',
    icon: ShieldCheck,
  },
  {
    id: 'reconciliation',
    name: 'Reconciliation',
    role: 'Cross-Doc Alignment',
    agentClass: 'ReconciliationAgent',
    icon: GitCompare,
  },
  {
    id: 'explanation',
    name: 'Explanation',
    role: 'Evidence Briefing',
    agentClass: 'ExplanationAgent',
    icon: Sparkles,
  },
];

export const AgentProgressPipeline: React.FC<AgentProgressPipelineProps> = ({
  traces,
  workflowStatus = 'PENDING',
  discrepanciesCount = 0,
  onSelectAgent,
}) => {
  const isWorkflowActive =
    workflowStatus === 'RUNNING' || workflowStatus === 'PROCESSING' || workflowStatus === 'PENDING';
  const isWorkflowCompleted =
    workflowStatus === 'COMPLETED' || workflowStatus === 'REVIEW_REQUIRED';

  // Compute status for each of the 6 stages
  let lastCompletedIndex = -1;

  const stageStates: StageState[] = AGENT_STAGES.map((stage, idx): StageState => {
    // Find matching trace
    const matchingTraces = traces.filter(
      (t) =>
        t.agent_name?.toLowerCase().includes(stage.id.toLowerCase()) ||
        t.agent_name === stage.agentClass ||
        (stage.id === 'document_intel' && t.agent_name?.toLowerCase().includes('document')) ||
        (stage.id === 'order_matching' && t.agent_name?.toLowerCase().includes('order'))
    );

    const latestTrace = matchingTraces[matchingTraces.length - 1];

    let state: StageStatus = 'pending';
    let label = 'Queued';

    if (latestTrace) {
      lastCompletedIndex = idx;
      const st = latestTrace.status?.toUpperCase();
      if (st === 'SUCCESS' || st === 'COMPLETED') {
        state = 'completed';
        label = latestTrace.step_name || 'Completed';
      } else if (st === 'DISCREPANCIES_DETECTED' || (stage.id === 'validation' && discrepanciesCount > 0)) {
        state = 'warning';
        label = `${discrepanciesCount} Variances Detected`;
      } else if (st === 'SKIPPED') {
        state = 'skipped';
        label = 'Skipped (Single Doc)';
      } else if (st === 'FAILED' || st === 'ERROR') {
        state = 'failed';
        label = 'Failed';
      } else {
        state = 'completed';
        label = latestTrace.step_name || 'Done';
      }
    } else if (isWorkflowCompleted) {
      // Workflow finished: if no trace for this stage, it either completed or was synchronized
      state = 'completed';
      label = 'Executed';
    }

    return {
      stage,
      state,
      label,
      latestTrace,
    };
  });

  // If workflow is actively running, set the current active stage to running
  if (isWorkflowActive) {
    const activeIdx = Math.min(lastCompletedIndex + 1, AGENT_STAGES.length - 1);
    if (activeIdx >= 0 && stageStates[activeIdx].state === 'pending') {
      stageStates[activeIdx].state = 'running';
      stageStates[activeIdx].label = 'Executing Agent...';
    }
  }

  const completedCount = stageStates.filter(
    (s) => s.state === 'completed' || s.state === 'warning' || s.state === 'skipped'
  ).length;
  const progressPercent = Math.round((completedCount / AGENT_STAGES.length) * 100);

  return (
    <div className="card-subtle p-4 bg-white shadow-subtle border border-slate-200/80 rounded-xl space-y-3.5">
      {/* Top Header & Live Progress */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-2.5">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-blue-50 text-blue-600">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <span>Multi-Agent Verification Pipeline</span>
              {isWorkflowActive && (
                <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full border border-blue-200/60 animate-pulse">
                  <Loader2 className="w-2.5 h-2.5 animate-spin" />
                  Live Agents Active
                </span>
              )}
            </h3>
            <p className="text-[11px] text-slate-500">
              Coordinated LangGraph workflow across 6 specialized AI verification agents.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-[11px] font-semibold text-slate-700">
              {completedCount} of {AGENT_STAGES.length} Agents Completed
            </span>
            <span className="text-[10px] text-slate-400 block font-mono">
              {progressPercent}% Complete
            </span>
          </div>
          <div className="w-20 bg-slate-100 rounded-full h-2 overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${
                discrepanciesCount > 0 ? 'bg-amber-500' : 'bg-emerald-500'
              }`}
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* 6-Stage Stepper Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
        {stageStates.map(({ stage, state, label, latestTrace }, idx) => {
          const Icon = stage.icon;

          let badgeColor = 'bg-slate-50 border-slate-200 text-slate-600';
          let iconColor = 'text-slate-400';

          if (state === 'completed') {
            badgeColor = 'bg-emerald-50/70 border-emerald-200 text-emerald-900';
            iconColor = 'text-emerald-600';
          } else if (state === 'warning') {
            badgeColor = 'bg-amber-50/80 border-amber-300 text-amber-900 ring-1 ring-amber-300/50';
            iconColor = 'text-amber-600';
          } else if (state === 'running') {
            badgeColor = 'bg-blue-50 border-blue-300 text-blue-900 ring-2 ring-blue-500/20';
            iconColor = 'text-blue-600';
          } else if (state === 'skipped') {
            badgeColor = 'bg-slate-50 border-slate-200 text-slate-500';
            iconColor = 'text-slate-400';
          } else if (state === 'failed') {
            badgeColor = 'bg-rose-50 border-rose-200 text-rose-900';
            iconColor = 'text-rose-600';
          }

          return (
            <div
              key={stage.id}
              onClick={() => onSelectAgent && onSelectAgent(stage.name)}
              className={`p-2.5 rounded-lg border transition-all text-left flex flex-col justify-between ${badgeColor} ${
                onSelectAgent ? 'cursor-pointer hover:shadow-subtle' : ''
              }`}
            >
              <div>
                <div className="flex items-center justify-between gap-1 mb-1.5">
                  <span className="text-[10px] font-mono font-bold text-slate-400">
                    0{idx + 1}
                  </span>
                  <div>
                    {state === 'completed' && (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    )}
                    {state === 'warning' && (
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                    )}
                    {state === 'running' && (
                      <Loader2 className="w-3.5 h-3.5 text-blue-600 animate-spin" />
                    )}
                    {state === 'skipped' && (
                      <span className="text-[9px] px-1 py-0.2 rounded bg-slate-200/80 text-slate-600 font-mono">
                        SKIP
                      </span>
                    )}
                    {state === 'pending' && (
                      <Clock className="w-3.5 h-3.5 text-slate-300" />
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-1.5">
                  <Icon className={`w-3.5 h-3.5 shrink-0 ${iconColor}`} />
                  <span className="text-xs font-bold truncate tracking-tight">{stage.name}</span>
                </div>

                <span className="text-[10px] text-slate-500 block truncate mt-0.5">
                  {stage.role}
                </span>
              </div>

              <div className="mt-2 pt-1.5 border-t border-slate-200/50">
                <span
                  className="text-[10px] font-medium truncate block leading-tight"
                  title={label}
                >
                  {label}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
