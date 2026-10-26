import { expect, test } from "@playwright/test";

const API = "http://localhost:8010";
const RESULTS = "We found 2 projects for “Supertech Eco Village”";

test("a slow, sleeping server: waking notice first, then the search, then results", async ({ page }) => {
  await page.route(`${API}/api/health`, async (route) => {
    await new Promise((done) => setTimeout(done, 2500));
    await route.continue();
  });
  await page.route(`${API}/api/projects/search**`, async (route) => {
    await new Promise((done) => setTimeout(done, 1500));
    await route.continue();
  });

  await page.goto("/check?q=Supertech%20Eco%20Village");
  await expect(page.getByRole("status").filter({ hasText: "Waking up the server" })).toBeVisible();
  await expect(page.getByRole("status").filter({ hasText: "Searching RERA portals" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(RESULTS);
});

test("a proxy error while the server starts is retried once without bothering the visitor", async ({ page }) => {
  let calls = 0;
  await page.route(`${API}/api/projects/search**`, async (route) => {
    calls += 1;
    if (calls === 1) return route.fulfill({ status: 503, contentType: "text/html", body: "<p>starting</p>" });
    return route.continue();
  });

  await page.goto("/check?q=Supertech%20Eco%20Village");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(RESULTS);
  expect(calls).toBe(2);
});

test("a real API error names its reason and is not retried", async ({ page }) => {
  let calls = 0;
  await page.route(`${API}/api/projects/search**`, (route) => {
    calls += 1;
    return route.fulfill({
      status: 502,
      contentType: "application/json",
      headers: { "Access-Control-Allow-Origin": "*" },
      body: JSON.stringify({ detail: { code: "wallet_empty", message: "Search failed: no credit" } }),
    });
  });

  await page.goto("/check?q=Supertech%20Eco%20Village");
  const alert = page.locator("section[role=alert]");
  await expect(alert).toContainText("We could not search the RERA portals just now");
  await expect(alert).toContainText("out of credit");
  expect(calls).toBe(1);
});

test("a search that is rate limited says how long to wait", async ({ page }) => {
  await page.route(`${API}/api/projects/search**`, (route) =>
    route.fulfill({
      status: 429,
      contentType: "application/json",
      headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Expose-Headers": "Retry-After", "Retry-After": "40" },
      body: JSON.stringify({ detail: { code: "rate_limited", message: "Search failed: rate limit" } }),
    }),
  );
  await page.goto("/check?q=Gaur%20City");
  await expect(page.locator("section[role=alert]")).toContainText("try again in 40 seconds");
});
