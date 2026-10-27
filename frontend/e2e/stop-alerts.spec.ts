import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

import { signInAsAsha } from "./signedIn";

const API = "http://localhost:8010";
const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
  "Access-Control-Allow-Methods": "GET, POST, DELETE",
};
const TOKEN = "t0ken-from-the-email";

/** Replays the two stop routes and records what the browser sent. */
async function recordStops(page: Page, status = 204) {
  const sent: string[] = [];
  await page.route(`${API}/api/sentinel/**`, (route) => {
    const request = route.request();
    if (request.method() === "OPTIONS") return route.fulfill({ status: 204, headers: CORS });
    if (request.method() === "GET") return route.fallback();
    sent.push(`${request.method()} ${new URL(request.url()).pathname} ${request.postData() ?? ""}`.trim());
    return route.fulfill({ status, headers: CORS, contentType: "application/json", body: status === 204 ? "" : "{}" });
  });
  return sent;
}

test("opening the link only shows the page; the button stops the alerts", async ({ page }) => {
  const sent = await recordStops(page);
  await page.goto(`/alerts/stop?token=${TOKEN}`);
  await expect(page.getByRole("heading", { name: "Stop alerts for this project?" })).toBeVisible();
  const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  expect(result.violations.map((v) => v.id)).toEqual([]);
  expect(sent).toEqual([]);

  await page.getByRole("button", { name: "Stop alerts" }).click();
  await expect(page.getByRole("heading", { name: "Alerts stopped" })).toBeVisible();
  expect(sent).toEqual([`POST /api/sentinel/unsubscribe {"token":"${TOKEN}"}`]);
});

test("the stop page is in Hindi too", async ({ page }) => {
  await page.context().addCookies([{ name: "neevcheck-lang", value: "hi", url: "http://localhost:3010" }]);
  await recordStops(page);
  await page.goto(`/alerts/stop?token=${TOKEN}`);
  await page.getByRole("button", { name: "अलर्ट बंद करें" }).click();
  await expect(page.getByRole("heading", { name: "अलर्ट बंद हो गए" })).toBeVisible();
});

test("a link without a token explains itself and offers no button", async ({ page }) => {
  await page.goto("/alerts/stop");
  await expect(page.getByRole("heading", { name: "This link is incomplete" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Stop alerts" })).toHaveCount(0);
});

test("a failed request says so and lets the reader try again", async ({ page }) => {
  await recordStops(page, 500);
  await page.goto(`/alerts/stop?token=${TOKEN}`);
  await page.getByRole("button", { name: "Stop alerts" }).click();
  await expect(page.getByRole("heading", { name: "We could not stop the alerts" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Stop alerts" })).toBeEnabled();
});

test("each alert has a Stop watching button that removes that watch", async ({ page }) => {
  await signInAsAsha(page);
  const sent = await recordStops(page);
  await page.goto("/alerts");
  const button = page.getByRole("button", { name: /^Stop watching / }).first();
  await expect(button).toBeVisible();
  await button.click();
  await expect.poll(() => sent.length).toBe(1);
  expect(sent[0]).toMatch(/^DELETE \/api\/sentinel\/[0-9a-f]{32}$/);
  // The card goes away with its watch.
  await expect(page.getByRole("article")).toHaveCount(0);
});
