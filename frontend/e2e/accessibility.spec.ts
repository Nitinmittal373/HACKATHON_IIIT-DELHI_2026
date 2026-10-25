import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const REPORT = "/report/4ad9752355f9455aa9d242c93950ea04";

async function violations(page: Page) {
  const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  return result.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join(" | ")}`);
}

const SCREENS: [string, string][] = [
  ["home", "/"],
  ["confirm", "/check?q=Supertech%20Eco%20Village"],
  ["no result", "/check?q=nothing"],
  ["report", REPORT],
  ["alerts", "/alerts"],
];

for (const [name, path] of SCREENS) {
  test(`${name} has no accessibility violations`, async ({ page }) => {
    await page.goto(path);
    // Entrance animations pass through low-contrast frames; check the settled page.
    await page.waitForTimeout(4500);
    expect(await violations(page)).toEqual([]);
  });
}

test("the live check has no accessibility violations once it has finished", async ({ page }) => {
  await page.route("https://live.tinyfish.example/**", (route) =>
    route.fulfill({ contentType: "text/html", body: "<p>live view</p>" }),
  );
  await page.goto("/check?q=Supertech%20Eco%20Village");
  await page.getByRole("button", { name: "Yes, check this project" }).click();
  await expect(page.getByText("NeevScore 68 · Moderate risk")).toBeVisible();
  await page.waitForTimeout(1500);
  expect(await violations(page)).toEqual([]);
});

test("the Hindi report has no accessibility violations", async ({ page, context }) => {
  await context.addCookies([{ name: "neevcheck-lang", value: "hi", url: "http://localhost:3010" }]);
  await page.goto(REPORT);
  await page.waitForTimeout(2500);
  expect(await violations(page)).toEqual([]);
});
