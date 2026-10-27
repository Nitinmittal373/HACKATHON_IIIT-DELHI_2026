import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const API = "http://localhost:8010";
const CORS = { "Access-Control-Allow-Origin": "*" };

function answer(page: Page, path: string, body: unknown, status = 200) {
  return page.route(`${API}${path}**`, (route) =>
    route.fulfill({ status, contentType: "application/json", headers: CORS, body: JSON.stringify(body) }),
  );
}

const MYWOODS = (rera_id: string, status: string, sources: string[]) => ({
  rera_id,
  name: "Mahagun Mywoods",
  promoter: null,
  registered_on: null,
  district: null,
  details_url: "https://www.up-rera.in/Frm_View_Project_Details.aspx?id=3330",
  status,
  sources,
  found_in: null,
});

test("a project only listing sites print says so, with where it was seen", async ({ page }) => {
  await answer(page, "/api/projects/search", {
    query: "Mahagun Mywoods",
    candidates: [
      MYWOODS("UPRERAPRJ3330", "confirmed", ["up-rera.in", "mahagunindia.com"]),
      MYWOODS("UPRERAPRJ3331", "listings_only", ["mahagunindia.com", "housing.com"]),
    ],
    outside_up: false,
    order_leads: [],
  });
  await page.goto("/check?q=Mahagun%20Mywoods");
  await expect(page.getByText("On UP-RERA")).toBeVisible();
  await expect(page.getByText("Seen on builder and listing sites")).toBeVisible();
  await expect(page.getByText("Seen on: mahagunindia.com, housing.com")).toBeVisible();
});

test("a number of another state gets one calm line and no list of states", async ({ page }) => {
  await page.goto("/check?q=P51800000937");
  const message =
    "NeevCheck covers Uttar Pradesh RERA projects for now. Check this project on its own state's RERA website.";
  await expect(page.getByRole("heading", { name: message })).toBeVisible();
  await expect(page.getByRole("button", { name: "Yes, check this project" })).toHaveCount(0);
  await expect(page.getByText(/Maharashtra|Karnataka|Haryana|coverage/i)).toHaveCount(0);
});

test("a builder search lists registered projects and company pages", async ({ page }) => {
  await answer(page, "/api/promoters/search", {
    query: "Mahagun India",
    companies: [
      {
        name: "MAHAGUN INDIA PRIVATE LIMITED",
        cin: "U45201DL1997PTC084715",
        source_url: "https://www.zaubacorp.com/MAHAGUN-INDIA-PRIVATE-LIMITED",
      },
    ],
    projects: [MYWOODS("UPRERAPRJ3330", "confirmed", ["up-rera.in"])],
    outside_up: false,
  });
  await page.goto("/check?builder=Mahagun%20India");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Registered projects found for “Mahagun India”");
  await expect(page.getByText("U45201DL1997PTC084715")).toBeVisible();
  await expect(page.getByText("Different companies of one group are different legal entities.")).toBeVisible();
});

test("the more-ways panel works with the keyboard and reads a brochure", async ({ page }) => {
  await answer(page, "/api/extract", {
    source: "your document",
    numbers: [{ rera_id: "UPRERAPRJ3330", line: "UP-RERA Reg. No. UPRERAPRJ3330 | [removed]" }],
    candidates: [MYWOODS("UPRERAPRJ3330", "from_document", ["your document"])],
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
  await expect(page.getByText(/UP-RERA Reg\. No\. UPRERAPRJ3330/)).toBeVisible();
  await page.getByRole("button", { name: "Use this number" }).click();
  await expect(page).toHaveURL(/\/check\?q=UPRERAPRJ3330$/);
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
    outside_up: false,
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
