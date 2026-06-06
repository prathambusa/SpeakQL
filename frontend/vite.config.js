import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  // Inside Docker Compose the backend service is reachable as "backend".
  // For local dev without Docker, override with VITE_BACKEND_HOST=localhost.
  const backendHost = env.VITE_BACKEND_HOST || 'backend'
  const backendUrl = `http://${backendHost}:8000`

  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        '/query':          { target: backendUrl, changeOrigin: true },
        '/schema':         { target: backendUrl, changeOrigin: true },
        '/refresh-schema': { target: backendUrl, changeOrigin: true },
        '/health':         { target: backendUrl, changeOrigin: true },
        '/databases':      { target: backendUrl, changeOrigin: true },
      },
    },
  }
})
