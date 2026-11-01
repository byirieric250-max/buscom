import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
const backend='http://127.0.0.1:8000';
export default defineConfig({ plugins: [react(), tailwindcss()], server: { proxy: { '/api': backend, '/admin': {target:backend,changeOrigin:true}, '/static': {target:backend,changeOrigin:true}, '/media': {target:backend,changeOrigin:true} } } });
