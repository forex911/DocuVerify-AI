import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingStateProps {
  message?: string;
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Loading document verification data...',
  className = 'py-16',
}) => {
  return (
    <div className={`flex flex-col items-center justify-center text-center ${className}`}>
      <Loader2 className="w-7 h-7 text-blue-600 animate-spin mb-3" />
      <p className="text-xs font-medium text-slate-500">{message}</p>
    </div>
  );
};

