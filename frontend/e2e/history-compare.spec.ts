import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { expect, test, type Page } from "@playwright/test";

const API = "http://localhost:8010";
const FIXTURES = resolve(__dirname, "fixtures");
const ECO = "4ad9752355f9455aa9d242c93950ea04";
const AVENUE = (JSON.parse(readFileSync(resolve(FIXTURES, "summary-6742.json"), "utf-8")) as { id: string }).id;

async function remember(page: Page, ids: string[]) {
  await page.addInitScript((saved) => localStorage.setItem("neevcheck-reports", JSON.stringify(saved)), ids);
}

test.describe("home", () => {
  test("the hero card and the strip show the latest real check", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("link", { name: /Latest NeevCheck report: SUPERTECH ECO VILLAGE-I PHASE I-C/ })).toBeVisible();
    const strip = page.getByRole("region", { name: "Recently checked on NeevCheck" });
    await expect(strip.getByRole("link", { name: /NeevScore 68, Moderate risk/ })).toHaveAttribute("href", `/report/${ECO}`);
  });

  test("before any check has finished: an empty card, no numbers, no strip", async ({ page }) => {
    await page.route(`${API}/api/checks/recent`, (route) =>
      route.fulfill({ contentType: "application/json", headers: { "Access-Control-Allow-Origin": "*" }, body: "[]" }),
    );
    await page.goto("/");
    await expect(page.getByLabel("Placeholder for your report")).toContainText("Your report appears here");
    await expect(page.getByText("Recently checked on NeevCheck")).toHaveCount(0);
  });

  test("the construction skyline is drawn behind the hero", async ({ page }) => {
    await page.goto("/");
    const skyline = page.locator("section svg[viewBox='0 0 1440 440']").first();
    await expect(skyline).toBeVisible();
    expect((await skyline.boundingBox())?.height).toBeGreaterThan(200);
  });

  test("the header leads to My reports", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: "My reports" }).click();
    await expect(page).toHaveURL(/\/reports$/);
  });
});

test.describe("My reports", () => {
  test("with nothing saved: an empty state with the search bar", async ({ page }) => {
    await page.goto("/reports");
    await expect(page.getByRole("heading", { name: "No reports yet" })).toBeVisible();
    await expect(page.getByRole("search")).toBeVisible();
  });

  test("saved checks are listed; two can be compared; one can be removed", async ({ page }) => {
    await remember(page, [ECO, AVENUE]);
    await page.goto("/reports");
    const eco = page.getByRole("article", { name: "SUPERTECH ECO VILLAGE-I PHASE I-C" });
    await expect(eco).toContainText("UPRERAPRJ8334");
    await expect(eco).toContainText("Moderate risk");
    await expect(eco.getByRole("link", { name: "Open" })).toHaveAttribute("href", `/report/${ECO}`);

    await eco.getByRole("button", { name: "Compare" }).click();
    await page.getByRole("article", { name: /14th Avenue/ }).getByRole("button", { name: "Compare" }).click();
    await page.getByRole("link", { name: "Compare projects" }).click();
    await expect(page).toHaveURL(/\/compare\?ids=/);
    await expect(page.getByRole("heading", { name: "Compare projects" })).toBeVisible();

    await page.goto("/reports");
    await page.getByRole("article", { name: /14th Avenue/ }).getByRole("button", { name: "Remove" }).click();
    await expect(page.getByRole("article")).toHaveCount(1);
  });

  test("a check started from the confirm step is saved", async ({ page }) => {
    await page.route("https://live.tinyfish.example/**", (route) => route.fulfill({ body: "<p>live</p>" }));
    await page.goto("/check?q=Supertech%20Eco%20Village");
    await page.getByRole("button", { name: "Yes, check this project" }).click();
    await expect(page).toHaveURL(/\/check\/[0-9a-f]{32}$/);
    const saved = await page.evaluate(() => localStorage.getItem("neevcheck-reports"));
    expect(JSON.parse(saved ?? "[]")).toContain(ECO);
  });
});

test.describe("Compare", () => {
  test("rows come from the records and nothing is ranked on thin evidence", async ({ page }) => {
    await page.goto(`/compare?ids=${ECO},${AVENUE}`);
    await expect(page.getByRole("status").filter({ hasText: "not enough evidence to rank" })).toBeVisible();
    const table = page.getByRole("table", { name: "Comparison of the selected projects" });
    await expect(table.getByRole("row", { name: /^Months past the completion date/ })).toContainText("105 months");
    await expect(table.getByRole("row", { name: /^UP-RERA complaints on the promoter/ })).toContainText("2,803");
    // Never read for 6742, so it says so instead of looking clean.
    await expect(table.getByRole("row", { name: /^Company status/ })).toContainText("Not read");
  });

  test("on a phone the columns become cards with a switcher", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`/compare?ids=${ECO},${AVENUE}`);
    const switcher = page.getByRole("navigation", { name: "Jump to a project" });
    await expect(switcher.getByRole("link")).toHaveCount(2);
    await expect(page.getByRole("region", { name: "SUPERTECH ECO VILLAGE-I PHASE I-C" })).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(0);
  });

  test("Add to compare on a report puts it in the tray", async ({ page }) => {
    await page.goto(`/report/${ECO}`);
    await page.getByRole("button", { name: "Add to compare" }).click();
    await expect(page.getByText("Added. Pick one more project to compare.")).toBeVisible();
  });
});

test.describe("report extras", () => {
  test("questions, the builder's other projects and WhatsApp sharing", async ({ page, context }) => {
    await context.route("https://wa.me/**", (route) => route.fulfill({ body: "<p>whatsapp</p>" }));
    await page.goto(`/report/${ECO}`);

    const questions = page.getByRole("region", { name: "Questions to ask the builder" });
    await expect(questions.getByRole("listitem")).toHaveCount(5);
    await expect(questions.getByRole("listitem").last()).toContainText("RERA collection account");

    const track = page.getByRole("region", { name: "Other UP-RERA projects by SUPERTECH LIMITED" });
    await expect(track.getByRole("link", { name: /^Check / }).first()).toHaveAttribute("href", /\/check\?q=UPRERAPRJ/);

    const popup = page.waitForEvent("popup");
    await page.getByRole("button", { name: "Share on WhatsApp" }).click();
    const url = decodeURIComponent((await popup).url());
    expect(url).toContain("NeevCheck: SUPERTECH ECO VILLAGE-I PHASE I-C scored 68/100 (Moderate risk)");
    expect(url).toContain(`/report/${ECO}`);
  });

  test("a report says when its records were read", async ({ page }) => {
    await page.goto(`/report/${ECO}`);
    await expect(page.getByText("Records read on 25 Oct 2026")).toBeVisible();
  });
});
