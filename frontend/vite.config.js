import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/health': 'http://127.0.0.1:8000',
      '/creators': 'http://127.0.0.1:8000',
      '/analytics': 'http://127.0.0.1:8000',
      '/content': 'http://127.0.0.1:8000',
      '/approvals': 'http://127.0.0.1:8000',
      '/trends': 'http://127.0.0.1:8000',
      '/experiments': 'http://127.0.0.1:8000',
      '/advisory': 'http://127.0.0.1:8000',
      '/reports': 'http://127.0.0.1:8000',
      '/creator-plan': 'http://127.0.0.1:8000',
      '/onboarding': 'http://127.0.0.1:8000',
      '/data': 'http://127.0.0.1:8000',
    },
  },
});
