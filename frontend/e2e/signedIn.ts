import type { Page } from "@playwright/test";

/** Replays what Auth.js and the token route answer for a signed-in visitor named Asha. */
export async function signInAsAsha(page: Page): Promise<void> {
  await page.route("**/api/auth/session", (route) =>
    route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        user: { id: "google-1", name: "Asha Buyer", email: "asha@example.com", image: null },
        expires: "2999-01-01T00:00:00.000Z",
      }),
    }),
  );
  await page.route("**/api/bridge-token", (route) =>
    route.fulfill({ contentType: "application/json", body: JSON.stringify({ token: "test-token" }) }),
  );
}
