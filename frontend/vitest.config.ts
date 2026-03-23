import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/__tests__/setup.ts"],
    globals: true,
    coverage: {
      reporter: ["text", "json", "html"],
      include: ["src/**/*.{ts,tsx}"],
      exclude: [
        "src/__tests__/**",
        "src/api/**",
        "src/components/analytics/**",
        "src/components/pipeline/**",
        "src/components/scraper/**",
        "src/lib/types.ts",
        "src/main.tsx",
        "src/pages/CanonicalJobs.tsx",
        "src/pages/Onboarding.tsx",
        "src/vite-env.d.ts",
      ],
    },
  },
});
