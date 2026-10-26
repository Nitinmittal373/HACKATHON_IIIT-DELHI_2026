import { expect, test, type Page } from "@playwright/test";

const CHECK_URL = /\/check\/[0-9a-f]{32}$/;

test.beforeEach(async ({ page }) => {
  // The recorded stream names a live-view address; give the frame something harmless to load.
  await page.route("https://live.tinyfish.example/**", (route) =>
    route.fulfill({ contentType: "text/html", body: "<p>live view</p>" }),
  );
});

async function startCheck(page: Page) {
  await page.goto("/check?q=Supertech%20Eco%20Village");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "We found 2 projects for “Supertech Eco Village”",
  );
  await page.getByRole("button", { name: "Yes, check this project" }).click();
  await expect(page).toHaveURL(CHECK_URL);
}

test("search, confirm, live check and report show the recorded score", async ({ page }) => {
  const problems: string[] = [];
  page.on("console", (message) => message.type() === "error" && problems.push(message.text()));

  await startCheck(page);

  await expect(page.getByRole("heading", { name: "Findings so far" })).toBeVisible();
  await expect(page.getByText("11 records")).toBeVisible();
  await expect(page.getByText("NeevScore 741 · Watch")).toBeVisible();
  // The CAPTCHA source stopped, and says so instead of guessing.
  await page.getByRole("button", { name: /Consumer cases/ }).click();
  await expect(page.getByText(/Agent stopped: this page asks for a CAPTCHA/)).toBeVisible();

  await page.getByRole("link", { name: "See report" }).click();
  await expect(page).toHaveURL(/\/report\/[0-9a-f]{32}$/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("SUPERTECH ECO VILLAGE-I PHASE I-C");
  await expect(page.getByRole("img", { name: "NeevScore 621 out of 900, Watch" })).toBeVisible();
  await expect(page.getByText("5 of 7 key checks read")).toBeVisible();
  await expect(page.getByText("Consumer cases: Not read")).toBeVisible();
  await expect(page.getByRole("link", { name: "How to check this yourself" }).first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Do this before paying more" })).toBeVisible();
  await expect(page.getByRole("listitem").filter({ hasText: "Pay only to the RERA collection account" })).toBeVisible();

  expect(problems).toEqual([]);
});

test("the confirm list and its buttons work from the keyboard", async ({ page }) => {
  await page.goto("/check?q=Supertech%20Eco%20Village");
  const rows = page.getByRole("radio");
  await rows.first().focus();
  await expect(rows.first()).toBeChecked();
  await page.keyboard.press("ArrowDown");
  await expect(rows.nth(1)).toBeChecked();

  await page.keyboard.press("Tab");
  const yes = page.getByRole("button", { name: "Yes, check this project" });
  await expect(yes).toBeFocused();
  const outline = await yes.evaluate((el) => getComputedStyle(el).outlineStyle);
  expect(outline).not.toBe("none");
});

test("an unknown project gets a friendly answer with tips", async ({ page }) => {
  await page.goto("/check?q=nothing%20here");
  await expect(page.getByRole("heading", { name: "No UP-RERA project found" })).toBeVisible();
  await expect(page.getByText(/Search by the UP-RERA number/)).toBeVisible();
});

test("a rate-limited visitor sees how long to wait", async ({ page }) => {
  await page.goto("/check?q=Supertech%20Eco%20Village");
  await page.getByRole("radio").nth(1).check({ force: true });
  await page.getByRole("button", { name: "Yes, check this project" }).click();
  await expect(page.locator("section[role=alert]")).toContainText("try again in 30 seconds");
});

test.describe("on a phone", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("the browser window sits above the findings and nothing overflows sideways", async ({ page }) => {
    await startCheck(page);
    await expect(page.getByText("NeevScore 741 · Watch")).toBeVisible();
    const browser = await page.getByRole("region", { name: /./ }).first().boundingBox();
    const findings = await page.getByRole("region", { name: "Findings so far" }).boundingBox();
    expect(browser && findings && browser.y < findings.y).toBe(true);

    await page.goto(page.url().replace("/check/", "/report/"));
    await expect(page.getByRole("heading", { name: "Evidence" })).toBeVisible();
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(0);
  });
});

test("an unknown check or report says so calmly", async ({ page }) => {
  for (const path of ["/report/" + "b".repeat(32), "/check/" + "b".repeat(32), "/report/not-an-id", "/nowhere"]) {
    await page.goto(path);
    await expect(page.getByRole("heading", { name: "We could not find this page" })).toBeVisible();
  }
});
