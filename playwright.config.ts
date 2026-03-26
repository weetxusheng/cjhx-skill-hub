import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  use: {
    trace: "retain-on-failure",
    baseURL: "http://127.0.0.1:4173",
  },
  webServer: [
    {
      command:
        "cd apps/api-server && .venv/bin/alembic upgrade head && .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000",
      url: "http://127.0.0.1:8000/health/live",
      reuseExistingServer: true,
      timeout: 120_000,
    },
    {
      command: "pnpm --filter portal-web build && pnpm preview:portal",
      url: "http://127.0.0.1:4173",
      reuseExistingServer: true,
      timeout: 120_000,
    },
    {
      command: "pnpm --filter admin-web build && pnpm preview:admin",
      url: "http://127.0.0.1:4174",
      reuseExistingServer: true,
      timeout: 120_000,
    },
  ],
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
