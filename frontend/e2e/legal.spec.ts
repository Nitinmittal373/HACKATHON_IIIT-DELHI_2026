import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import { signInAsAsha } from "./signedIn";

const API = "http://localhost:8010";
const REPORT = "/report/4ad9752355f9455aa9d242c93950ea04";
const CORS = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "Content-Type" };

test("a reader can send a correction about one finding", async ({ page }) => {
  let sent: Record<string, unknown> | null = null;
  await page.route(`${API}/api/corrections`, async (route) => {
    if (route.request().method() === "OPTIONS") return route.fulfill({ status: 204, headers: CORS });
    sent = route.request().postDataJSON();
    return route.fulfill({ status: 201, contentType: "application/json", headers: CORS, body: '{"id":"c1"}' });
  });
  await page.goto(REPORT);

  await page.getByRole("button", { name: "Report a mistake" }).click();
  await page.getByRole("button", { name: "Send correction" }).click();
  await expect(page.getByRole("alert").filter({ hasText: "Please write" })).toBeVisible();

  await page.getByLabel("Which finding is it about? (optional)").selectOption({ index: 1 });
  await page.getByLabel("What is wrong, and what do the records say?").fill("The date on the page differs.");
  await page.getByRole("button", { name: "Send correction" }).click();

  await expect(page.getByRole("status").filter({ hasText: "Thank you" })).toBeVisible();
  expect(sent).toMatchObject({ message: "The date on the page differs." });
  expect(sent).toHaveProperty("report_id", "4ad9752355f9455aa9d242c93950ea04");
  expect(sent).toHaveProperty("finding_id");
});

test("the rating notice is on the report and the QR code appears only in print", async ({ page }) => {
  await page.goto(REPORT);
  await expect(page.getByText("Risk indicator based on public records — not a credit rating.")).toBeVisible();

  const qr = page.getByRole("img", { name: "QR code linking to the live report" });
  await expect(qr).toBeHidden();
  await page.emulateMedia({ media: "print" });
  await expect(qr).toBeVisible();
  await expect(page.getByText("Scan to open the live report")).toBeVisible();
});

test("the watch dialog makes no email promise while mail is off", async ({ page }) => {
  await signInAsAsha(page);
  await page.goto(REPORT);
  await page.getByRole("button", { name: "Watch with Sentinel" }).first().click();
  await expect(page.getByText("You can stop watching at any time.").first()).toBeVisible();
  await expect(page.getByText("We use your email only to send alerts about this project.")).toHaveCount(0);
});

test("the correction form has no accessibility violations, in Hindi too", async ({ page, context }) => {
  await context.addCookies([{ name: "neevcheck-lang", value: "hi", url: "http://localhost:3000" }]);
  await page.goto(REPORT);
  await page.getByRole("button", { name: "गलती बताएँ" }).click();
  const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  expect(result.violations.map((v) => v.id)).toEqual([]);
});

test("a plain-language summary is built from the reason codes", async ({ page }) => {
  await page.goto(REPORT);
  await expect(page.getByText(/^Scored \d+ out of 900 \(.+\)\. The biggest reasons: /)).toBeVisible();
});
