import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const apiUrl =
    process.env.VITE_API_URL ||
    env.VITE_API_URL ||
    env.VITE_API_BASE_URL ||
    'https://pillsync-care.onrender.com';

  return {
    // Serve static HTML pages from public/ as the web root
    root: '.',
    publicDir: 'public',
    define: {
      'import.meta.env.VITE_API_URL': JSON.stringify(apiUrl),
      'import.meta.env.VITE_API_BASE_URL': JSON.stringify(apiUrl),
    },
    server: {
      port: 5173,
      // Talk to the backend dev server without CORS in development.
      proxy: {
        '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      },
    },
    plugins: [
      {
        name: 'generate-config-js',
        configureServer(server) {
          server.middlewares.use('/config.js', (_req, res) => {
            const devUrl = process.env.VITE_API_URL || env.VITE_API_URL || 'http://localhost:8000';
            const devBase = devUrl.replace(/\/+$/, '') + (devUrl.includes('/api/v1') ? '' : '/api/v1');
            res.setHeader('Content-Type', 'application/javascript');
            res.end(`window.VITE_API_URL = ${JSON.stringify(devUrl)};\nwindow.API_BASE_URL = ${JSON.stringify(devBase)};\n`);
          });
        },
        generateBundle() {
          const prodBase = apiUrl.replace(/\/+$/, '') + (apiUrl.includes('/api/v1') ? '' : '/api/v1');
          this.emitFile({
            type: 'asset',
            fileName: 'config.js',
            source: `// Dynamically generated at build time from VITE_API_URL\nwindow.VITE_API_URL = ${JSON.stringify(apiUrl)};\nwindow.API_BASE_URL = ${JSON.stringify(prodBase)};\n`,
          });
        },
      },
    ],
    build: {
      outDir: 'dist',
      rollupOptions: {
        input: {
          main: './index.html',
        },
      },
    },
    test: {
      environment: 'jsdom',
      globals: true,
      setupFiles: ['./tests/setup.js'],
      css: false,
      coverage: {
        provider: 'v8',
        reporter: ['text', 'lcov'],
      },
    },
  };
});
