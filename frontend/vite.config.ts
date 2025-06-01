import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import * as path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@components": path.resolve(__dirname, "src/components"),
      "@pages":      path.resolve(__dirname, "src/pages"),
      "@services":   path.resolve(__dirname, "src/services"),
      "@utils":      path.resolve(__dirname, "src/utils"),
      "@types":      path.resolve(__dirname, "src/types"),
      "@styles":     path.resolve(__dirname, "src/styles"),
      "@assets":     path.resolve(__dirname, "src/assets")
    }
  },
  css: {
    modules: {
      localsConvention: "camelCase",
      scopeBehaviour: "local"
    },
    preprocessorOptions: {
      scss: {
        additionalData: '@import "@styles/variables.module.scss";'
      }
    }
  },
  server: {
    port: 3000
  }
});