import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      process: "process/browser",
    },
  },
  define: {
    "globalThis.process": JSON.stringify({ env: {} }),
  },
  server: {
    port: 5173,
    proxy: {
      // Any request the frontend makes to /api/* gets forwarded to FastAPI.
      // This avoids CORS headaches during local development.
      "/api": {
        target: "http://localhost:8001",
        changeOrigin: true,
      },
    },
    watch: {
      usePolling: true,
    },
  },
});
