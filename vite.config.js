import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  base: process.env.GITHUB_ACTIONS ? '/Icons8-Collector/' : '/',
  plugins: [react()],
  build: {
    target: 'es2022',
    sourcemap: true,
    sourcemapIgnoreList: false
  },
  server: {
    port: 5173,
    strictPort: true
  }
});
