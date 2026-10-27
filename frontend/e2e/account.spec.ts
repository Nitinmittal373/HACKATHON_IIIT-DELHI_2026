import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const API = "http://localhost:8010";
const ECO = "4ad9752355f9455aa9d242c93950ea04";
const CORS = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "Authorization, Content-Type" };

async function violations(page: Page) {
  const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  return result.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join(" | ")}`);
}

test.describe("signed out", () => {
  test("the header and the landing page offer a way in, never a requirement", async ({ page }) => {
    await page.goto("/");
    const nav = page.getByRole("navigation", { name: "Main" });
    await expect(nav.getByRole("link", { name: "Sign in" })).toBeVisible();
    await expect(nav.getByRole("link", { name: "My reports" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Sign in to save reports and get alerts" })).toBeVisible();
  });

  test("a project can be searched and checked without signing in", async ({ page }) => {
    await page.route("https://live.tinyfish.example/**", (route) => route.fulfill({ body: "<p>live</p>" }));
    await page.goto("/check?q=Supertech%20Eco%20Village");
    await page.getByRole("button", { name: "Yes, check this project" }).click();
    await expect(page).toHaveURL(/\/check\/[0-9a-f]{32}$/);
    await expect(page.getByRole("link", { name: "Sign in", exact: true })).toBeVisible();
    const saved = await page.evaluate(() => localStorage.getItem("neevcheck-reports"));
    expect(JSON.parse(saved ?? "[]")).toContain(ECO);
  });

  test("the login page says what is kept and that no account is needed", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: "Sign in to NeevCheck" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Continue with Google" })).toBeEnabled();
    await expect(page.getByText("You never need an account to check a project.")).toBeVisible();
    await expect(page.getByText("We keep only your name, email and saved reports.")).toBeVisible();
    expect(await violations(page)).toEqual([]);
  });

  test("the login page is in Hindi too", async ({ page }) => {
    await page.context().addCookies([{ name: "neevcheck-lang", value: "hi", url: "http://localhost:3010" }]);
    await page.goto("/login");
    await expect(page.getByRole("button", { name: "Google से जारी रखें" })).toBeVisible();
    await expect(page.getByText("हम सिर्फ़ आपका नाम, ईमेल और सहेजी हुई रिपोर्ट रखते हैं।")).toBeVisible();
  });

  test("the login page fits a phone", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/login");
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(0);
  });

  test("the saved-report token route refuses a visitor who is not signed in", async ({ request }) => {
    expect((await request.get("/api/bridge-token")).status()).toBe(401);
  });
});

test.describe("signed in", () => {
  async function signIn(page: Page) {
    // Auth.js answers /api/auth/session with the signed-in user; here that answer is replayed.
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

  test("the avatar menu replaces Sign in, and this browser's reports move into the account", async ({ page }) => {
    await signIn(page);
    await page.addInitScript((ids) => localStorage.setItem("neevcheck-reports", JSON.stringify(ids)), [ECO]);
    const sent: { auth: string | undefined; ids: string[] }[] = [];
    await page.route(`${API}/api/me/reports`, async (route) => {
      const request = route.request();
      if (request.method() === "OPTIONS") return route.fulfill({ status: 204, headers: CORS });
      if (request.method() === "POST") {
        sent.push({ auth: request.headers().authorization, ids: request.postDataJSON().ids });
      }
      return route.fulfill({ contentType: "application/json", headers: CORS, body: "[]" });
    });

    await page.goto("/");
    const nav = page.getByRole("navigation", { name: "Main" });
    await expect(nav.getByRole("button", { name: "Your account" })).toBeVisible();
    await expect(nav.getByRole("link", { name: "Sign in", exact: true })).toHaveCount(0);
    await expect(page.getByRole("link", { name: "Sign in to save reports and get alerts" })).toHaveCount(0);

    await nav.getByRole("button", { name: "Your account" }).click();
    await expect(page.getByRole("menuitem", { name: "My reports" })).toBeVisible();
    await expect(page.getByRole("menuitem", { name: "Sign out" })).toBeVisible();

    await expect.poll(() => sent.length).toBe(1);
    expect(sent[0]).toEqual({ auth: "Bearer test-token", ids: [ECO] });
    // Once moved, the list leaves this browser.
    await expect.poll(() => page.evaluate(() => localStorage.getItem("neevcheck-reports"))).toBe("[]");
  });

  test("My reports lists the account's reports and Alerts lists the account's alerts", async ({ page }) => {
    await signIn(page);
    const summary = {
      id: ECO,
      rera_id: "UPRERAPRJ8334",
      details_url: "https://www.up-rera.in/Frm_View_Project_Details.aspx?id=8334",
      project: "SUPERTECH ECO VILLAGE-I PHASE I-C",
      promoter: "SUPERTECH LIMITED",
      status: "completed",
      score: 68,
      band: "Moderate",
      confidence: 0.71,
      display_score: {
        value: 495,
        provisional_value: null,
        band: "Elevated",
        hard_stop: false,
        confidence: 0.83,
        provisional: false,
        records_read: 5,
        records_total: 6,
      },
      created_at: "2026-10-25T04:00:00Z",
      completed_at: "2026-10-25T04:00:00Z",
    };
    await page.route(`${API}/api/me/reports`, (route) =>
      route.request().method() === "OPTIONS"
        ? route.fulfill({ status: 204, headers: CORS })
        : route.fulfill({ contentType: "application/json", headers: CORS, body: JSON.stringify([summary]) }),
    );

    await page.goto("/reports");
    const card = page.getByRole("article", { name: "SUPERTECH ECO VILLAGE-I PHASE I-C" });
    await expect(card).toContainText("UPRERAPRJ8334");
    await expect(page.getByText("Saved to your account.")).toBeVisible();

    await page.goto("/alerts");
    await expect(page.getByRole("article")).toHaveCount(1);
    await expect(page.locator("#alerts-email")).toHaveCount(0);
  });
});
