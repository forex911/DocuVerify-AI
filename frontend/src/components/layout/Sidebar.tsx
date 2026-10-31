import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  CheckCircle2,
  Package,
  AlertTriangle,
  Bot,
  ScrollText,
  Settings,
  ChevronLeft,
  ChevronRight,
  Shield,
  UserCheck,
} from 'lucide-react';
import { useUIStore } from '../../store/uiStore';

export const Sidebar: React.FC = () => {
  const { sidebarCollapsed, toggleSidebar, currentReviewer } = useUIStore();
  const location = useLocation();

  const navigation = [
    { name: 'Overview', href: '/', icon: LayoutDashboard },
    { name: 'Documents', href: '/documents', icon: FileText },
    { name: 'Verification Queue', href: '/verification', icon: CheckCircle2 },
    { name: 'Approved Orders', href: '/orders', icon: Package },
    { name: 'Discrepancies', href: '/discrepancies', icon: AlertTriangle },
    { name: 'Agent Activity', href: '/agents', icon: Bot },
    { name: 'Audit Trail', href: '/audit', icon: ScrollText },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  return (
    <aside
      className={`relative flex flex-col border-r border-slate-200 bg-white transition-all duration-300 z-30 select-none ${sidebarCollapsed ? 'w-16' : 'w-64'
        }`}
    >
      {/* Brand Header */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-slate-100">
        <NavLink to="/" className="flex items-center gap-3 overflow-hidden">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-blue-600 text-white shrink-0 shadow-sm">
            <Shield className="w-5 h-5 text-white" />
          </div>
          {!sidebarCollapsed && (
            <div className="flex flex-col">
              <span className="text-sm font-bold tracking-tight text-slate-900 leading-tight">
                DocuVerify                <span className="text-blue-600 font-semibold text-xs ml-0.5">AI</span>
              </span>
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">
                Enterprise Verification
              </span>
            </div>
          )}
        </NavLink>

        <button
          onClick={toggleSidebar}
          className="p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition hidden lg:block"
          title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {sidebarCollapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        {navigation.map((item) => {
          const isActive =
            item.href === '/'
              ? location.pathname === '/'
              : location.pathname.startsWith(item.href);
          const Icon = item.icon;

          return (
            <NavLink
              key={item.name}
              to={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${isActive
                ? 'bg-blue-50 text-blue-700 font-semibold shadow-subtle'
                : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                }`}
              title={sidebarCollapsed ? item.name : undefined}
            >
              <Icon
                className={`w-4 h-4 shrink-0 transition-colors ${isActive ? 'text-blue-600' : 'text-slate-400'
                  }`}
              />
              {!sidebarCollapsed && <span>{item.name}</span>}
            </NavLink>
          );
        })}
      </div>

      {/* Human Reviewer Badge & Policy Notice */}
      {!sidebarCollapsed && (
        <div className="p-3 mx-3 mb-2 rounded-lg bg-slate-50 border border-slate-200/80">
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[10px] font-semibold text-slate-700 uppercase tracking-wider">
              Human-in-the-Loop Active
            </span>
          </div>
          <p className="text-[11px] text-slate-500 leading-relaxed">
            AI extracts and detects anomalies. Final decisions require authorized human review.
          </p>
        </div>
      )}

      {/* Bottom Profile Footer */}
      <div className="p-3 border-t border-slate-100 bg-slate-50/50">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-slate-200 border border-slate-300 flex items-center justify-center shrink-0 text-slate-700 font-semibold text-xs">
            {currentReviewer.name
              .split(' ')
              .map((n) => n[0])
              .join('')}
          </div>
          {!sidebarCollapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-slate-900 truncate">
                {currentReviewer.name}
              </p>
              <div className="flex items-center gap-1">
                <UserCheck className="w-3 h-3 text-emerald-600" />
                <span className="text-[10px] text-slate-500 truncate">
                  {currentReviewer.role}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
};

