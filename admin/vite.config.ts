import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

// When mounted behind a reverse proxy at /admin (prod), the operator sets
// VITE_BASE=/admin/. Locally it defaults to '/' so `npm run dev` stays reachable
// at http://localhost:5174/.
const base = process.env.VITE_BASE || '/';

export default defineConfig({
  base,
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5174,
    strictPort: true,
    watch: {
      usePolling: true,
      interval: 250,
    },
    // Trust the proxy in front (Traefik → external nginx / Cloudflare).
    allowedHosts: true,
  },
});
