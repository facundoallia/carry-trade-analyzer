import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    // En desarrollo, proxy /api al backend FastAPI local (puerto 8000)
    // En producción en Vercel, /api/* es manejado por las serverless functions
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
