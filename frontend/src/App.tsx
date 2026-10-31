import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppShell } from './components/layout/AppShell';

import { Dashboard } from './pages/Dashboard';
import { Documents } from './pages/Documents';
import { DocumentDetail } from './pages/DocumentDetail';
import { Orders } from './pages/Orders';
import { OrderDetail } from './pages/OrderDetail';
import { VerificationQueue } from './pages/VerificationQueue';
import { VerificationWorkspace } from './pages/VerificationWorkspace';
import { Discrepancies } from './pages/Discrepancies';
import { AgentActivity } from './pages/AgentActivity';
import { AuditTrail } from './pages/AuditTrail';
import { Settings } from './pages/Settings';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5000,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppShell />}>
            <Route index element={<Dashboard />} />
            <Route path="documents" element={<Documents />} />
            <Route path="documents/:id" element={<DocumentDetail />} />
            <Route path="orders" element={<Orders />} />
            <Route path="orders/:id" element={<OrderDetail />} />
            <Route path="verification" element={<VerificationQueue />} />
            <Route path="verification/:workflowId" element={<VerificationWorkspace />} />
            <Route path="discrepancies" element={<Discrepancies />} />
            <Route path="agents" element={<AgentActivity />} />
            <Route path="agents/:workflowId" element={<AgentActivity />} />
            <Route path="audit" element={<AuditTrail />} />
            <Route path="settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;

