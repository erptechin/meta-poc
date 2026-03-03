import React from 'react';
import ReactDOM from 'react-dom/client';
import { Toaster } from 'react-hot-toast';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from './components/AppLayout';
import PlatformIntegration from './components/PlatformIntegration';
import PlatformData from './components/PlatformData';
import IntegrationResult from './components/IntegrationResult';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000,
      gcTime: 5 * 60 * 1000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<Navigate to="/platform-integration" replace />} />
          <Route path="platform-integration" element={<PlatformIntegration />} />
          <Route path="platform-data" element={<PlatformData />} />
        </Route>
        <Route path="/integration-result" element={<IntegrationResult />} />
        <Route path="/platform-integration-success" element={<IntegrationResult />} />
        <Route path="/platform-integration-failure" element={<IntegrationResult />} />
      </Routes>
    </BrowserRouter>
    <Toaster position="top-center" toastOptions={{ duration: 4000 }} />
  </QueryClientProvider>
);