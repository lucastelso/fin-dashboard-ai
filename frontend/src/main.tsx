// frontend/src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';
import './index.css';
import { BrowserRouter } from 'react-router-dom';

// Configuração de cache padrão para um dashboard financeiro
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false, // Evita re-fetch ao mudar de aba no navegador
      retry: 1,                    // Tenta recuperar uma falha apenas 1 vez
      staleTime: 1000 * 60 * 5,     // Considera os dados "frescos" por 5 minutos
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter basename="/dashboard-financeiro">  
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
    </BrowserRouter>
  </React.StrictMode>
);