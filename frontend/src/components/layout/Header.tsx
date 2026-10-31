import React, { useEffect, useState } from 'react';
import { useLocation, Link } from 'react-router-dom';
import {
  ChevronRight,
  UploadCloud,
  PlayCircle,
  Activity,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import { apiClient } from '../../services/api';

interface HeaderProps {
  onOpenUploadModal?: () => void;
  onOpenWorkflowModal?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  onOpenUploadModal,
  onOpenWorkflowModal,
}) => {
  const location = useLocation();
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let isMounted = true;
    const checkHealth = async () => {
      try {
        const res = await apiClient.get('/health');
        if (isMounted) setBackendOnline(res.status === 200);
      } catch {
        if (isMounted) setBackendOnline(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const pathnames = location.pathname.split('/').filter((x) => x);

  const getBreadcrumbLabel = (segment: string) => {
    switch (segment) {
      case 'documents':
        return 'Documents';
      case 'orders':
        return 'Approved Orders';
      case 'verification':
        return 'Verification Queue';
      case 'discrepancies':
        return 'Discrepancies';
      case 'agents':
        return 'Agent Activity';
      case 'audit':
        return 'Audit Trail';
      case 'settings':
        return 'Settings';
      default:
        return segment.length > 15 ? `${segment.slice(0, 12)}...` : segment;
    }
  };

  return (
    <header className="h-16 border-b border-slate-200 bg-white px-6 flex items-center justify-between z-20">
      {/* Breadcrumbs */}
      <nav className="flex items-center space-x-2 text-xs font-medium text-slate-500">
        <Link to="/" className="text-slate-600 hover:text-slate-900 transition">
          Home
        </Link>
        {pathnames.map((segment, index) => {
          const routeTo = `/${pathnames.slice(0, index + 1).join('/')}`;
          const isLast = index === pathnames.length - 1;

          return (
            <React.Fragment key={routeTo}>
              <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
              {isLast ? (
                <span className="text-slate-900 font-semibold">{getBreadcrumbLabel(segment)}</span>
              ) : (
                <Link to={routeTo} className="text-slate-600 hover:text-slate-900 transition">
                  {getBreadcrumbLabel(segment)}
                </Link>
              )}
            </React.Fragment>
          );
        })}
      </nav>

      {/* Right side controls */}
      <div className="flex items-center gap-3">
        {/* Backend Connectivity Status Pill */}
        <div
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
            backendOnline === true
              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
              : backendOnline === false
              ? 'bg-rose-50 text-rose-700 border-rose-200'
              : 'bg-slate-50 text-slate-600 border-slate-200'
          }`}
          title="Backend API status at /api/health"
        >
          {backendOnline === true ? (
            <>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span>Engine Online</span>
            </>
          ) : backendOnline === false ? (
            <>
              <AlertCircle className="w-3.5 h-3.5 text-rose-500" />
              <span>Engine Offline</span>
            </>
          ) : (
            <>
              <Activity className="w-3.5 h-3.5 text-slate-400 animate-spin" />
              <span>Connecting</span>
            </>
          )}
        </div>

        {/* Action: Upload PDF */}
        {onOpenUploadModal && (
          <button
            onClick={onOpenUploadModal}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 hover:border-slate-300 transition shadow-subtle"
          >
            <UploadCloud className="w-4 h-4 text-slate-500" />
            <span>Upload Document</span>
          </button>
        )}

        {/* Action: New Multi-Agent Verification */}
        {onOpenWorkflowModal && (
          <button
            onClick={onOpenWorkflowModal}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition"
          >
            <PlayCircle className="w-4 h-4" />
            <span>Verify Documents</span>
          </button>
        )}
      </div>
    </header>
  );
};

