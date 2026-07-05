import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: true,
    // allow access through the cloudflared quick tunnel (Telegram Mini App)
    allowedHosts: ['.trycloudflare.com'],
    // same-origin API: the app calls /api/*, vite forwards to the backend.
    // Inside the Telegram iframe cross-origin fetches are blocked, so the
    // mini-app must talk to its own origin.
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ''),
      },
    },
  },
})
