import { expect, test } from "@playwright/test";

import { signInAsAsha } from "./signedIn";

const HI = { name: "neevcheck-lang", value: "hi", url: "http://localhost:3010" };

test.describe("the home page", () => {
  test("is the hero and its search, and nothing else but a short footer", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { level: 1 })).toContainText("Know your builder before you book.");
    await expect(page.getByRole("search")).toBeVisible();
    await expect(page.getByText("More ways to find it")).toBeVisible();
    await expect(page.getByRole("link", { name: "Supertech", exact: true })).toBeVisible();
    // The sections that used to scroll below the hero now have their own pages.
    for (const heading of ["Questions, answered", "We keep watching after you book", "The problem"]) {
      await expect(page.getByText(heading)).toHaveCount(0);
    }
    expect(await page.locator("main h2").count()).toBeLessThanOrEqual(1);
  });

  test("says Uttar Pradesh in the line under the headline, not in a pill above it", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("For homebuyers in Uttar Pradesh.")).toBeVisible();
    await expect(page.getByText("Built for homebuyers in Uttar Pradesh")).toHaveCount(0);
  });

  test("has a footer with a link to every page", async ({ page }) => {
    await page.goto("/");
    const footer = page.getByRole("contentinfo");
    for (const [name, href] of [
      ["Check a project", "/check"],
      ["How it works", "/how-it-works"],
      ["For RWAs", "/rwa"],
      ["Alerts", "/alerts"],
      ["Privacy", "/privacy"],
    ] as const) {
      await expect(footer.getByRole("link", { name })).toHaveAttribute("href", href);
    }
  });

  test("sends the old section links to the new pages", async ({ page }) => {
    for (const [from, to] of [
      ["/#search", "/check"],
      ["/#how-it-works", "/how-it-works"],
      ["/#sentinel", "/rwa"],
    ] as const) {
      await page.goto(from);
      await expect(page).toHaveURL(new RegExp(`${to}$`));
    }
  });
});

test.describe("the header", () => {
  test("links to the pages and marks the current one", async ({ page }) => {
    await page.goto("/how-it-works");
    const nav = page.getByRole("navigation", { name: "Main" });
    await expect(nav.getByRole("link", { name: "How it works" })).toHaveAttribute("aria-current", "page");
    await expect(nav.getByRole("link", { name: "For RWAs" })).not.toHaveAttribute("aria-current", "page");
    await expect(nav.getByRole("link", { name: "Check a project" })).toHaveAttribute("href", "/check");
    await expect(nav.getByRole("link", { name: "For RWAs" })).toHaveAttribute("href", "/rwa");
    await nav.getByRole("link", { name: "For RWAs" }).click();
    await expect(page).toHaveURL(/\/rwa$/);
    await expect(nav.getByRole("link", { name: "For RWAs" })).toHaveAttribute("aria-current", "page");
  });

  test("keeps Check a project active on the live check too", async ({ page }) => {
    await page.goto("/check?q=Supertech%20Eco%20Village");
    await expect(page.getByRole("navigation", { name: "Main" }).getByRole("link", { name: "Check a project" })).toHaveAttribute(
      "aria-current",
      "page",
    );
  });
});

test.describe("Check a project", () => {
  test("has its own title and description, the search, the gallery and what a check costs", async ({ page }) => {
    await page.goto("/check");
    await expect(page).toHaveTitle("Check a project · NeevCheck");
    await expect(page.locator('meta[name="description"]')).toHaveAttribute("content", /Search a UP-RERA project/);
    await expect(page.getByRole("heading", { level: 1, name: "Check a project" })).toBeVisible();
    await expect(page.getByRole("search")).toBeVisible();
    await expect(page.getByText("More ways to find it", { exact: true })).toBeVisible();

    const gallery = page.getByRole("region", { name: "Recently checked famous projects" });
    await expect(gallery.getByRole("link", { name: /SUPERTECH ECO VILLAGE/i })).toHaveAttribute("href", /\/report\/[0-9a-f]{32}$/);
    await expect(gallery.getByText(/^Read /)).toBeVisible();

    await expect(page.getByRole("heading", { name: "What a check reads" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "What a check costs" })).toBeVisible();
    await expect(page.getByText(/checked less than 7 days ago, you get that report at no cost/)).toBeVisible();
  });

  test("shows the gallery only from saved checks, so an empty list shows nothing", async ({ page }) => {
    await page.route("http://localhost:8010/api/featured", (route) =>
      route.fulfill({ headers: { "Access-Control-Allow-Origin": "*" }, contentType: "application/json", body: "[]" }),
    );
    await page.goto("/check");
    await expect(page.getByRole("heading", { name: "What a check reads" })).toBeVisible();
    await expect(page.getByText("Recently checked famous projects")).toHaveCount(0);
  });

  test("keeps the search results at /check?q=", async ({ page }) => {
    await page.goto("/check?q=Supertech%20Eco%20Village");
    await expect(page.getByRole("button", { name: "Yes, check this project" })).toBeVisible();
  });
});

