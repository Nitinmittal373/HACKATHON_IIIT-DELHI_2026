import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const REPORT = "/report/4ad9752355f9455aa9d242c93950ea04";

test("one click builds an editable draft with annexures and the not-legal-advice banner", async ({ page }) => {
  await page.goto(REPORT);
  await page.getByRole("button", { name: "Draft a UP-RERA complaint" }).click();

  await expect(page.getByRole("note")).toHaveText("Draft for you to review and file. Not legal advice.");
  const draft = page.getByLabel("Complaint draft (you can edit it)");
  await expect(draft).toContainText("UPRERAPRJ8334");
  await expect(draft).toContainText("Annexures");
  await expect(draft).toContainText("https://");

  await draft.fill("My edited complaint");
  await expect(draft).toHaveValue("My edited complaint");
  await expect(page.getByRole("link", { name: "Open the UP-RERA site to file" })).toHaveAttribute(
    "href",
    /up-rera\.in/,
  );
  await expect(page.getByRole("button", { name: "Print or save as PDF" })).toBeVisible();

  const violations = (await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations;
  expect(violations.map((v) => v.id)).toEqual([]);
});

test("the draft is written in Hindi when the language is Hindi", async ({ page, context }) => {
  await context.addCookies([{ name: "neevcheck-lang", value: "hi", url: "http://localhost:3000" }]);
  await page.goto(REPORT);
  await page.getByRole("button", { name: "UP-RERA शिकायत का मसौदा बनाएँ" }).click();
  await expect(page.getByRole("note")).toContainText("कानूनी सलाह नहीं");
  await expect(page.getByRole("textbox")).toContainText("अनुलग्नक");
});
