import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { expect, test, type Page } from "@playwright/test";

import { ASHA, BALA, FakeAccounts } from "./fakeAccounts";

const ECO = "4ad9752355f9455aa9d242c93950ea04";
const AVENUE = (JSON.parse(readFileSync(resolve(__dirname, "fixtures", "summary-6742.json"), "utf-8")) as { id: string }).id;
const ECO_NAME = "SUPERTECH ECO VILLAGE-I PHASE I-C";
const REPORTS_KEY = "neevcheck-reports";
const HOME = "http://localhost:3010/";

async function setup(page: Page): Promise<FakeAccounts> {
  const accounts = new FakeAccounts();
  accounts.alerts.set(ASHA.id, JSON.parse(readFileSync(resolve(__dirname, "fixtures", "alerts.json"), "utf-8")));
  await accounts.install(page);
  await page.route("https://live.tinyfish.example/**", (route) => route.fulfill({ body: "<p>live</p>" }));
  return accounts;
}

const stored = (page: Page) =>
  page.evaluate((key) => JSON.parse(localStorage.getItem(key) ?? "[]") as { id: string; owner: string }[], REPORTS_KEY);

async function signOut(page: Page) {
  await page.getByRole("button", { name: "Your account" }).click();
  await page.getByRole("menuitem", { name: "Sign out" }).click();
  const nav = page.getByRole("navigation", { name: "Main" });
  await expect(nav.getByRole("link", { name: "Sign in", exact: true })).toBeVisible();
}

async function expectNothingOfAsha(page: Page) {
  await page.goto("/reports");
  await expect(page.getByRole("heading", { name: "No reports yet" })).toBeVisible();
  await expect(page.getByRole("article")).toHaveCount(0);
  await page.goto("/alerts");
  await expect(page.getByText("No alerts yet.")).toBeVisible();
  await expect(page.getByRole("article")).toHaveCount(0);
  await page.goto("/");
  await expect(page.getByLabel("Placeholder for your report")).toContainText("Your report appears here");
  await expect(page.getByText("Your recent checks")).toHaveCount(0);
  await expect(page.getByText("Checked in this browser")).toHaveCount(0);
}

test.describe("separate accounts in one browser", () => {
  test("B sees none of A's reports, alerts or recent checks, and A's are intact on return", async ({ page }) => {
    const accounts = await setup(page);

    accounts.signInAs(ASHA);
    await page.goto("/check?q=Supertech%20Eco%20Village");
    await page.getByRole("button", { name: "Yes, check this project" }).click();
    await expect(page).toHaveURL(/\/check\/[0-9a-f]{32}$/);
    // The check went out with Asha's token, so the API saved it to her account on its own.
    expect(accounts.checkTokens).toEqual(["Bearer token-google-asha"]);
    expect(accounts.saved.get(ASHA.id)).toEqual([ECO]);
    expect(accounts.saves).toEqual([]);

    await page.goto("/");
    const recent = page.getByRole("region", { name: "Your recent checks" });
    await expect(recent.getByRole("link", { name: /NeevScore 495/ })).toHaveAttribute("href", `/report/${ECO}`);
    await page.goto("/reports");
    await expect(page.getByRole("article", { name: ECO_NAME })).toBeVisible();
    await page.goto("/alerts");
    await expect(page.getByRole("article")).toHaveCount(1);

    await page.goto("/");
    await signOut(page);
    // Nothing of the account stays in this browser.
    expect((await stored(page)).filter((report) => report.owner !== "anon")).toEqual([]);
    expect(await page.evaluate(() => localStorage.getItem("neevcheck-compare") ?? "[]")).toBe("[]");

    accounts.signInAs(BALA);
    await expectNothingOfAsha(page);

    accounts.signInAs(ASHA);
    await page.goto("/reports");
    await expect(page.getByRole("article", { name: ECO_NAME })).toBeVisible();
    await page.goto("/alerts");
    await expect(page.getByRole("article")).toHaveCount(1);
    await page.goto("/");
    await expect(page.getByRole("region", { name: "Your recent checks" })).toBeVisible();
  });

  test("signed out after A, the home page and My reports show nothing of A", async ({ page }) => {
    const accounts = await setup(page);
    accounts.signInAs(ASHA);
    accounts.saved.set(ASHA.id, [ECO]);
    await page.goto("/");
    await expect(page.getByRole("region", { name: "Your recent checks" })).toBeVisible();

    await signOut(page);
    await page.goto("/reports");
    await expect(page.getByRole("heading", { name: "No reports yet" })).toBeVisible();
    await page.goto("/");
    await expect(page.getByLabel("Placeholder for your report")).toContainText("Your report appears here");
    await expect(page.getByRole("region", { name: "Your recent checks" })).toHaveCount(0);
  });

  test("while signed in, reports made in this browser are not mixed into any list", async ({ page }) => {
    const accounts = await setup(page);
    accounts.signInAs(ASHA);
    accounts.saved.set(ASHA.id, [ECO]);
    await page.addInitScript(
      ({ key, id }) => {
        if (localStorage.getItem(key) === null) localStorage.setItem(key, JSON.stringify([{ id, owner: "anon" }]));
      },
      { key: REPORTS_KEY, id: AVENUE },
    );
    await page.goto("/reports");
    // Declining keeps the browser's report out of the account's list.
    await page.getByRole("button", { name: "Not now" }).click();
    await expect(page.getByRole("article", { name: ECO_NAME })).toBeVisible();
    await expect(page.getByRole("article")).toHaveCount(1);
    await page.goto("/");
    const recent = page.getByRole("region", { name: "Your recent checks" });
    await expect(recent.getByRole("listitem")).toHaveCount(1);
  });
});

