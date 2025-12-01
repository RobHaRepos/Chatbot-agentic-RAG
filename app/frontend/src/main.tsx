import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { QUERY_STALE_TIME, QUERY_CACHE_TIME } from '@/lib/constants';
import App from './App.tsx';
import './index.css';

/**
 * FIXED: Proper React Query configuration using constants
 * - staleTime: How long data is considered fresh
 * - gcTime: How long unused data stays in cache (React Query v5)
 * - retry: 2 with exponential backoff (industry standard)
 */
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: QUERY_STALE_TIME,
      gcTime: QUERY_CACHE_TIME,
      retry: 2, // Retry twice on failure with exponential backoff
      refetchOnWindowFocus: false, // Prevent excessive refetching
    },
  },
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>,
);
