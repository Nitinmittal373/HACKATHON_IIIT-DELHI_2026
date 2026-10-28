import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const API = "http://localhost:8010";
const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Authorization, Content-Type",
  "Access-Control-Allow-Methods": "GET, POST, DELETE",
};

test("the privacy page says what is kept, in English", async ({ page }) => {
  await page.goto("/privacy");
  await expect(page.getByRole("heading", { level: 1, name: "Privacy" })).toBeVisible();
  await expect(page.getByText("Last updated 28 Oct 2026")).toBeVisible();
  await expect(page.getByText("your Google account id and the list of reports you saved")).toBeVisible();
  await expect(page.getByRole("link", { name: "neevcheck.help@gmail.com" })).toHaveAttribute(
    "href",
    "mailto:neevcheck.help@gmail.com",
  );
  const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  expect(result.violations.map((v) => v.id)).toEqual([]);
});

test("the privacy page is in Hindi too", async ({ page }) => {
  await page.context().addCookies([{ name: "neevcheck-lang", value: "hi", url: "http://localhost:3010" }]);
  await page.goto("/privacy");
  await expect(page.getByRole("heading", { level: 1, name: "गोपनीयता" })).toBeVisible();
  await expect(page.getByText("आख़िरी बार अपडेट: 28 अक्टू॰ 2026")).toBeVisible();
  await expect(page.getByRole("heading", { name: "अपना डेटा हटाएँ" })).toBeVisible();
});

test("the footer and the login page link to it", async ({ page }) => {
  await page.goto("/login");
  await page.locator("main").getByRole("link", { name: "Read our privacy page" }).click();
  await expect(page).toHaveURL(/\/privacy$/);
  await page.goto("/");
  await page.getByRole("contentinfo").getByRole("link", { name: "Privacy" }).click();
  await expect(page).toHaveURL(/\/privacy$/);
});

test("Delete my data asks first, sends the token, then signs out", async ({ page }) => {
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
  await page.route(`${API}/api/me/reports`, (route) =>
    route.fulfill({ contentType: "application/json", headers: CORS, body: "[]" }),
  );
  const sent: (string | undefined)[] = [];
  await page.route(`${API}/api/me`, (route) => {
    const request = route.request();
    if (request.method() === "OPTIONS") return route.fulfill({ status: 204, headers: CORS });
    sent.push(request.headers().authorization);
    return route.fulfill({ status: 204, headers: CORS });
  });

  await page.goto("/");
  const open = async () => {
    await page.getByRole("navigation", { name: "Main" }).getByRole("button", { name: "Account menu" }).click();
  };

  // Cancelling the question deletes nothing.
  page.once("dialog", (dialog) => dialog.dismiss());
  await open();
  await page.getByRole("menuitem", { name: "Delete my data" }).click();
  expect(sent).toEqual([]);

  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("menuitem", { name: "Delete my data" }).click();
  await expect.poll(() => sent).toEqual(["Bearer test-token"]);
});
