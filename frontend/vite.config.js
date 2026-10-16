import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// vite settings for the react app
// when you run npm run dev the api calls go to a backend on localhost port 8000
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { '/api': 'http://localhost:8000' } },
});
