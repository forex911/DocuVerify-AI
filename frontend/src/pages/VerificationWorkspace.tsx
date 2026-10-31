import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { workflowsService } from '../services/workflows.service';
import { documentsService } from '../services/documents.service';
import { ordersService } from '../services/orders.service';
import { PDFViewer } from '../components/verification/PDFViewer';
import { ComparisonTable } from '../components/verification/ComparisonTable';
import { EvidenceInspector } from '../components/verification/EvidenceInspector';
import { ReviewDecisionModal } from '../components/review/ReviewDecisionModal';
import { StatusBadge } from '../components/common/StatusBadge';
import { SeverityBadge } from '../components/common/SeverityBadge';
import { LoadingState } from '../components/common/LoadingState';
import { Discrepancy, DocumentItem } from '../types';
import {
  FileText,
  ShieldCheck,
  Bot,
  AlertTriangle,
  UserCheck,
  CheckCircle2,
  ArrowLeft,
  RefreshCw,
  ExternalLink,
  Layers,
  HelpCircle,
} from 'lucide-react';

export const VerificationWorkspace: React.FC = () => {
  const { workflowId } = useParams<{ workflowId: string }>();

  const [activeDocId, setActiveDocId] = useState<string | null>(null);
  const [selectedDiscrepancy, setSelectedDiscrepancy] = useState<Discrepancy | null>(null);
  const [reviewModalOpen, setReviewModalOpen] = useState(false);
  const [rightTab, setRightTab] = useState<'comparison' | 'evidence' | 'discrepancies'>('comparison');

  // Fetch Workflow status and findings
  const {
    data: workflow,
    isLoading: isWorkflowLoading,
    refetch: refetchWorkflow,
  } = useQuery({
    queryKey: ['workflow', workflowId],
    queryFn: () => workflowsService.getWorkflow(workflowId!),
    enabled: !!workflowId,
    refetchInterval: (query) => {
      // Poll while running
      const st = query.state.data?.workflow_status;
      return st === 'RUNNING' || st === 'PENDING' ? 3000 : false;
    },
  });

  // Set default active doc
  useEffect(() => {
    if (workflow?.document_ids && workflow.document_ids.length > 0 && !activeDocId) {
      setActiveDocId(workflow.document_ids[0]);
    }
    if (workflow?.discrepancies && workflow.discrepancies.length > 0 && !selectedDiscrepancy) {
      setSelectedDiscrepancy(workflow.discrepancies[0]);
    }
  }, [workflow]);

  // Fetch active document details
  const { data: activeDoc } = useQuery({
    queryKey: ['document', activeDocId],
    queryFn: () => documentsService.getDocument(activeDocId!),
    enabled: !!activeDocId,
  });

  // Fetch approved order
  const orderId = workflow?.order_id || activeDoc?.order_id;
  const { data: order } = useQuery({
    queryKey: ['order', orderId],
    queryFn: () => ordersService.getOrder(orderId!),
    enabled: !!orderId,
  });

  if (isWorkflowLoading) {
    return <LoadingState message="Connecting to Multi-Agent Verification Workspace..." />;
  }

  if (!workflow) {
    return (
      <div className="p-8 text-center text-xs text-red-600 bg-red-50 border border-red-200 rounded-xl">
        Workflow '{workflowId}' was not found.
      </div>
    );
  }

  const discrepancies = workflow.discrepancies || [];
  const investigationReport = workflow.final_investigation_report;

  return (
    <div className="space-y-4">
      {/* Top Workspace Bar */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 pb-3 border-b border-slate-200">
        <div>
          <Link
            to="/verification"
            className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-slate-800 transition mb-0.5"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Verification Queue</span>
          </Link>
          <div className="flex items-center gap-2.5">
            <h1 className="text-lg font-bold tracking-tight text-slate-900">
              Verification Workspace
            </h1>
            <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-700">
              {workflow.workflow_id.slice(0, 16)}...
            </span>
            <StatusBadge status={workflow.workflow_status} size="sm" />
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <Link
            to={`/agents/${workflow.workflow_id}`}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 font-medium transition shadow-subtle"
          >
            <Bot className="w-3.5 h-3.5 text-blue-600" />
            <span>Agent Traces ({workflow.agent_logs_count})</span>
          </Link>

          <button
            onClick={() => refetchWorkflow()}
            className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 transition"
            title="Refresh findings"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Human Oversight Banner */}
      <div className="p-3 bg-blue-50/60 border border-blue-200/80 rounded-xl flex items-center justify-between text-xs">
        <div className="flex items-center gap-2 text-blue-900">
          <ShieldCheck className="w-4 h-4 text-blue-600 shrink-0" />
          <span>
            <strong>Human Reviewer Authority:</strong> AI findings are evidence-backed recommendations. Final determinations require authorized human reviewer confirmation.
          </span>
        </div>
        <span className="text-[10px] font-semibold text-blue-700 uppercase tracking-wider hidden lg:block">
          Non-autonomous Engine
        </span>
      </div>

      {/* 3-Pane Workstation Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* ============================================================== */}
        {/* PANE 1: Context, Documents, & Executive Report (3 Cols)        */}
        {/* ============================================================== */}
        <div className="lg:col-span-3 space-y-4">
          {/* Document Selector Tabs */}
          <div className="card-subtle p-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 mb-2 flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-blue-600" />
              <span>Commercial Documents ({workflow.document_ids.length})</span>
            </h3>
            <div className="space-y-1.5">
              {workflow.document_ids.map((docId) => {
                const isActive = docId === activeDocId;
                return (
                  <button
                    key={docId}
                    onClick={() => setActiveDocId(docId)}
                    className={`w-full text-left p-2.5 rounded-lg text-xs font-medium transition-all ${
                      isActive
                        ? 'bg-blue-600 text-white shadow-sm'
                        : 'bg-slate-50 text-slate-700 hover:bg-slate-100 border border-slate-200/60'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="truncate block font-semibold">
                        {activeDoc && activeDoc.id === docId
                          ? activeDoc.original_filename
                          : `Doc ${docId.slice(0, 8)}...`}
                      </span>
                      {isActive && <span className="text-[10px] uppercase font-bold tracking-wider">Active</span>}
                    </div>
                    <span
                      className={`text-[10px] block mt-0.5 ${
                        isActive ? 'text-blue-100' : 'text-slate-400'
                      }`}
                    >
                      ID: {docId.slice(0, 10)}...
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Approved Order Baseline Summary */}
          <div className="card-subtle p-4 space-y-2 text-xs">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span>Ground Truth Baseline</span>
            </h3>

            {order ? (
              <div className="space-y-2 pt-1">
                <div>
                  <span className="text-[10px] uppercase text-slate-400 block font-bold">Customer</span>
                  <span className="font-semibold text-slate-900">{order.customer_name}</span>
                </div>
                <div>
                  <span className="text-[10px] uppercase text-slate-400 block font-bold">Order ID</span>
                  <Link to={`/orders/${order.id}`} className="font-mono text-blue-600 hover:underline">
                    {order.id}
                  </Link>
                </div>
                <div className="grid grid-cols-2 gap-2 pt-1 border-t border-slate-100">
                  <div>
                    <span className="text-[10px] uppercase text-slate-400 block font-bold">Authorized Total</span>
                    <span className="font-mono font-bold text-slate-900">
                      {order.currency} {Number(order.grand_total).toLocaleString()}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] uppercase text-slate-400 block font-bold">Quantity</span>
                    <span className="font-mono text-slate-800">{order.quantity} PCS</span>
                  </div>
                </div>
                <div className="pt-1">
                  <span className="text-[10px] uppercase text-slate-400 block font-bold">Destination</span>
                  <span className="text-slate-700">{order.destination}</span>
                </div>
              </div>
            ) : (
              <p className="text-slate-400 italic">No approved order matched yet.</p>
            )}
          </div>

          {/* AI Explanation Agent Brief */}
          {investigationReport && (
            <div className="card-subtle p-4 space-y-2 bg-gradient-to-b from-slate-50 to-white text-xs">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-1.5">
                  <Bot className="w-3.5 h-3.5 text-blue-600" />
                  <span>Agent Briefing</span>
                </h3>
                {investigationReport.risk_level && (
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-100 text-amber-800">
                    {investigationReport.risk_level} Risk
                  </span>
                )}
              </div>

              <p className="text-slate-700 leading-relaxed text-[11px]">
                {investigationReport.summary || 'Reconciliation completed.'}
              </p>

              {investigationReport.recommended_action && (
                <div className="p-2.5 rounded bg-blue-50/70 border border-blue-200 text-blue-900 text-[11px] font-medium">
                  <strong>Recommendation:</strong> {investigationReport.recommended_action}
                </div>
              )}
            </div>
          )}
        </div>

        {/* ============================================================== */}
        {/* PANE 2: Digital PDF Stream Viewer (5 Cols)                    */}
        {/* ============================================================== */}
        <div className="lg:col-span-5 h-[760px] sticky top-4">
          <PDFViewer
            documentId={activeDocId || undefined}
            filename={activeDoc?.original_filename || 'Commercial PDF'}
            highlightPage={selectedDiscrepancy?.page_number}
            highlightText={selectedDiscrepancy?.source_text}
          />
        </div>

        {/* ============================================================== */}
        {/* PANE 3: Comparison, Evidence & Reviewer Decisions (4 Cols)     */}
        {/* ============================================================== */}
        <div className="lg:col-span-4 space-y-4">
          {/* Tabs for Right Pane */}
          <div className="flex items-center gap-1 p-1 bg-slate-100 rounded-lg text-xs font-semibold">
            <button
              onClick={() => setRightTab('comparison')}
              className={`flex-1 py-1.5 rounded-md transition ${
                rightTab === 'comparison'
                  ? 'bg-white text-slate-900 shadow-subtle'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Field Comparison
            </button>
            <button
              onClick={() => setRightTab('discrepancies')}
              className={`flex-1 py-1.5 rounded-md transition ${
                rightTab === 'discrepancies'
                  ? 'bg-white text-slate-900 shadow-subtle'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Variances ({discrepancies.length})
            </button>
            <button
              onClick={() => setRightTab('evidence')}
              className={`flex-1 py-1.5 rounded-md transition ${
                rightTab === 'evidence'
                  ? 'bg-white text-slate-900 shadow-subtle'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Evidence Inspector
            </button>
          </div>

          {/* Tab 1: Field Reconciliation Table */}
          {rightTab === 'comparison' && (
            <ComparisonTable
              order={order}
              canonicalDoc={activeDoc?.canonical_document}
              discrepancies={discrepancies}
              selectedDiscrepancyId={selectedDiscrepancy?.id}
              onSelectDiscrepancy={(disc) => {
                setSelectedDiscrepancy(disc);
                setRightTab('evidence');
              }}
            />
          )}

          {/* Tab 2: Discrepancies List */}
          {rightTab === 'discrepancies' && (
            <div className="card-subtle p-3 space-y-2">
              {discrepancies.length === 0 ? (
                <div className="p-6 text-center text-xs text-slate-400">
                  <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                  <p>All extracted fields strictly match approved baseline values!</p>
                </div>
              ) : (
                discrepancies.map((disc) => {
                  const isSelected = selectedDiscrepancy?.id === disc.id;
                  return (
                    <div
                      key={disc.id}
                      onClick={() => {
                        setSelectedDiscrepancy(disc);
                        setRightTab('evidence');
                      }}
                      className={`p-3 rounded-lg border cursor-pointer transition ${
                        isSelected
                          ? 'border-red-400 bg-red-50/60 ring-1 ring-red-400'
                          : 'border-slate-200 hover:border-slate-300 bg-white'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-1.5">
                          <SeverityBadge severity={disc.severity} size="sm" />
                          <span className="font-mono font-bold text-slate-800 text-xs">
                            {disc.rule_id}
                          </span>
                        </div>
                        <StatusBadge status={disc.review_status} size="sm" />
                      </div>
                      <p className="text-xs font-semibold text-slate-900 leading-snug">
                        {disc.description}
                      </p>
                      <div className="flex items-center justify-between text-[11px] text-slate-500 mt-2 pt-1 border-t border-slate-100">
                        <span>Field: {disc.field_name}</span>
                        {disc.page_number && <span>Page {disc.page_number}</span>}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          )}

          {/* Tab 3: Detailed Evidence Inspector */}
          {rightTab === 'evidence' && (
            <div className="min-h-[460px]">
              <EvidenceInspector
                discrepancy={selectedDiscrepancy}
                onOpenReviewModal={() => setReviewModalOpen(true)}
              />
            </div>
          )}
        </div>
      </div>

      {/* Mandatory Human Review Decision Modal */}
      <ReviewDecisionModal
        isOpen={reviewModalOpen}
        discrepancy={selectedDiscrepancy}
        onClose={() => setReviewModalOpen(false)}
        onSuccess={() => {
          refetchWorkflow();
        }}
      />
    </div>
  );
};

