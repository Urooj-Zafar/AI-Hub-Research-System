import { createRoot } from 'react-dom/client';
import App from './App';
import { ErrorBoundary } from './components/error-boundary';
import { setBaseUrl } from '@workspace/api-client-react';
import './index.css';

// Use the deployed backend in production.
// In local development, keep the base URL empty so Vite's /api proxy
// forwards requests to http://localhost:8080.
const apiBaseUrl =
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.PROD
    ? 'https://ai-hub-research-system.vercel.app'
    : null);

setBaseUrl(apiBaseUrl);

createRoot(document.getElementById('root')).render(
  <ErrorBoundary>
    <App />
  </ErrorBoundary>,
);