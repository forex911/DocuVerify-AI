import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { UploadDocumentModal } from '../common/UploadDocumentModal';
import { LaunchVerificationModal } from '../common/LaunchVerificationModal';
import { useUIStore } from '../../store/uiStore';
import { CheckCircle, AlertTriangle, Info, X } from 'lucide-react';

export const AppShell: React.FC = () => {
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [workflowModalOpen, setWorkflowModalOpen] = useState(false);
  const { notification, clearNotification } = useUIStore();

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#f8fafc] text-slate-800">
      {/* Persistent Left Sidebar */}
      <Sidebar />

      {/* Main Layout Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <Header
          onOpenUploadModal={() => setUploadModalOpen(true)}
          onOpenWorkflowModal={() => setWorkflowModalOpen(true)}
        />

        {/* Global Toast Notification */}
        {notification && (
          <div className="fixed bottom-6 right-6 z-50 animate-in fade-in slide-in-from-bottom-3 duration-200">
            <div
              className={`flex items-center gap-3 px-4 py-3 rounded-xl border shadow-elevated text-xs font-medium max-w-md ${
                notification.type === 'success'
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                  : notification.type === 'error'
                  ? 'bg-red-50 border-red-200 text-red-800'
                  : notification.type === 'warning'
                  ? 'bg-amber-50 border-amber-200 text-amber-800'
                  : 'bg-blue-50 border-blue-200 text-blue-800'
              }`}
            >
              {notification.type === 'success' && (
                <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
              )}
              {notification.type === 'error' && (
                <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
              )}
              {notification.type === 'warning' && (
                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
              )}
              {notification.type === 'info' && (
                <Info className="w-4 h-4 text-blue-600 shrink-0" />
              )}
              <span className="flex-1">{notification.message}</span>
              <button
                onClick={clearNotification}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}

        {/* Dynamic Route View */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <Outlet />
        </main>
      </div>

      {/* Global Modals */}
      <UploadDocumentModal
        isOpen={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
      />

      <LaunchVerificationModal
        isOpen={workflowModalOpen}
        onClose={() => setWorkflowModalOpen(false)}
      />
    </div>
  );
};

