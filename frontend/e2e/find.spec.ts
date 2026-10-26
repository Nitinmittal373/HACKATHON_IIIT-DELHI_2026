import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const API = "http://localhost:8010";
const CORS = { "Access-Control-Allow-Origin": "*" };

function answer(page: Page, path: string, body: unknown, status = 200) {
  return page.route(`${API}${path}**`, (route) =>
    route.fulfill({ status, contentType: "application/json", headers: CORS, body: JSON.stringify(body) }),
  );
}

const LODHA = (rera_id: string, status: string, sources: string[]) => ({
  state: "MH",
  state_name: "Maharashtra",
  rera_name: "MahaRERA",
  rera_id,
  name: "Lodha World Towers",
  promoter: null,
  registered_on: null,
  district: null,
  details_url: "https://maharera.maharashtra.gov.in/projects-search-result",
  status,
  sources,
  found_in: null,
});

test("a project only listing sites print says so, with where it was seen", async ({ page }) => {
  await answer(page, "/api/projects/search", {
    query: "Lodha World Towers",
    candidates: [
      LODHA("P51900008345", "confirmed", ["maharera.maharashtra.gov.in", "lodhagroup.com"]),
      LODHA("P51900008962", "listings_only", ["lodhagroup.com", "housing.com"]),
    ],
    detected_state: null,
    searched_states: ["MH"],
    pre_rera: [],
    order_leads: [],
  });
  await page.goto("/check?q=Lodha%20World%20Towers");
  await expect(page.getByText("On the state portal")).toBeVisible();
  await expect(page.getByText("Seen on builder and listing sites")).toBeVisible();
  await expect(page.getByText("Seen on: lodhagroup.com, housing.com")).toBeVisible();
});

test("a project older than RERA shows the page's own words and no score", async ({ page }) => {
  await answer(page, "/api/projects/search", {
    query: "DLF The Camellias",
    candidates: [],
    detected_state: null,
    searched_states: ["HR"],
    pre_rera: [
      {
        name: "DLF Camellias",
        statement: "DLF The Camellias does not apply to RERA registration and has already been delivered.",
        source_url: "https://www.luxuryresidences.in/dlf-camellias-sector-42-gurgaon/",
      },
    ],
    order_leads: [],
  });
  await page.goto("/check?q=DLF%20The%20Camellias");
  await expect(page.getByRole("heading", { name: "This project may be older than RERA" })).toBeVisible();
  await expect(page.getByText(/does not apply to RERA registration/)).toBeVisible();
  await expect(page.getByRole("link", { name: "See this builder's projects" })).toHaveAttribute(
    "href",
    "/check?builder=DLF",
  );
  await expect(page.getByRole("button", { name: "Yes, check this project" })).toHaveCount(0);
});

test("a builder search lists registered projects and company pages", async ({ page }) => {
  await answer(page, "/api/promoters/search", {
    query: "Lodha Developers",
    state: null,
    companies: [
      {
        name: "LODHA DEVELOPERS LIMITED",
        cin: "L45200MH1995PLC093041",
        source_url: "https://www.zaubacorp.com/LODHA-DEVELOPERS-LIMITED",
      },
    ],
    projects: [LODHA("P51700020128", "confirmed", ["maharera.maharashtra.gov.in"])],
    searched_states: ["UP", "MH"],
  });
  await page.goto("/check?builder=Lodha%20Developers");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Registered projects found for “Lodha Developers”");
  await expect(page.getByText("L45200MH1995PLC093041")).toBeVisible();
  await expect(page.getByText("Different companies of one group are different legal entities.")).toBeVisible();
});

test("the more-ways panel works with the keyboard and reads a brochure", async ({ page }) => {
  await answer(page, "/api/extract", {
    source: "your document",
    numbers: [{ rera_id: "P51900008345", state: "MH", line: "MahaRERA Reg. No. P51900008345 | [removed]" }],
    candidates: [LODHA("P51900008345", "from_document", ["your document"])],
    message: null,
  });
  await page.goto("/");
  await page.getByText("More ways to find it").click();
  const tabs = page.getByRole("tab");
  await expect(tabs).toHaveCount(4);
  await tabs.first().focus();
  await page.keyboard.press("ArrowRight");
  await page.keyboard.press("ArrowRight");
  await expect(page.getByRole("tab", { name: "Upload brochure" })).toHaveAttribute("aria-selected", "true");
  await expect(page.getByText(/Photos are never uploaded/)).toBeVisible();

  await page.locator('input[type="file"]').setInputFiles({
    name: "brochure.pdf",
    mimeType: "application/pdf",
    buffer: Buffer.from("%PDF-1.4 test"),
  });
  await expect(page.getByText("Found in your document")).toBeVisible();
  await expect(page.getByText(/MahaRERA Reg\. No\. P51900008345/)).toBeVisible();
  await page.getByRole("button", { name: "Use this number" }).click();
  await expect(page).toHaveURL(/\/check\?q=P51900008345&state=MH/);
});

test("a file that is not a PDF is refused in the browser", async ({ page }) => {
  await page.goto("/");
  await page.getByText("More ways to find it").click();
  await page.getByRole("tab", { name: "Upload brochure" }).click();
  await page.locator('input[type="file"]').setInputFiles({
    name: "photo.png",
    mimeType: "image/png",
    buffer: Buffer.from("not a pdf"),
  });
  await expect(page.locator("p[role=alert]")).toContainText("Please choose a PDF");
});

test("the panel and the cards have no accessibility violations", async ({ page }) => {
  await answer(page, "/api/projects/search", {
    query: "x",
    candidates: [],
    detected_state: null,
    searched_states: ["UP"],
    pre_rera: [],
    order_leads: [],
  });
  await page.goto("/check?q=nothing%20here");
  await page.waitForTimeout(800);
  let result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  expect(result.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join(" | ")}`)).toEqual([]);

  await page.goto("/");
  await page.getByText("More ways to find it").click();
  await page.waitForTimeout(4500);
  result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  expect(result.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join(" | ")}`)).toEqual([]);
});
