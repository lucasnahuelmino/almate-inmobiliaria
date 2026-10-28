/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// El backend FastAPI corre en 127.0.0.1:8000; en desarrollo se le pasa el
// tráfico de /api y /static a través del proxy para evitar CORS.
const backend = "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [vue()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/api": { target: backend, changeOrigin: true },
      "/static": { target: backend, changeOrigin: true },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    include: ["src/**/*.{test,spec}.ts"],
    exclude: ["node_modules", "dist"],
  },
});
