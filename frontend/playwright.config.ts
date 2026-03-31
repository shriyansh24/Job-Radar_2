import { defineConfig } from "@playwright/test";
import process from "node:process";
import { fileURLToPath } from "node:url";

const frontendRoot = fileURLToPath(new URL(".", import.meta.url));
const repoRoot = fileURLToPath(new URL("..", import.meta.url));
const baseURL = process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:5173";

process.env.PLAYWRIGHT_BASE_URL ??= baseURL;
process.env.VITE_API_PROXY_TARGET ??= "http://127.0.0.1:8000";
process.env.JR_DEBUG ??= "true";
process.env.JR_SECRET_KEY ??= "playwright-local-secret";
process.env.JR_CORS_ORIGINS ??= '["http://127.0.0.1:5173","http://localhost:5173"]';
process.env.JR_TRUSTED_HOSTS ??= '["127.0.0.1","localhost","test"]';

export default defineConfig({
  testDir: "./e2e",
  outputDir: "./test-results/e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [["list"], ["html", { outputFolder: "./playwright-report", open: "never" }]],
  use: {
    baseURL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    viewport: { width: 1440, height: 960 },
  },
  webServer: [
    {
      name: "backend-api",
      command: `uv run python "${fileURLToPath(new URL("../scripts/start_playwright_backend.py", import.meta.url))}"`,
      url: "http://127.0.0.1:8000/docs",
      reuseExistingServer: true,
      timeout: 120_000,
      cwd: repoRoot,
    },
    {
      name: "frontend-vite",
      command: "npm run dev -- --host 127.0.0.1 --port 5173",
      url: baseURL,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      cwd: frontendRoot,
    },
  ],
  projects: [
    {
      name: "chromium",
      use: {
        browserName: "chromium",
      },
    },
  ],
});
