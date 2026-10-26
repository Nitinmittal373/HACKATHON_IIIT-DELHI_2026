import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const REPORT = "/report/4ad9752355f9455aa9d242c93950ea04";

async function violations(page: Page) {
  const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  return result.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join(" | ")}`);
}

test("the report leads with the 300-900 score, its reasons and the classic score below", async ({ page }) => {
  await page.goto(REPORT);

  await expect(page.getByRole("img", { name: "NeevScore 621 out of 900, Watch" })).toBeVisible();
  await expect(page.getByText("5 of 6 record types read")).toBeVisible();
  await expect(page.getByText("Risk indicator based on public records — not a credit rating.")).toBeVisible();
  // The classic score is kept, smaller, and says so.
  await expect(page.getByText("Classic score (0–100)")).toBeVisible();
  await expect(page.getByLabel("NeevScore 68 out of 100, Moderate risk")).toBeVisible();
  await expect(page.getByRole("alert").filter({ hasText: "Hard stop" })).toHaveCount(0);

  const chips = page.getByRole("button", { name: /^R\d\d:/ });
  await expect(chips).toHaveCount(4);
  await expect(chips.nth(0)).toContainText("R05");
  // Data that could not be read is listed last, and costs nothing.
  await expect(chips.nth(3)).toContainText("R12");
  await expect(chips.nth(3)).toContainText("Not read");
});

test("each pillar shows its weight and cost", async ({ page }) => {
  await page.goto(REPORT);

  const bars = page.getByRole("meter");
  await expect(bars).toHaveCount(7); // six pillars and the confidence meter
  await expect(page.getByText("Weight 30%")).toBeVisible();
  await expect(page.getByText("Weight 5%").first()).toBeVisible();
});

test("a reason chip opens the evidence ledger on its own records, from the keyboard", async ({ page }) => {
  await page.goto(REPORT);

  const chip = page.getByRole("button", { name: /^R13:/ });
  await chip.focus();
  await page.keyboard.press("Enter");

  const ledger = page.getByRole("dialog", { name: "Evidence ledger" });
  await expect(ledger).toBeVisible();
  const rows = ledger.getByRole("listitem");
  await expect(rows).toHaveCount(1);
  await expect(rows.first()).toContainText("group projects read on UP-RERA");
  await expect(rows.first()).toContainText("R13");
  await expect(rows.first().getByRole("link", { name: "Open the source page" })).toHaveAttribute("href", /^https:\/\//);
  // The excerpt and the read time are part of every claim.
  await expect(rows.first().locator("blockquote")).not.toBeEmpty();
  await expect(rows.first()).toContainText(/read \d\d \w{3} 2026/);

  expect(await violations(page)).toEqual([]);

  await page.keyboard.press("Escape");
  await expect(ledger).toBeHidden();
  await expect(chip).toBeFocused();
});

test("the ledger lists every record and can be narrowed by code", async ({ page }) => {
  await page.goto(REPORT);

  await page.getByRole("button", { name: "Open evidence ledger" }).click();
  const ledger = page.getByRole("dialog", { name: "Evidence ledger" });
  const all = await ledger.getByRole("listitem").count();
  expect(all).toBeGreaterThan(10);

  await ledger.getByRole("button", { name: "R11" }).click();
  await expect(ledger.getByRole("listitem")).toHaveCount(3);
  await expect(ledger.getByRole("button", { name: "R11" })).toHaveAttribute("aria-pressed", "true");
});

test("the credit header is in Hindi", async ({ page }) => {
  await page.context().addCookies([{ name: "neevcheck-lang", value: "hi", url: "http://localhost:3010" }]);
  await page.goto(REPORT);

  await expect(page.getByRole("img", { name: "नींवस्कोर 900 में से 621, निगरानी रखें" })).toBeVisible();
  await expect(page.getByText("क्लासिक स्कोर (0–100)")).toBeVisible();
  await expect(page.getByRole("button", { name: /^R13:/ })).toContainText("उसी समूह के अन्य प्रोजेक्ट देरी में");
  await page.getByRole("button", { name: "प्रमाण बही खोलें" }).click();
  await expect(page.getByRole("dialog", { name: "प्रमाण बही" })).toBeVisible();
  expect(await violations(page)).toEqual([]);
});

test.describe("on a phone", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("the credit header and the ledger fit the screen", async ({ page }) => {
    await page.goto(REPORT);
    await expect(page.getByRole("img", { name: /NeevScore 621/ })).toBeVisible();
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(0);

    await page.getByRole("button", { name: "Open evidence ledger" }).click();
    const box = await page.getByRole("dialog", { name: "Evidence ledger" }).boundingBox();
    expect(box && Math.round(box.width)).toBeLessThanOrEqual(390);
  });
});
