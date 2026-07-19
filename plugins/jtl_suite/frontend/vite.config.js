import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  root: './', // The root directory for the config is the current folder (frontend/)
  build: {
    outDir: '../dist', // Output compiled assets to a 'dist' folder one level up, or adjust as needed.
    emptyOutDir: true,
  },
});