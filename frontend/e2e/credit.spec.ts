import { expect, test, type Page } from "@playwright/test";

import { signInAsAsha } from "./signedIn";

const API = "http://localhost:8010";
const CORS = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "Authorization, Content-Type" };
const CREDIT_REPORT = `/report/${"c".repeat(32)}`;

const LIMITS = {
  require_signin: true,
  invite_only: false,
  checks_per_account_per_day: 2,
  reuse_report_days: 7,
  recheck_min_days: 7,
  live_checks_open: true,
  checks_left_today: null,
  invited: null,
};

/** Answers every POST /api/checks with the given refusal; other calls go on to the mock API. */
async function refuseChecks(page: Page, status: number, detail: Record<string, string>, retryAfter = "3600") {
  await page.route(`${API}/api/checks`, (route) =>
    route.request().method() === "POST"
      ? route.fulfill({
          status,
          headers: { ...CORS, "Retry-After": retryAfter },
          contentType: "application/json",
          body: JSON.stringify({ detail }),
        })
      : route.fallback(),
  );
}

async function limitSearches(page: Page) {
  await page.route(`${API}/api/projects/search**`, (route) =>
    route.fulfill({
      status: 429,
      headers: { ...CORS, "Retry-After": "3600" },
      contentType: "application/json",
      body: JSON.stringify({ detail: { code: "search_limit", message: "x" } }),
    }),
  );
}

test.describe("starting a live check", () => {
  test("signed out, the button asks for a sign-in and returns to this page afterwards", async ({ page }) => {
    await page.route(`${API}/api/limits`, (route) =>
      route.fulfill({ headers: CORS, contentType: "application/json", body: JSON.stringify(LIMITS) }),
    );
    // A recent report would open for anyone; this project has none, so the API asks for a sign-in.
    await refuseChecks(page, 401, { code: "signin_required", message: "Sign in to run a live check." });
    await page.goto("/check?q=Supertech%20Eco%20Village");
    const button = page.getByRole("button", { name: "Sign in to run a live check" });
    await expect(button).toBeVisible();
    await expect(page.getByText("A report of this project less than 7 days old opens without signing in.")).toBeVisible();

    await button.click();
    await expect(page).toHaveURL(/\/login\?next=%2Fcheck%3Fq%3DSupertech%2520Eco%2520Village$/);
  });

  test("signed in, the page says how many live checks are left today", async ({ page }) => {
    await signInAsAsha(page);
    await page.route(`${API}/api/limits`, (route) =>
      route.fulfill({
        headers: CORS,
        contentType: "application/json",
        body: JSON.stringify({ ...LIMITS, checks_left_today: 1, invited: true }),
      }),
    );
    await page.goto("/check?q=Supertech%20Eco%20Village");
    await expect(page.getByRole("button", { name: "Yes, check this project" })).toBeVisible();
    await expect(page.getByText("You have 1 live check left today.")).toBeVisible();
  });

  test("a used-up account limit is explained calmly", async ({ page }) => {
    await signInAsAsha(page);
    await refuseChecks(page, 429, { code: "account_limit", message: "x", resets_at: "2026-10-29T00:00:00+05:30" });
    await page.goto("/check?q=Supertech%20Eco%20Village");
    await page.getByRole("button", { name: "Yes, check this project" }).click();
    await expect(page.locator("section[role=alert]")).toContainText("You have used your live checks for today.");
  });

  test("the site budget message keeps saved reports open", async ({ page }) => {
    await signInAsAsha(page);
    await refuseChecks(page, 429, { code: "site_budget", message: "Today's live checks are used up." });
    await page.goto("/check?q=Supertech%20Eco%20Village");
    await page.getByRole("button", { name: "Yes, check this project" }).click();
    await expect(page.locator("section[role=alert]")).toContainText(
      "Today's live checks are used up. Saved reports are still open; new checks open again tomorrow.",
    );
  });

  test("an invite-only deployment says so", async ({ page }) => {
    await signInAsAsha(page);
    await refuseChecks(page, 403, { code: "invite_only", message: "x" });
    await page.goto("/check?q=Supertech%20Eco%20Village");
    await page.getByRole("button", { name: "Yes, check this project" }).click();
    await expect(page.locator("section[role=alert]")).toContainText("Live checks are invite-only right now.");
  });

  test("a search over the daily limit invites a sign-in", async ({ page }) => {
    await limitSearches(page);
    await page.goto("/check?q=Gaur%20City");
    await expect(page.getByText("You have used today's searches. Sign in for more, or come back tomorrow.")).toBeVisible();
  });
});

test.describe("a report", () => {
  test("shows when Re-check now opens instead of the button", async ({ page }) => {
    await page.goto(CREDIT_REPORT);
    await expect(page.getByText("Next re-check possible on 01 Nov 2026")).toBeVisible();
    await expect(page.getByRole("button", { name: /Re-check now/ })).toHaveCount(0);
  });

  test("says a pillar was partly read, and names what was read", async ({ page }) => {
    await page.goto(CREDIT_REPORT);
    await expect(page.getByText(/Partly read \(UP-RERA complaints\)/).first()).toBeVisible();
  });

  test("a fact from a secondary source is grey and never says Confirmed", async ({ page }) => {
    await page.goto(CREDIT_REPORT);
    const row = page.getByRole("listitem").filter({ hasText: "Company status: Active" });
    const badge = row.getByText("From a secondary source").first();
    await expect(badge).toBeVisible();
    await expect(row.getByText("Confirmed")).toHaveCount(0);
    await expect(badge).toHaveClass(/tone-neutral/);
  });

  test("a CAPTCHA lane is not checked automatically and links to the site", async ({ page }) => {
    await page.goto(CREDIT_REPORT);
    await expect(page.getByText(/Not checked automatically: the site needs a CAPTCHA/).first()).toBeVisible();
  });

  test("the Watch button explains Sentinel in one line, with no near-empty card", async ({ page }) => {
    await page.goto(CREDIT_REPORT);
    await expect(page.getByRole("button", { name: "Watch with Sentinel" })).toHaveCount(1);
    await expect(page.getByText("We re-check this project every week and tell you only when a record changes.")).toBeVisible();
  });
});

test("the credit messages are in Hindi too", async ({ page, context }) => {
  await context.addCookies([{ name: "neevcheck-lang", value: "hi", url: "http://localhost:3010" }]);
  await limitSearches(page);
  await page.goto("/check?q=Gaur%20City");
  await expect(page.getByText("आज की खोजें पूरी हो गईं। और के लिए साइन इन करें, या कल आएँ।")).toBeVisible();
});
