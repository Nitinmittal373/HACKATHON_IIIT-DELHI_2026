import { expect, test } from "@playwright/test";

const MH_NUMBER = "P99000055716";

test("a MahaRERA number is recognised, confirmed and checked, and the report wears the MH badge", async ({ page }) => {
  await page.goto("/");
  await page.locator("#search").first().getByRole("searchbox").fill(MH_NUMBER);
  // The picker follows the number's format.
  await expect(page.locator("#search").first().getByLabel("State", { exact: true })).toHaveValue("MH");
  await page.locator("#search").first().getByRole("button", { name: "Check project" }).click();

  await expect(page).toHaveURL(/\/check\?q=P99000055716&state=MH/);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("We found 1 project");
  const group = page.getByRole("region", { name: "Maharashtra" });
  await expect(group.getByText("Search only")).toBeVisible();
  await expect(group.getByText("From the official portal's search results")).toBeVisible();
  await expect(group.getByRole("link", { name: /Open on MahaRERA/ })).toHaveAttribute("href", /maharera/);

  await page.getByRole("button", { name: "Yes, check this project" }).click();
  // The recorded check is already finished, so the live view hands over to its report.
  await expect(page).toHaveURL(new RegExp(`/report/${"a1".repeat(16)}`), { timeout: 20_000 });
  const header = page.getByRole("main").locator("header").first();
  await expect(header.getByText("MH", { exact: true })).toBeVisible();
  await expect(header.getByText("Maharashtra")).toBeVisible();
  await expect(page.getByText("From the official portal's search results").first()).toBeVisible();
  // The copy names this state's authority, not UP-RERA.
  await expect(page.getByText("UP-RERA")).toHaveCount(0);
});

test("a name search groups the results by state", async ({ page }) => {
  await page.goto("/check?q=Prestige%20Lakeside%20Habitat");
  await expect(page.getByRole("region", { name: "Karnataka" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Uttar Pradesh" })).toBeVisible();
  await expect(page.getByText("Searched: KA, UP")).toBeVisible();
});

test("the coverage page lists every state and marks formats not yet verified", async ({ page }) => {
  await page.goto("/coverage");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Which states NeevCheck can read");
  const rows = page.locator("tbody tr");
  expect(await rows.count()).toBeGreaterThanOrEqual(20);
  await expect(rows.filter({ hasText: "Uttar Pradesh" })).toContainText("Full");
  await expect(rows.filter({ hasText: "Goa" })).toContainText("Partial");
  const telangana = rows.filter({ hasText: "Telangana" });
  await expect(telangana).toContainText("Number format not yet verified");
  await expect(telangana).not.toContainText("P0");
  await page.getByRole("link", { name: "Coverage" }).click();
  await expect(page).toHaveURL(/\/coverage/);
});

test("the footer links to coverage in Hindi too", async ({ page }) => {
  await page.context().addCookies([{ name: "neevcheck-lang", value: "hi", url: "http://localhost:3010" }]);
  await page.goto("/coverage");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("NeevCheck किन राज्यों को पढ़ सकता है");
});
