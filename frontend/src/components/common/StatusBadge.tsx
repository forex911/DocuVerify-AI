import React from 'react';
import { ReviewStatus, DocumentStatus, WorkflowStatus } from '../../types';
import { CheckCircle2, Clock, AlertCircle, XCircle, CheckSquare, ShieldCheck } from 'lucide-react';

interface StatusBadgeProps {
  status: ReviewStatus | DocumentStatus | WorkflowStatus | string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const s = (status || '').toUpperCase();

  const getStyle = () => {
    switch (s) {
      case 'ACCEPT_WITH_JUSTIFICATION':
      case 'APPROVED':
      case 'VERIFIED':
      case 'COMPLETED':
        return {
          bg: 'bg-emerald-50 text-emerald-700 border-emerald-200/80',
          icon: CheckCircle2,
          label:
            s === 'COMPLETED'
              ? 'Completed'
              : s === 'VERIFIED'
              ? 'Verified'
              : s === 'ACCEPT_WITH_JUSTIFICATION'
              ? 'Accepted w/ Justification'
              : 'Approved',
        };
      case 'REJECT':
      case 'REJECTED':
      case 'FAILED':
        return {
          bg: 'bg-rose-50 text-rose-700 border-rose-200/80',
          icon: XCircle,
          label: s === 'FAILED' ? 'Failed' : 'Rejected',
        };
      case 'REQUEST_CORRECTION':
      case 'ACCEPTED_WITH_EXCEPTION':
        return {
          bg: 'bg-indigo-50 text-indigo-700 border-indigo-200/80',
          icon: ShieldCheck,
          label: s === 'REQUEST_CORRECTION' ? 'Correction Requested' : 'Accepted w/ Exception',
        };
      case 'ESCALATE':
      case 'ESCALATED':
      case 'REVIEW_REQUIRED':
        return {
          bg: 'bg-amber-50 text-amber-700 border-amber-200/80',
          icon: AlertCircle,
          label: s.includes('ESCALAT') ? 'Escalated' : 'Review Required',
        };
      case 'EXTRACTED':
        return {
          bg: 'bg-sky-50 text-sky-700 border-sky-200/80',
          icon: CheckSquare,
          label: 'Extracted',
        };
      case 'KEEP_PENDING':
      case 'PENDING':
      case 'RUNNING':
        return {
          bg: 'bg-blue-50 text-blue-700 border-blue-200/80',
          icon: Clock,
          label: s === 'RUNNING' ? 'Running' : s === 'KEEP_PENDING' ? 'Kept Pending' : 'Pending',
        };
      default:
        return {
          bg: 'bg-slate-100 text-slate-700 border-slate-200',
          icon: Clock,
          label: s || 'Unknown',
        };
    }
  };

  const style = getStyle();
  const Icon = style.icon;
  const sizeClasses = size === 'sm' ? 'px-1.5 py-0.5 text-xs' : 'px-2.5 py-1 text-xs';

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium rounded-md border ${style.bg} ${sizeClasses}`}
    >
      <Icon className={size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5'} />
      <span>{style.label}</span>
    </span>
  );
};
