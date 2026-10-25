import { defineConfig } from "@playwright/test";

const APP_PORT = 3010;
const API_PORT = 8010;

/**
 * The browser tests run the real frontend against e2e/mock-api.ts, which replays the recorded
 * check. They never touch the network or a real backend.
 */
export default defineConfig({
  testDir: "./e2e",
  use: { baseURL: `http://localhost:${APP_PORT}`, trace: "retain-on-failure" },
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
  webServer: [
    {
      command: "node e2e/mock-api.ts",
      url: `http://localhost:${API_PORT}/api/health`,
      env: { MOCK_API_PORT: String(API_PORT), MOCK_ALLOWED_ORIGIN: `http://localhost:${APP_PORT}` },
      reuseExistingServer: !process.env.CI,
    },
    {
      command: `npm run build && npx next start -p ${APP_PORT}`,
      url: `http://localhost:${APP_PORT}`,
      env: { NEXT_PUBLIC_API_URL: `http://localhost:${API_PORT}` },
      timeout: 240_000,
      reuseExistingServer: !process.env.CI,
    },
  ],
});
