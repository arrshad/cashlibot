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
  },
});
