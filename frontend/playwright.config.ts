import { defineConfig } from "@playwright/test";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const frontendPort = 4173;
const backendPort = 8010;
const currentDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(currentDir, "..");

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  fullyParallel: false,
  retries: 0,
  reporter: "list",
  use: {
    baseURL: `http://127.0.0.1:${frontendPort}`,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  webServer: [
    {
      command: ".\\.venv-chat\\Scripts\\python.exe start.py --host 127.0.0.1 --port 8010",
      cwd: repoRoot,
      url: `http://127.0.0.1:${backendPort}/api/health/live`,
      reuseExistingServer: true,
      timeout: 120_000,
      stdout: "pipe",
      stderr: "pipe",
      env: {
        BUSINESS_LETTER_VALIDATION_REPORT_DIR: resolve(repoRoot, "data", "temp", "playwright-validation-reports"),
      },
    },
    {
      command: `npm run dev -- --host 127.0.0.1 --port ${frontendPort}`,
      cwd: currentDir,
      url: `http://127.0.0.1:${frontendPort}`,
      reuseExistingServer: true,
      timeout: 120_000,
      stdout: "pipe",
      stderr: "pipe",
      env: {
        VITE_DEV_BACKEND_TARGET: `http://127.0.0.1:${backendPort}`,
      },
    },
  ],
});