test.describe("How it works", () => {
  test("lists the steps, the pillars with their weights, the scale and the sources", async ({ page }) => {
    await page.goto("/how-it-works");
    await expect(page).toHaveTitle("How it works · NeevCheck");
    await expect(page.locator('meta[name="description"]')).toHaveAttribute("content", /300 to 900/);
    await expect(page.getByRole("heading", { level: 1, name: "How NeevCheck works" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "The steps" })).toBeVisible();

    const pillars = page.getByRole("region", { name: "Six pillars and their weights" });
    await expect(pillars.getByRole("listitem")).toHaveCount(6);
    await expect(pillars.getByText("Regulatory compliance (RERA)")).toBeVisible();
    await expect(pillars.getByText("30%")).toBeVisible();

    const scale = page.getByRole("region", { name: "The 300 to 900 scale" });
    await expect(scale.getByText("Low risk: 750 to 900")).toBeVisible();
    await expect(scale.getByText("High risk: 300 to 449")).toBeVisible();

    await expect(page.getByRole("heading", { name: "What “Not enough evidence yet” means" })).toBeVisible();
    await expect(page.getByText("Partly read (UP-RERA complaints)")).toBeVisible();

    const sources = page.getByRole("region", { name: "Where the records come from" });
    await expect(sources.getByRole("link", { name: /up-rera\.in/ })).toHaveAttribute("href", "https://www.up-rera.in/");
    await expect(sources.getByText("Behind a CAPTCHA, so not checked automatically.")).toBeVisible();

    await expect(page.getByRole("link", { name: "Privacy page" })).toHaveAttribute("href", "/privacy");
  });

  test("is in Hindi, with a Hindi title", async ({ page, context }) => {
    await context.addCookies([HI]);
    await page.goto("/how-it-works");
    await expect(page).toHaveTitle("यह कैसे काम करता है · NeevCheck");
    await expect(page.getByRole("heading", { level: 1 })).toHaveText("NeevCheck कैसे काम करता है");
    await expect(page.getByRole("link", { name: "गोपनीयता पेज" })).toHaveAttribute("href", "/privacy");
  });
});

test.describe("For RWAs", () => {
  test("explains watching, alerts and stop links, and asks a visitor to sign in", async ({ page }) => {
    await page.goto("/rwa");
    await expect(page).toHaveTitle("For RWAs · NeevCheck");
    await expect(page.getByRole("heading", { level: 1 })).toHaveText("For RWAs and residents' groups");
    await expect(page.getByText("Each alert email ends with a link that stops that watch.")).toBeVisible();
    await expect(page.getByRole("link", { name: "Sign in", exact: true }).last()).toHaveAttribute("href", /\/login\?next=/);
  });

  test("points a signed-in visitor to their alerts", async ({ page }) => {
    await signInAsAsha(page);
    await page.goto("/rwa");
    await expect(page.getByRole("link", { name: "Open Alerts" })).toHaveAttribute("href", "/alerts");
  });

  test("is in Hindi", async ({ page, context }) => {
    await context.addCookies([HI]);
    await page.goto("/rwa");
    await expect(page).toHaveTitle("RWA के लिए · NeevCheck");
    await expect(page.getByRole("heading", { level: 1 })).toContainText("RWA");
  });
});

test.describe("inner pages read from the left, at a normal width", () => {
  test.use({ viewport: { width: 1440, height: 900 } });

  for (const path of ["/check", "/how-it-works", "/rwa", "/alerts", "/privacy"]) {
    test(`${path} is left-aligned with a reading width`, async ({ page }) => {
      await page.goto(path);
      const title = page.getByRole("heading", { level: 1 });
      expect(await title.evaluate((el) => getComputedStyle(el).textAlign)).toMatch(/^(start|left)$/);
      const box = await title.boundingBox();
      expect(box?.x ?? 999).toBeLessThan(120);
      // Body text stops at about 68 characters, not at the edge of a wide screen.
      const widest = await page.locator("main p").evaluateAll((nodes) =>
        Math.max(...nodes.map((node) => node.getBoundingClientRect().width)),
      );
      expect(widest).toBeLessThanOrEqual(1000);
    });
  }
});

test("the sitemap lists every public page", async ({ request }) => {
  const response = await request.get("/sitemap.xml");
  expect(response.status()).toBe(200);
  const xml = await response.text();
  for (const path of ["/check", "/how-it-works", "/rwa", "/alerts", "/privacy", "/login"]) {
    expect(xml).toContain(`${path}</loc>`);
  }
  expect(xml).not.toContain("/report/");
});
