import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    host: "127.0.0.1",
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    chunkSizeWarningLimit: 500,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) {
            return;
          }

          const normalized = id.replace(/\\/g, "/");

          if (
            normalized.includes("/react/") ||
            normalized.includes("/react-dom/") ||
            normalized.includes("/react-router-dom/")
          ) {
            return "vendor-react";
          }

          if (normalized.includes("/@tanstack/react-query/")) {
            return "vendor-query";
          }

          if (normalized.includes("/recharts/")) {
            return "vendor-charts";
          }

          if (normalized.includes("/@phosphor-icons/react/")) {
            return "vendor-icons";
          }

          if (normalized.includes("/framer-motion/")) {
            return "vendor-motion";
          }

          if (
            normalized.includes("/react-markdown/") ||
            normalized.includes("/remark-gfm/")
          ) {
            return "vendor-markdown";
          }

          if (
            normalized.includes("/@dnd-kit/core/") ||
            normalized.includes("/@dnd-kit/sortable/")
          ) {
            return "vendor-dnd";
          }

          if (normalized.includes("/date-fns/")) {
            return "vendor-date";
          }

          if (
            normalized.includes("/axios/") ||
            normalized.includes("/zustand/") ||
            normalized.includes("/clsx/") ||
            normalized.includes("/class-variance-authority/") ||
            normalized.includes("/tailwind-merge/") ||
            normalized.includes("/tw-animate-css/")
          ) {
            return "vendor-utils";
          }
        },
      },
    },
  },
});
