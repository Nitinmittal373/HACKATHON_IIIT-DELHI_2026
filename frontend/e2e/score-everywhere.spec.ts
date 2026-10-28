import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { expect, test, type Page } from "@playwright/test";

import type { components } from "../src/lib/api-schema";
import { signInAsAsha } from "./signedIn";

/**
 * Every screen that shows a score shows NeevScore on the scale the API's /api/meta gives. The
 * mock API serves what the real backend answered (see e2e/fixtures), so the numbers asserted
 * here are read from those fixtures, never typed in.
 */

type Schemas = components["schemas"];
const FIXTURES = resolve(__dirname, "fixtures");
const fixture = <T>(name: string): T => JSON.parse(readFileSync(resolve(FIXTURES, name), "utf-8")) as T;

const META = fixture<Schemas["Meta"]>("meta.json");
const REPORT = fixture<Schemas["Report"]>("report.json");
const AVENUE = fixture<Schemas["CheckSummary"]>("summary-6742.json");
const ALERT = fixture<Schemas["Alert"][]>("alerts.json")[0]!;
// The live check, the comparison and the alert replay a run without the v2 sources, so their
// NeevScore differs from the report's; each screen is asserted against its own recording.
const FINISHED = fixture<Schemas["Check"]>("check-done.json").display_score!;
const COMPARED = fixture<Schemas["Comparison"]>("compare.json").projects[0]!.display_score;
const ECO = REPORT.check.id;
const SCORE = REPORT.display_score;

const { min, max } = META.scale;
const BANDS_EN: Record<Schemas["DisplayScore"]["band"], string> = {
  Low: "Low risk",
  Watch: "Watch",
  Elevated: "Elevated risk",
  High: "High risk",
  insufficient_evidence: "Not enough evidence yet",
};
const label = (score: Schemas["DisplayScore"]) =>
  `NeevScore ${score.value} out of ${max}, ${BANDS_EN[score.band]}`;
const NEEVSCORE_LABEL = new RegExp(`^NeevScore (\\d+) out of ${max}, `);

async function remember(page: Page, ids: string[]) {
  await page.addInitScript((saved) => localStorage.setItem("neevcheck-reports", JSON.stringify(saved)), ids);
}

/** Every drawn score on the page, as the values their accessible names announce. */
async function drawnScores(page: Page): Promise<number[]> {
  const labels = await page.locator('[role="img"][aria-label^="NeevScore"]').evaluateAll((nodes) =>
    nodes.map((node) => node.getAttribute("aria-label") ?? ""),
  );
  return labels.map((label) => {
    const match = NEEVSCORE_LABEL.exec(label);
    expect(match, `"${label}" is a NeevScore on the API's scale`).not.toBeNull();
    return Number(match?.[1]);
  });
}

async function noOldScale(page: Page) {
  await expect(page.locator("body")).not.toContainText(/out of 100\b|\/ ?100\b|0 to 100/);
}

test("the fixtures really are on the 300-900 scale the API reports", () => {
  expect([min, max]).toEqual([300, 900]);
  expect(SCORE.value).toBeGreaterThanOrEqual(min);
  expect(SCORE.value).toBeLessThanOrEqual(max);
  expect(META.bands.map((band) => band.key)).toEqual(["Low", "Watch", "Elevated", "High"]);
});

test("how it works: the scale and bands are drawn from the meta", async ({ page }) => {
  await page.goto("/how-it-works");

  await expect(page.getByRole("heading", { name: `The ${min} to ${max} scale` })).toBeVisible();
  const scale = page.getByRole("region", { name: `The ${min} to ${max} scale` });
  for (const band of META.bands) {
    await expect(scale.getByText(`${BANDS_EN[band.key]}: ${band.min} to ${band.max}`)).toBeVisible();
  }
  await noOldScale(page);
});

test("check result: the finished check ends on its NeevScore", async ({ page }) => {
  await page.route("https://live.tinyfish.example/**", (route) => route.fulfill({ body: "<p>live</p>" }));
  await page.goto("/check?q=Supertech%20Eco%20Village");
  await page.getByRole("button", { name: "Yes, check this project" }).click();

  await expect(page.getByText(`NeevScore ${FINISHED.value} · ${BANDS_EN[FINISHED.band]}`)).toBeVisible();
  expect(await drawnScores(page)).toEqual([FINISHED.value]);
  await noOldScale(page);
});

