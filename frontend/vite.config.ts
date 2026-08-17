import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      // Em dev, evita problema de CORS falando com o backend local
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
