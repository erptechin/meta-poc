import React from 'react';
import ReactDOM from 'react-dom/client';
import { Toaster } from 'react-hot-toast';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import PlatformIntegration from './components/PlatformIntegration';
import CampaignResult from './components/CampaignResult';

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
        <Route path="/" element={<PlatformIntegration />} />
        <Route path="/campaign-result" element={<CampaignResult />} />
        <Route path="/campaign-success" element={<CampaignResult />} />
        <Route path="/campaign-failure" element={<CampaignResult />} />
      </Routes>
    </BrowserRouter>
    <Toaster position="top-center" toastOptions={{ duration: 4000 }} />
  </QueryClientProvider>
);