test.describe("reports made while signed out", () => {
  async function seed(page: Page) {
    // An anonymous report, and one that another account made in this browser earlier.
    await page.addInitScript(
      ({ key, mine, theirs }) => {
        if (localStorage.getItem(key) !== null) return;
        const reports = [
          { id: mine, owner: "anon" },
          { id: theirs, owner: "google-someone-else" },
        ];
        localStorage.setItem(key, JSON.stringify(reports));
      },
      { key: REPORTS_KEY, mine: ECO, theirs: AVENUE },
    );
  }

  test("are offered to the account and only moved when the visitor says Add", async ({ page }) => {
    const accounts = await setup(page);
    await seed(page);
    accounts.signInAs(ASHA);

    await page.goto("/");
    const dialog = page.getByRole("dialog", { name: "Add the 1 report from this browser to your account?" });
    await expect(dialog).toBeVisible();
    expect(accounts.saves).toEqual([]);

    await dialog.getByRole("button", { name: "Not now" }).click();
    await expect(dialog).toBeHidden();
    expect(accounts.saves).toEqual([]);
    expect(await stored(page)).toContainEqual({ id: ECO, owner: "anon" });

    // The next sign-in asks again.
    await page.reload();
    await expect(dialog).toBeVisible();
    await dialog.getByRole("button", { name: "Add" }).click();
    await expect(dialog).toBeHidden();

    // Only the anonymous report moved; the other account's was never touched or sent.
    expect(accounts.saves).toEqual([{ account: ASHA.id, ids: [ECO] }]);
    expect(await stored(page)).toEqual([]);

    await page.goto("/reports");
    await expect(page.getByRole("article", { name: ECO_NAME })).toBeVisible();
  });

  test("stay in the browser, listed as 'Checked in this browser', while nobody is signed in", async ({ page }) => {
    await setup(page);
    await seed(page);
    await page.goto("/");
    await expect(page.getByRole("dialog")).toHaveCount(0);
    const strip = page.getByRole("region", { name: "Checked in this browser" });
    await expect(strip.getByRole("listitem")).toHaveCount(1);
    await expect(strip.getByRole("link", { name: /NeevScore 495/ })).toBeVisible();
  });

  test("a different account's report is never offered to a new sign-in", async ({ page }) => {
    const accounts = await setup(page);
    await page.addInitScript(
      ({ key, id }) => {
        if (localStorage.getItem(key) === null) {
          localStorage.setItem(key, JSON.stringify([{ id, owner: "google-someone-else" }]));
        }
      },
      { key: REPORTS_KEY, id: AVENUE },
    );
    accounts.signInAs(BALA);
    await page.goto("/");
    await expect(page.getByRole("button", { name: "Your account" })).toBeVisible();
    await expect(page.getByRole("dialog")).toHaveCount(0);
    expect(accounts.saves).toEqual([]);
  });
});

test.describe("after signing in", () => {
  /** Auth.js posts the sign-in; here the call is caught and the visitor lands on callbackUrl. */
  async function catchSignIn(page: Page, accounts: FakeAccounts): Promise<{ callbackUrl: () => string | null }> {
    let callbackUrl: string | null = null;
    await page.route("**/api/auth/signin/google", (route) => {
      callbackUrl = new URLSearchParams(route.request().postData() ?? "").get("callbackUrl");
      accounts.signInAs(ASHA);
      return route.fulfill({ contentType: "application/json", body: JSON.stringify({ url: callbackUrl }) });
    });
    return { callbackUrl: () => callbackUrl };
  }

  test("the header and /login lead to the home page", async ({ page }) => {
    const accounts = await setup(page);
    const signIn = await catchSignIn(page, accounts);
    await page.goto("/reports");
    await page.getByRole("navigation", { name: "Main" }).getByRole("link", { name: "Sign in", exact: true }).click();
    await expect(page).toHaveURL(/\/login$/);
    await page.getByRole("button", { name: "Continue with Google" }).click();
    await expect(page.getByRole("button", { name: "Your account" })).toBeVisible();
    expect(signIn.callbackUrl()).toBe("/");
    await expect(page).toHaveURL(HOME);
  });

  test("Watch this project returns to the report and reopens the dialog", async ({ page }) => {
    const accounts = await setup(page);
    const signIn = await catchSignIn(page, accounts);
    await page.goto(`/report/${ECO}`);
    await page.getByRole("button", { name: "Watch with Sentinel" }).first().click();
    await page.getByRole("dialog").getByRole("link", { name: "Sign in with Google" }).click();
    await expect(page).toHaveURL(`/login?next=${encodeURIComponent(`/report/${ECO}?watch=1`)}`);
    await page.getByRole("button", { name: "Continue with Google" }).click();

    const dialog = page.getByRole("dialog", { name: "Watch this project" });
    await expect(dialog.getByRole("button", { name: "Start watching" })).toBeVisible();
    expect(signIn.callbackUrl()).toBe(`/report/${ECO}?watch=1`);
    // The marker is used up, so a reload does not open the dialog again.
    await expect(page).toHaveURL(`${HOME}report/${ECO}`);
  });

  test("an address outside this site is ignored", async ({ page }) => {
    const accounts = await setup(page);
    const signIn = await catchSignIn(page, accounts);
    for (const next of ["https://evil.example/steal", "//evil.example", "/\\evil.example"]) {
      await page.goto(`/login?next=${encodeURIComponent(next)}`);
      await page.getByRole("button", { name: "Continue with Google" }).click();
      await expect(page).toHaveURL(HOME);
      expect(signIn.callbackUrl()).toBe("/");
      accounts.signInAs(null);
    }
  });
});
