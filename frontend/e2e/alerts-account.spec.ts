import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import { signInAsAsha } from "./signedIn";

const API = "http://localhost:8010";
const REPORT = "/report/4ad9752355f9455aa9d242c93950ea04";
const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
  "Access-Control-Allow-Methods": "GET, POST, DELETE",
};

test("signed out, Alerts gives the reason to sign in and has no email box", async ({ page }) => {
  await page.goto("/alerts");
  await expect(page.getByText("Sign in so only you can see and stop your alerts.")).toBeVisible();
  await expect(page.getByRole("link", { name: "Sign in with Google" })).toHaveAttribute("href", "/login");
  await expect(page.locator("input[type=email]")).toHaveCount(0);
  await expect(page.getByRole("article")).toHaveCount(0);
  // Entrance animations pass through low-contrast frames; check the settled page.
  await page.waitForTimeout(1500);
  const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  expect(result.violations.map((v) => v.id)).toEqual([]);
});

test("signed out, Alerts is in Hindi too", async ({ page }) => {
  await page.context().addCookies([{ name: "neevcheck-lang", value: "hi", url: "http://localhost:3010" }]);
  await page.goto("/alerts");
  await expect(page.getByText("साइन इन करें ताकि सिर्फ़ आप अपने अलर्ट देख और बंद कर सकें।")).toBeVisible();
});

test("signed out, Watch this project asks to sign in first and has no email box", async ({ page }) => {
  await page.goto(REPORT);
  await page.getByRole("button", { name: "Watch with Sentinel" }).first().click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByText("Sign in so only you can see and stop your alerts.")).toBeVisible();
  await expect(dialog.locator("input")).toHaveCount(0);
  await expect(dialog.getByRole("button", { name: "Start watching" })).toHaveCount(0);
});

test("signed in, watching sends the token and no email, and promises none while mail is off", async ({ page }) => {
  await signInAsAsha(page);
  const sent: { auth: string | undefined; body: unknown }[] = [];
  await page.route(`${API}/api/sentinel`, (route) => {
    const request = route.request();
    if (request.method() === "OPTIONS") return route.fulfill({ status: 204, headers: CORS });
    sent.push({ auth: request.headers().authorization, body: request.postDataJSON() });
    return route.fulfill({ status: 201, contentType: "application/json", headers: CORS, body: "{}" });
  });

  await page.goto(REPORT);
  await page.getByRole("button", { name: "Watch with Sentinel" }).first().click();
  const dialog = page.getByRole("dialog");
  // The mock API reports no email setup, so the dialog must not promise an email.
  await expect(dialog.getByText(/Alerts appear on your Alerts page/)).toBeVisible();
  await expect(dialog.getByText(/Alerts go to/)).toHaveCount(0);
  await expect(dialog.getByText(/We use your email/)).toHaveCount(0);
  await expect(dialog.locator("input[type=email]")).toHaveCount(0);
  await dialog.getByRole("button", { name: "Start watching" }).click();

  await expect(dialog.getByRole("heading", { name: "Watching this project" })).toBeVisible();
  await expect(dialog.getByText("Alerts appear on your Alerts page.", { exact: true })).toBeVisible();
  await expect(dialog.getByText(/email/i)).toHaveCount(0);
  expect(sent).toHaveLength(1);
  expect(sent[0]?.auth).toBe("Bearer test-token");
  expect(Object.keys(sent[0]?.body as object).sort()).toEqual(["details_url", "language", "rera_id"]);
  await expect(dialog.getByRole("link", { name: "See your alerts" })).toHaveAttribute("href", "/alerts");
});

test("the watch limit is explained per account", async ({ page }) => {
  await signInAsAsha(page);
  await page.route(`${API}/api/sentinel`, (route) =>
    route.request().method() === "OPTIONS"
      ? route.fulfill({ status: 204, headers: CORS })
      : route.fulfill({
          status: 409,
          contentType: "application/json",
          headers: CORS,
          body: JSON.stringify({ detail: { code: "watch_limit", message: "limit" } }),
        }),
  );
  await page.goto(REPORT);
  await page.getByRole("button", { name: "Watch with Sentinel" }).first().click();
  await page.getByRole("dialog").getByRole("button", { name: "Start watching" }).click();
  await expect(page.getByRole("alert").filter({ hasText: "One account can watch up to 3 projects" })).toBeVisible();
});
