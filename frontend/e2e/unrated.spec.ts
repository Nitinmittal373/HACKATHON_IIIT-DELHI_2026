import { expect, test } from "@playwright/test";

// The recorded Maharashtra check read 2 of 6 record types: too little to give a number.
const MH_REPORT = `/report/${"a1".repeat(16)}`;
const REASON = /Not enough evidence yet · 2 of 6 record types read/;

test("a project with too little read shows a dash and the reason, never a number", async ({ page }) => {
  await page.goto(MH_REPORT);

  const dial = page.getByRole("img", { name: /Not enough evidence yet/ }).first();
  await expect(dial).toBeVisible();
  await expect(dial).toContainText("—");
  await expect(dial).toContainText(REASON);
  // The summary chip carries the dash too.
  await expect(page.getByLabel("In plain words").getByText("—")).toBeVisible();
  // The computed figure is kept for the method section only, and is called what it is.
  await expect(page.getByText(/Provisional figure, not a score: 900 out of 900/)).toBeVisible();
  expect(await page.title()).toContain("not enough evidence yet");
  expect(await page.title()).not.toMatch(/NeevScore \d/);
});

test("the unrated report is in Hindi too", async ({ page }) => {
  await page.context().addCookies([{ name: "neevcheck-lang", value: "hi", url: "http://localhost:3010" }]);
  await page.goto(MH_REPORT);
  await expect(page.getByText(/अभी पर्याप्त प्रमाण नहीं · 6 में से 2 तरह के रिकॉर्ड पढ़े गए/).first()).toBeVisible();
});

test("a project that was read well keeps its number", async ({ page }) => {
  await page.goto("/report/4ad9752355f9455aa9d242c93950ea04");
  await expect(page.getByRole("img", { name: /^NeevScore \d+ out of 900/ }).first()).toBeVisible();
  expect(await page.title()).toMatch(/NeevScore \d+/);
});

test("the share picture is served for an unrated report", async ({ page, request }) => {
  await page.goto(MH_REPORT);
  const picture = await page.locator('meta[property="og:image"]').getAttribute("content");
  expect(picture).toBeTruthy();
  const response = await request.get(new URL(picture ?? "").pathname);
  expect(response.status()).toBe(200);
  expect(response.headers()["content-type"]).toContain("image/png");
});
