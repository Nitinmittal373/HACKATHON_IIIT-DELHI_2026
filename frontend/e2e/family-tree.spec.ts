import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const REPORT = "/report/4ad9752355f9455aa9d242c93950ea04";
const FLAGGED = "/report/" + "f".repeat(32);

async function violations(page: Page) {
  const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  return result.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join(" | ")}`);
}

const tree = (page: Page) => page.getByRole("region", { name: "Builder family tree" });

test("the tree shows the promoter, directors by name and DIN, related companies and projects", async ({ page }) => {
  await page.goto(REPORT);

  const diagram = tree(page).getByRole("group", { name: /Family tree diagram/ });
  await expect(diagram.getByRole("button", { name: /^Promoter: SUPERTECH LIMITED/ })).toBeVisible();
  await expect(diagram.getByRole("button", { name: /^Director:/ })).toHaveCount(6);
  await expect(diagram.getByRole("button", { name: /^Related company:/ })).toHaveCount(8);
  await expect(diagram.getByRole("button", { name: /^UP-RERA project:/ }).first()).toBeVisible();
  // A director is a name and a DIN: no other personal data is drawn.
  await expect(diagram.getByText(/^DIN \d{8}$/).first()).toBeVisible();
});

test("nodes can be reached and opened from the keyboard, and the details panel follows", async ({ page }) => {
  await page.goto(REPORT);

  const node = tree(page).getByRole("button", { name: /^Related company: SUPERTECH REALTORS/ });
  await node.focus();
  await expect(node).toBeFocused();
  await page.keyboard.press("Enter");

  await expect(node).toHaveAttribute("aria-pressed", "true");
  const details = tree(page).getByRole("complementary");
  await expect(details).toContainText("SUPERTECH REALTORS PRIVATE LIMITED");
  await expect(details).toContainText("Registry status: Active");
  await expect(details).toContainText("does not say which director links");
  await expect(details.getByRole("link", { name: /Open the page this came from/ })).toHaveAttribute(
    "href",
    /^https:\/\//,
  );

  const outline = await node.evaluate((el) => getComputedStyle(el.querySelector("rect")!).strokeWidth);
  expect(parseFloat(outline)).toBeGreaterThanOrEqual(3);
});

test("a delayed project is labelled in words, not only by its outline", async ({ page }) => {
  await page.goto(REPORT);

  await expect(
    tree(page).getByRole("button", { name: /UP-RERA project: Supertech Upcountry.*Delayed over 12 months/ }),
  ).toBeVisible();
});

test("insolvent, struck-off and lapsed nodes carry a red outline and a text label", async ({ page }) => {
  await page.goto(FLAGGED);

  const company = tree(page).getByRole("button", { name: /^Related company: DAZZLE.*In insolvency/ });
  await expect(company).toBeVisible();
  await expect(company.locator("text").nth(1)).toHaveText("In insolvency");
  const stroke = await company.evaluate((el) => getComputedStyle(el.querySelector("rect")!).stroke);
  expect(stroke).toBe("rgb(180, 35, 24)");

  const lapsed = tree(page).getByRole("group").getByRole("button", { name: /Registration lapsed/ });
  await expect(lapsed).toHaveCount(1);
  const lapsedStroke = await lapsed.evaluate((el) => getComputedStyle(el.querySelector("rect")!).stroke);
  expect(lapsedStroke).toBe("rgb(180, 35, 24)");
});

test("the list view says the same thing and works without the diagram", async ({ page }) => {
  await page.goto(FLAGGED);

  const list = tree(page).getByRole("region", { name: "Related companies" });
  await expect(list.getByRole("button")).toHaveCount(8);
  await expect(list.getByRole("button", { name: /DAZZLE/ })).toContainText("In insolvency");
  await list.getByRole("button", { name: /DAZZLE/ }).click();
  await expect(tree(page).getByRole("complementary")).toContainText("In insolvency");
});

test("the tree is in Hindi and has no accessibility violations", async ({ page }) => {
  await page.context().addCookies([{ name: "neevcheck-lang", value: "hi", url: "http://localhost:3010" }]);
  await page.goto(FLAGGED);

  const hindi = page.getByRole("region", { name: "बिल्डर का पारिवारिक वृक्ष" });
  await expect(hindi).toBeVisible();
  await expect(hindi.getByRole("button", { name: /^संबंधित कंपनी: DAZZLE.*दिवाला प्रक्रिया में/ })).toBeVisible();
  await page.waitForTimeout(2500);
  expect(await violations(page)).toEqual([]);
});

test.describe("on a phone", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("the list replaces the diagram and nothing overflows", async ({ page }) => {
    await page.goto(REPORT);

    await expect(tree(page).getByRole("group", { name: /Family tree diagram/ })).toBeHidden();
    await expect(tree(page).getByRole("region", { name: "Directors (name and DIN)" })).toBeVisible();
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(0);
  });
});
