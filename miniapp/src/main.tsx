import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from '@/App';
import { installSpotlight } from '@/util/spotlight';
import '@/theme/globals.css';

installSpotlight();

const root = document.getElementById('root');
if (!root) throw new Error('No #root element in index.html');

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