test("report: the dial, the summary, the drivers and the title all use it", async ({ page }) => {
  await page.goto(`/report/${ECO}`);
  // Let the page finish loading, so a score drawn twice while it settles is not counted.
  await page.waitForLoadState("networkidle");

  expect(await drawnScores(page)).toEqual([SCORE.value]);
  await expect(page.getByRole("heading", { name: `Why ${SCORE.value}` })).toBeVisible();
  await expect(page.getByText(`Everyone starts at ${max}.`)).toBeVisible();
  await expect(page).toHaveTitle(`${REPORT.project.name}: NeevScore ${SCORE.value} · NeevCheck`);
  // The classic score appears exactly once, in the method section.
  const method = page.getByRole("region", { name: "How this score is made" });
  await expect(method).toContainText(`Classic score (0–100): ${REPORT.score.value}`);
  await expect(page.getByText("Classic score (0–100)")).toHaveCount(1);
  await expect(page.locator("main").getByText(/out of 100\b|\/ ?100\b/)).toHaveCount(0);
});

test("report: sharing carries the NeevScore on its scale", async ({ page, context }) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.goto(`/report/${ECO}`);
  const popup = page.waitForEvent("popup");
  await page.getByRole("button", { name: "Share on WhatsApp" }).click();
  // The link may already have been redirected, which turns spaces into plus signs.
  const url = decodeURIComponent((await popup).url().replace(/\+/g, " "));
  expect(url).toContain(label(SCORE));
  expect(url).not.toMatch(/\/100/);
});

test("My reports: each card draws the NeevScore and its band", async ({ page }) => {
  await remember(page, [ECO, AVENUE.id]);
  await page.goto("/reports");

  const eco = page.getByRole("article", { name: REPORT.project.name ?? "" });
  await expect(eco.getByRole("img", { name: label(SCORE) })).toBeVisible();
  const avenue = page.getByRole("article", { name: /14th Avenue/ });
  const thin = AVENUE.display_score;
  expect(thin?.provisional).toBe(true);
  // Too little was read, so the card draws a dash and the reason instead of a number.
  expect(thin?.value).toBeNull();
  await expect(avenue).toContainText(BANDS_EN.insufficient_evidence);
  await expect(avenue).toContainText(/Not enough evidence yet · \d of 6 record types read/);
  expect(await drawnScores(page)).toEqual([SCORE.value]);
  await noOldScale(page);
});

test("Compare: the score row and the pillar rows use the scale; only enough evidence is ranked", async ({ page }) => {
  await page.goto(`/compare?ids=${ECO},${AVENUE.id}`);
  const table = page.getByRole("table", { name: "Comparison of the selected projects" });

  const scores = table.getByRole("row", { name: /^NeevScore/ });
  await expect(scores.getByRole("img", { name: label(COMPARED) })).toBeVisible();
  await expect(scores).toContainText(BANDS_EN.insufficient_evidence);
  await expect(table.getByRole("row", { name: /^Legal and insolvency/ })).toContainText("of 150");
  await expect(page.getByRole("status").filter({ hasText: "not enough evidence to rank" })).toBeVisible();
  await noOldScale(page);
});

test("alerts: the score before and after is on the scale", async ({ page }) => {
  await signInAsAsha(page);
  await page.goto("/alerts");

  const card = page.getByRole("article");
  const before = ALERT.old_display_score;
  const after = ALERT.new_display_score;
  expect(before && after).toBeTruthy();
  await expect(card.getByLabel(`NeevScore ${before?.value} to ${after?.value}`)).toBeVisible();
  await expect(card).toContainText(String(after?.value));
  await noOldScale(page);
});

test("in Hindi the band labels and the scale follow the same map", async ({ page }) => {
  await page.context().addCookies([{ name: "neevcheck-lang", value: "hi", url: "http://localhost:3010" }]);
  await page.goto(`/report/${ECO}`);
  await expect(page.getByRole("img", { name: `नींवस्कोर ${max} में से ${SCORE.value}, बढ़ा हुआ जोखिम` })).toBeVisible();
  await page.goto("/how-it-works");
  await expect(page.getByRole("heading", { name: `${min} से ${max} का पैमाना` })).toBeVisible();
});

test("the shared preview image is served for a report", async ({ page, request }) => {
  await page.goto(`/report/${ECO}`);
  const shared = await page.locator('meta[property="og:image"]').getAttribute("content");
  // The page names itself by its public address; the test server listens elsewhere.
  const image = await request.get(new URL(shared ?? "", "http://localhost:3010").pathname);
  expect(image.status()).toBe(200);
  expect(image.headers()["content-type"]).toContain("image/png");
});
