import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    watch: {
      // Required so the file watcher works through Docker bind mounts.
      usePolling: true,
      interval: 250,
    },
    // Trust the proxy in front (Traefik → external nginx / Cloudflare).
    allowedHosts: true,
    // Same-origin proxy in local dev so the browser hits :5173 for both
    // static assets and API calls. Avoids CORS entirely.
    proxy: {
      '/api': {
        target: 'http://api:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://api:8000',
        changeOrigin: true,
      },
    },
  },
});
