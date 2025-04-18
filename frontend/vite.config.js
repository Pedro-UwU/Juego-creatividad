import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import yaml from '@rollup/plugin-yaml';

export default defineConfig({
  plugins: [
    svelte(),
    yaml() // Add YAML plugin
  ],
  build: {
    outDir: 'dist',
  },
  server: {
    proxy: {
      // Proxy API requests during development
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
});
