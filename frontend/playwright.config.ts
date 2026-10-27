import { defineConfig } from "@playwright/test";

const APP_PORT = 3010;
const API_PORT = 8010;
const CI = Boolean(process.env.CI);

/**
 * The browser tests run the real frontend against e2e/mock-api.ts, which replays the recorded
 * check. They never touch the network or a real backend.
 *
 * CI gets slower, shared machines: more patience per assertion, two retries, and a trace of the
 * first retry so a failure can be read from the uploaded report instead of guessed at.
 */
export default defineConfig({
  testDir: "./e2e",
  retries: CI ? 2 : 0,
  workers: CI ? 2 : undefined,
  timeout: CI ? 60_000 : 30_000,
  expect: { timeout: CI ? 10_000 : 5_000 },
  reporter: CI ? [["github"], ["html", { open: "never" }]] : "list",
  use: { baseURL: `http://localhost:${APP_PORT}`, trace: CI ? "on-first-retry" : "retain-on-failure" },
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
  webServer: [
    {
      command: "node e2e/mock-api.ts",
      url: `http://localhost:${API_PORT}/api/health`,
      env: { MOCK_API_PORT: String(API_PORT), MOCK_ALLOWED_ORIGIN: `http://localhost:${APP_PORT}` },
      reuseExistingServer: !CI,
    },
    {
      command: `node scripts/build-with-retry.ts && npx next start -p ${APP_PORT}`,
      url: `http://localhost:${APP_PORT}`,
      env: { NEXT_PUBLIC_API_URL: `http://localhost:${API_PORT}` },
      timeout: 240_000,
      reuseExistingServer: !CI,
    },
  ],
});
