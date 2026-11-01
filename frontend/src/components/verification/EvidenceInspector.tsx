import React from 'react';
import { Discrepancy } from '../../types';
import { SeverityBadge } from '../common/SeverityBadge';
import { StatusBadge } from '../common/StatusBadge';
import { ShieldAlert, BookOpen, UserCheck, AlertCircle, FileText } from 'lucide-react';

interface EvidenceInspectorProps {
  discrepancy?: Discrepancy | null;
  onOpenReviewModal?: (discrepancy: Discrepancy) => void;
}

export const EvidenceInspector: React.FC<EvidenceInspectorProps> = ({
  discrepancy,
  onOpenReviewModal,
}) => {
  if (!discrepancy) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 bg-white border border-slate-200 rounded-xl text-center shadow-subtle">
        <BookOpen className="w-10 h-10 text-slate-300 mb-2" />
        <p className="text-xs font-semibold text-slate-700">No Discrepancy Selected</p>
        <p className="text-[11px] text-slate-400 mt-1 max-w-xs">
          Click any flagged row in the reconciliation table or list to inspect traceable audit evidence and agent explanations.
        </p>
      </div>
    );
  }

  const isResolved = discrepancy.review_status && discrepancy.review_status !== 'PENDING';
  const title = discrepancy.explanation || discrepancy.rule_name || discrepancy.description || 'Variance condition';
  const page = discrepancy.source_page ?? discrepancy.page_number;

  return (
    <div className="flex flex-col h-full bg-white border border-slate-200 rounded-xl overflow-hidden shadow-subtle">
      {/* Header */}
      <div className="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-red-600" />
          <span className="font-mono font-bold text-slate-800 text-xs">
            {discrepancy.rule_id}
          </span>
          <SeverityBadge severity={discrepancy.severity} size="sm" />
        </div>
        <StatusBadge status={discrepancy.review_status} size="sm" />
      </div>

      <div className="p-5 flex-1 overflow-y-auto space-y-4 text-xs">
        {/* Description / Explanation */}
        <div>
          <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
            Anomalous Condition
          </label>
          <p className="font-semibold text-slate-900 leading-snug">{title}</p>
        </div>

        {/* Expected vs Actual */}
        <div className="grid grid-cols-2 gap-3 p-3 bg-slate-50 rounded-lg border border-slate-200/80">
          <div>
            <span className="text-[10px] uppercase font-bold text-slate-500 block">
              Expected (Baseline)
            </span>
            <span className="font-mono font-semibold text-slate-800 mt-0.5 block break-all">
              {discrepancy.expected_value || 'None specified'}
            </span>
          </div>
          <div>
            <span className="text-[10px] uppercase font-bold text-red-600 block">
              Actual (Extracted)
            </span>
            <span className="font-mono font-bold text-red-700 mt-0.5 block break-all">
              {discrepancy.actual_value || 'Missing'}
            </span>
          </div>
        </div>

        {/* Traceable Document Provenance */}
        <div>
          <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
            Traceable Source Provenance
          </label>
          <div className="p-3 bg-amber-50/70 border border-amber-200 rounded-lg space-y-1.5">
            <div className="flex items-center justify-between text-[11px] text-amber-900 font-medium">
              <span className="flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5" /> Document: {discrepancy.document_filename || (discrepancy.document_id ? `${discrepancy.document_id.slice(0, 8)}...` : 'Multi-Document')}
              </span>
              {page && (
                <span className="px-1.5 py-0.5 bg-amber-200/80 rounded font-semibold text-[10px]">
                  Page {page}
                </span>
              )}
            </div>
            {discrepancy.source_text ? (
              <p className="font-mono text-[11px] text-amber-950 bg-white/70 p-2 rounded border border-amber-200/60 break-words">
                "{discrepancy.source_text}"
              </p>
            ) : (
              <p className="text-[11px] text-amber-800 italic">
                Field missing from document text.
              </p>
            )}
          </div>
        </div>

        {/* AI Agent Explanation */}
        {discrepancy.explanation && (
          <div>
            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
              Explanation Agent Analysis
            </label>
            <div className="p-3 bg-blue-50/60 border border-blue-200/70 rounded-lg text-blue-950 leading-relaxed text-[11px]">
              {discrepancy.explanation}
            </div>
          </div>
        )}

        {/* Recorded Human Review Decision */}
        {isResolved && (
          <div className="p-3.5 bg-emerald-50/80 border border-emerald-200 rounded-lg space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase font-bold text-emerald-800 flex items-center gap-1">
                <UserCheck className="w-3.5 h-3.5" /> Human Reviewer Determination
              </span>
              <span className="text-[10px] text-emerald-700">
                {discrepancy.reviewed_at ? new Date(discrepancy.reviewed_at).toLocaleDateString() : ''}
              </span>
            </div>
            <p className="text-xs font-semibold text-emerald-950">
              Decision: <StatusBadge status={discrepancy.review_status} size="sm" /> by {discrepancy.reviewer_id || 'Reviewer'}
            </p>
            {discrepancy.review_comment && (
              <p className="text-[11px] text-emerald-900 italic bg-white/80 p-2 rounded border border-emerald-200">
                "{discrepancy.review_comment}"
              </p>
            )}
          </div>
        )}
      </div>

      {/* Review Action Footer */}
      <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
        <span className="text-[10px] text-slate-400">
          Strict Policy: AI cannot resolve or alter findings
        </span>
        <button
          onClick={() => onOpenReviewModal && onOpenReviewModal(discrepancy)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition"
        >
          <UserCheck className="w-3.5 h-3.5" />
          <span>{isResolved ? 'Update Review Decision' : 'Review & Decide'}</span>
        </button>
      </div>
    </div>
  );
};
