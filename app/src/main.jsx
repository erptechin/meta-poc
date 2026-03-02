import React from 'react';
import ReactDOM from 'react-dom/client';
import { Toaster } from 'react-hot-toast';
import PlatformIntegration from './components/PlatformIntegration';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <QueryClientProvider client={queryClient}>
    <PlatformIntegration />
    <Toaster position="top-center" toastOptions={{ duration: 4000 }} />
  </QueryClientProvider>
);