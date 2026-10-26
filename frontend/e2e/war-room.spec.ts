import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const CHECK_URL = /\/check\/[0-9a-f]{32}$/;

test.beforeEach(async ({ page }) => {
  await page.route("https://live.tinyfish.example/**", (route) =>
    route.fulfill({ contentType: "text/html", body: "<p>live view</p>" }),
  );
});

async function startCheck(page: Page) {
  await page.goto("/check?q=Supertech%20Eco%20Village");
  await page.getByRole("button", { name: "Yes, check this project" }).click();
  await expect(page).toHaveURL(CHECK_URL);
  await expect(page.getByText("NeevScore 741 · Watch")).toBeVisible();
}

test("the War Room shows six lanes with an honest status each", async ({ page }) => {
  await startCheck(page);

  const room = page.getByRole("region", { name: "War Room" });
  await expect(room.getByRole("listitem")).toHaveCount(6);
  await expect(room.getByRole("button", { name: /^UP-RERA/ })).toContainText("Done");
  // One half of this lane was read and the other stopped at a CAPTCHA; it must not say "Done".
  await expect(room.getByRole("button", { name: /^Insolvency and court cases/ })).toContainText("Partly read");
  // The recorded check ran without the v2 sources, so this lane says so instead of waiting forever.
  await expect(room.getByRole("button", { name: /^Group companies/ })).toContainText("Not in this check");
  await expect(room.getByRole("button", { name: /^UP-RERA/ })).toContainText(/\d+ findings?/);
});

test("opening a lane puts it in the big browser view", async ({ page }) => {
  await startCheck(page);

  const room = page.getByRole("region", { name: "War Room" });
  await room.getByRole("button", { name: /^Land authority/ }).click();

  await expect(room.getByRole("button", { name: /^Land authority/ })).toHaveAttribute("aria-pressed", "true");
  await expect(room.getByRole("button", { name: /^Land authority/ })).toContainText("Shown in the big view");
  await expect(page.getByRole("region", { name: "Land authority", exact: true })).toBeVisible();
});

test("a lane can be opened from the keyboard", async ({ page }) => {
  await startCheck(page);

  const lane = page.getByRole("region", { name: "War Room" }).getByRole("button", { name: /^News and lenders/ });
  await lane.focus();
  await page.keyboard.press("Enter");

  await expect(lane).toHaveAttribute("aria-pressed", "true");
});

test("the War Room is in Hindi and has no accessibility violations", async ({ page }) => {
  await page.context().addCookies([{ name: "neevcheck-lang", value: "hi", url: "http://localhost:3010" }]);
  await page.goto("/check?q=Supertech%20Eco%20Village");
  await page.getByRole("button", { name: "हाँ, इस प्रोजेक्ट को जाँचें" }).click();
  await expect(page).toHaveURL(CHECK_URL);

  const room = page.getByRole("region", { name: "वॉर रूम" });
  await expect(room.getByRole("listitem")).toHaveCount(6);
  await expect(room.getByRole("button", { name: /^समूह की कंपनियाँ/ })).toContainText("इस जाँच में नहीं");

  await page.waitForTimeout(4500);
  const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  expect(result.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join(" | ")}`)).toEqual([]);
});

test.describe("on a phone", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("the lanes fit without sideways scrolling", async ({ page }) => {
    await startCheck(page);
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(0);
  });
});
