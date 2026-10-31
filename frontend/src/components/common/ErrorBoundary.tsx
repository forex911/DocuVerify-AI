import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCcw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error in component tree:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="p-8 my-4 rounded-xl bg-red-50 border border-red-200 text-center max-w-xl mx-auto shadow-sm">
          <div className="p-3 bg-red-100 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-3 text-red-600">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-red-950 mb-1">
            {this.props.fallbackTitle || 'Unable to display view'}
          </h3>
          <p className="text-xs text-red-800 mb-4 max-w-md mx-auto">
            {this.state.error?.message || 'An unexpected rendering error occurred in this view.'}
          </p>
          <button
            onClick={() => {
              this.setState({ hasError: false, error: null });
              window.location.reload();
            }}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-red-600 hover:bg-red-700 rounded-lg shadow-sm transition"
          >
            <RefreshCcw className="w-3.5 h-3.5" />
            <span>Reload View</span>
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

