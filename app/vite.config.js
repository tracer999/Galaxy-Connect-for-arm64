import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Electron 이 file:// 로 dist/index.html 을 열기 때문에 상대 경로로 빌드한다
export default defineConfig({
  plugins: [react()],
  base: './',
  build: { outDir: 'dist', emptyOutDir: true },
});
