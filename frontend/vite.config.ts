import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 18114,
    proxy: {
      '/api': {
        target: 'http://localhost:19114',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  build: { outDir: 'dist', sourcemap: false },
})
