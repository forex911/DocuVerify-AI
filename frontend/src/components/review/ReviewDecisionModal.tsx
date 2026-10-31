import React, { useState } from 'react';
import { Discrepancy, ReviewStatus } from '../../types';
import { Modal } from '../common/Modal';
import { useUIStore } from '../../store/uiStore';
import { discrepanciesService } from '../../services/discrepancies.service';
import { useQueryClient } from '@tanstack/react-query';
import {
  ShieldAlert,
  UserCheck,
  AlertCircle,
  Loader2,
  CheckCircle2,
  XCircle,
  FileQuestion,
  ArrowUpRight,
} from 'lucide-react';

interface ReviewDecisionModalProps {
  isOpen: boolean;
  onClose: () => void;
  discrepancy: Discrepancy | null;
  onSuccess?: () => void;
}

export const ReviewDecisionModal: React.FC<ReviewDecisionModalProps> = ({
  isOpen,
  onClose,
  discrepancy,
  onSuccess,
}) => {
  const queryClient = useQueryClient();
  const { currentReviewer, showNotification } = useUIStore();

  const [action, setAction] = useState<ReviewStatus>('ACCEPT_WITH_JUSTIFICATION');
  const [comment, setComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!discrepancy) return null;

  const title = discrepancy.explanation || discrepancy.rule_name || discrepancy.description || 'Variance Condition';
  const page = discrepancy.source_page ?? discrepancy.page_number;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Strict validation: Non-empty rationale comment required by backend
    if (!comment.trim()) {
      setError('A mandatory review rationale comment is required to record this determination.');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      await discrepanciesService.submitDecision(discrepancy.id, {
        action,
        comment: comment.trim(),
        reviewer_id: currentReviewer.id,
      });

      showNotification(
        `Decision '${action}' successfully recorded by ${currentReviewer.name}.`,
        'success'
      );

      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ['discrepancies'] });
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
      queryClient.invalidateQueries({ queryKey: ['audit-logs'] });

      setComment('');
      onClose();
      if (onSuccess) onSuccess();
    } catch (err: any) {
      setError(err.message || 'Failed to submit review decision');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Record Human Reviewer Determination"
      subtitle={`Enforcing human oversight on ${discrepancy.rule_id}: ${discrepancy.field_name}`}
      maxWidth="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-xs text-red-700">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Discrepancy Context Summary */}
        <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1.5">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-start gap-2">
              <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-slate-900 block">{discrepancy.rule_id} &bull; {discrepancy.field_name}</span>
                <p className="text-slate-700 mt-0.5">{title}</p>
              </div>
            </div>
          </div>
          <div className="flex items-center justify-between pt-1 border-t border-slate-200/60 font-mono text-[11px] text-slate-500">
            <span>Expected: <strong className="text-slate-800">{discrepancy.expected_value || 'None'}</strong></span>
            <span>Actual: <strong className="text-red-700">{discrepancy.actual_value || 'Missing'}</strong></span>
            {page && <span>Page: {page}</span>}
          </div>
        </div>

        {/* Action Decision Selector */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-2">
            Determination Action <span className="text-red-500">*</span>
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <label
              className={`flex items-start gap-2.5 p-3 rounded-lg border cursor-pointer transition ${
                action === 'ACCEPT_WITH_JUSTIFICATION'
                  ? 'bg-blue-50/80 border-blue-400 text-blue-950 ring-1 ring-blue-400'
                  : 'bg-white border-slate-200 hover:bg-slate-50 text-slate-700'
              }`}
            >
              <input
                type="radio"
                name="decision-action"
                value="ACCEPT_WITH_JUSTIFICATION"
                checked={action === 'ACCEPT_WITH_JUSTIFICATION'}
                onChange={() => setAction('ACCEPT_WITH_JUSTIFICATION')}
                className="mt-0.5 text-blue-600 focus:ring-blue-500"
              />
              <div>
                <p className="text-xs font-semibold flex items-center gap-1">
                  <UserCheck className="w-3.5 h-3.5 text-blue-600" /> Accept w/ Justification
                </p>
                <p className="text-[10px] text-slate-500 mt-0.5">
                  Variance confirmed against contract amendment, discount, or authorized exception.
                </p>
              </div>
            </label>

            <label
              className={`flex items-start gap-2.5 p-3 rounded-lg border cursor-pointer transition ${
                action === 'REQUEST_CORRECTION'
                  ? 'bg-amber-50/80 border-amber-400 text-amber-950 ring-1 ring-amber-400'
                  : 'bg-white border-slate-200 hover:bg-slate-50 text-slate-700'
              }`}
            >
              <input
                type="radio"
                name="decision-action"
                value="REQUEST_CORRECTION"
                checked={action === 'REQUEST_CORRECTION'}
                onChange={() => setAction('REQUEST_CORRECTION')}
                className="mt-0.5 text-amber-600 focus:ring-amber-500"
              />
              <div>
                <p className="text-xs font-semibold flex items-center gap-1">
                  <FileQuestion className="w-3.5 h-3.5 text-amber-600" /> Request Correction
                </p>
                <p className="text-[10px] text-slate-500 mt-0.5">
                  Vendor or internal operations must reissue corrected document.
                </p>
              </div>
            </label>

            <label
              className={`flex items-start gap-2.5 p-3 rounded-lg border cursor-pointer transition ${
                action === 'REJECT'
                  ? 'bg-red-50/80 border-red-400 text-red-950 ring-1 ring-red-400'
                  : 'bg-white border-slate-200 hover:bg-slate-50 text-slate-700'
              }`}
            >
              <input
                type="radio"
                name="decision-action"
                value="REJECT"
                checked={action === 'REJECT'}
                onChange={() => setAction('REJECT')}
                className="mt-0.5 text-red-600 focus:ring-red-500"
              />
              <div>
                <p className="text-xs font-semibold flex items-center gap-1">
                  <XCircle className="w-3.5 h-3.5 text-red-600" /> Reject Transaction
                </p>
                <p className="text-[10px] text-slate-500 mt-0.5">
                  Commercial terms strictly non-compliant; document rejected.
                </p>
              </div>
            </label>

            <label
              className={`flex items-start gap-2.5 p-3 rounded-lg border cursor-pointer transition ${
                action === 'ESCALATE'
                  ? 'bg-purple-50/80 border-purple-400 text-purple-950 ring-1 ring-purple-400'
                  : 'bg-white border-slate-200 hover:bg-slate-50 text-slate-700'
              }`}
            >
              <input
                type="radio"
                name="decision-action"
                value="ESCALATE"
                checked={action === 'ESCALATE'}
                onChange={() => setAction('ESCALATE')}
                className="mt-0.5 text-purple-600 focus:ring-purple-500"
              />
              <div>
                <p className="text-xs font-semibold flex items-center gap-1">
                  <ArrowUpRight className="w-3.5 h-3.5 text-purple-600" /> Escalate to Legal/Exec
                </p>
                <p className="text-[10px] text-slate-500 mt-0.5">
                  Requires senior compliance or director level determination.
                </p>
              </div>
            </label>
          </div>
        </div>

        {/* Mandatory Rationale Comment */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Reviewer Justification & Rationale <span className="text-red-500">* (Mandatory)</span>
          </label>
          <textarea
            rows={3}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Explain why this decision is made (e.g. 'Variance confirmed against customer amendment #04 approved on Oct 30', 'Freight miscalculation requires revised invoice')..."
            className="w-full text-xs rounded-lg border border-slate-200 p-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 placeholder:text-slate-400"
          />
          <p className="text-[11px] text-slate-400 mt-1">
            This justification will be permanently written to the immutable audit trail with your digital reviewer signature.
          </p>
        </div>

        {/* Reviewer Digital Sign-Off Info */}
        <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-lg flex items-center justify-between text-xs text-slate-600">
          <div className="flex items-center gap-2">
            <UserCheck className="w-4 h-4 text-emerald-600" />
            <span>
              Authorized Reviewer:{' '}
              <strong className="text-slate-800">{currentReviewer.name}</strong> ({currentReviewer.role})
            </span>
          </div>
          <span className="text-[10px] text-slate-400 font-mono">ID: {currentReviewer.id}</span>
        </div>

        {/* Buttons */}
        <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting || !comment.trim()}
            className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg shadow-sm transition"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Recording Decision...</span>
              </>
            ) : (
              <>
                <UserCheck className="w-4 h-4" />
                <span>Sign & Confirm Determination</span>
              </>
            )}
          </button>
        </div>
      </form>
    </Modal>
  );
};
