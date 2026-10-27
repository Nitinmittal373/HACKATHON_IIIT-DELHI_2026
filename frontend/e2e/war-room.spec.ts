import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

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
  await expect(page.getByText("NeevScore 495 · Elevated")).toBeVisible();
}

// The file may have Windows line endings; the blocks are split on blank lines below.
const EVENTS = readFileSync(resolve(__dirname, "fixtures/events.sse"), "utf-8").replaceAll("\r\n", "\n");

/** Serves the recorded event stream with some of its events changed or left out. */
async function replayWith(page: Page, change: (block: string) => string | null) {
  const body = EVENTS.trim()
    .split("\n\n")
    .map(change)
    .filter((block) => block !== null)
    .join("\n\n");
  await page.route(/\/api\/checks\/[0-9a-f]{32}\/events$/, (route) =>
    route.fulfill({
      status: 200,
      headers: { "Content-Type": "text/event-stream", "Access-Control-Allow-Origin": "*" },
      body: `${body}\n\n`,
    }),
  );
}

test("the War Room shows the lanes that ran, with an honest status each", async ({ page }) => {
  await startCheck(page);

  const room = page.getByRole("region", { name: "War Room" });
  await expect(room.getByRole("listitem")).toHaveCount(6);
  await expect(room.getByText("6 lanes read, two at a time.")).toBeVisible();
  await expect(room.getByRole("button", { name: /^UP-RERA/ })).toContainText("Done");
  // One half of this lane was read and the other stopped at a CAPTCHA; it must not say "Done".
  await expect(room.getByRole("button", { name: /^Insolvency and court cases/ })).toContainText("Partly read");
  await expect(room.getByRole("button", { name: /^Group companies/ })).toContainText("Done");
  await expect(room.getByRole("button", { name: /^UP-RERA/ })).toContainText(/\d+ findings?/);
});

test("a lane that was never started says why, and the count follows what ran", async ({ page }) => {
  // A check made before the group and lender sources existed has no events for them.
  await replayWith(page, (block) => (/"source":"(group|sarfaesi)"/.test(block) ? null : block));
  await startCheck(page);

  const room = page.getByRole("region", { name: "War Room" });
  const group = room.getByRole("button", { name: /^Group companies/ });
  await expect(group).toContainText("Not in this check");
  await expect(group).toContainText("this check was made before this source was added");
  await expect(room.getByText("5 lanes read, two at a time.")).toBeVisible();
});

test("a lane with findings is never shown as not read, and its findings are listed", async ({ page }) => {
  // The insolvency source gives up after reporting its findings; the CAPTCHA source stays stopped.
  await replayWith(page, (block) =>
    /"type":"source.completed".*"source":"insolvency"/.test(block)
      ? block.replace('"status":"completed"', '"status":"failed"')
      : block,
  );
  await startCheck(page);

  const room = page.getByRole("region", { name: "War Room" });
  const lane = room.getByRole("button", { name: /^Insolvency and court cases/ });
  await expect(lane).toContainText("Partly read");
  await expect(lane).not.toContainText("Not read");
  await lane.click();
  const window = page.getByRole("region", { name: "Insolvency", exact: true });
  await expect(window).toContainText("Read in part before it stopped");
  await expect(window).toContainText("Insolvency application against SUPERTECH LIMITED was admitted");
  await expect(window).not.toContainText("Could not be read this time");
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
  await expect(room.getByRole("button", { name: /^समूह की कंपनियाँ/ })).toContainText("पूरा");

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
