import React from 'react';
import { SeverityLevel } from '../../types';
import { AlertCircle, AlertTriangle, Info } from 'lucide-react';

interface SeverityBadgeProps {
  severity: SeverityLevel | string;
  size?: 'sm' | 'md';
  showIcon?: boolean;
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({
  severity,
  size = 'md',
  showIcon = true,
}) => {
  const sev = (severity || 'LOW').toUpperCase();

  const config = {
    CRITICAL: {
      bg: 'bg-red-50 text-red-700 border-red-200/80',
      dot: 'bg-red-600',
      icon: AlertCircle,
      label: 'Critical',
    },
    HIGH: {
      bg: 'bg-orange-50 text-orange-700 border-orange-200/80',
      dot: 'bg-orange-500',
      icon: AlertTriangle,
      label: 'High',
    },
    MEDIUM: {
      bg: 'bg-amber-50 text-amber-700 border-amber-200/80',
      dot: 'bg-amber-500',
      icon: AlertTriangle,
      label: 'Medium',
    },
    LOW: {
      bg: 'bg-blue-50 text-blue-700 border-blue-200/80',
      dot: 'bg-blue-500',
      icon: Info,
      label: 'Low',
    },
  }[sev] || {
    bg: 'bg-slate-100 text-slate-700 border-slate-200',
    dot: 'bg-slate-400',
    icon: Info,
    label: sev,
  };

  const IconComponent = config.icon;
  const sizeClasses = size === 'sm' ? 'px-1.5 py-0.5 text-xs' : 'px-2.5 py-1 text-xs';

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium rounded-md border ${config.bg} ${sizeClasses}`}
    >
      {showIcon && <IconComponent className={size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5'} />}
      <span>{config.label}</span>
    </span>
  );
};

