import { readFileSync } from "node:fs";
import { mkdirSync } from "node:fs";
import { resolve } from "node:path";

import { expect, test, type Page } from "@playwright/test";

/**
 * Every page, in English and Hindi, at desktop and phone width: no console error, no sideways
 * scroll, no failing link, and no leftover words from the days NeevCheck covered other states
 * or carried a hackathon's name. Set SWEEP_SHOTS=<folder> to also save a screenshot of each.
 */
const FIXTURES = resolve(__dirname, "fixtures");
const ECO = "4ad9752355f9455aa9d242c93950ea04";
const AVENUE = (JSON.parse(readFileSync(resolve(FIXTURES, "summary-6742.json"), "utf-8")) as { id: string }).id;
const SHOTS = process.env.SWEEP_SHOTS;

const LEFTOVERS =
  /Maharashtra|Karnataka|Haryana|Telangana|Rajasthan|Gujarat|MahaRERA|Search only|All India|\bMH\b|RYZEN|KIET|HackIIITD|hackathon|महाराष्ट्र|कर्नाटक|हरियाणा|सभी राज्य|किसी भी राज्य/i;

const PAGES = [
  { name: "home", path: "/" },
  { name: "rwas", path: "/#sentinel" },
  { name: "search-and-confirm", path: "/check?q=Supertech%20Eco%20Village" },
  { name: "outside-up", path: "/check?q=P51800000937" },
  { name: "nothing-found", path: "/check?q=nothing%20here" },
  { name: "war-room", path: "/check/__ECO__", settle: true },
  { name: "report", path: "/report/__ECO__" },
  { name: "report-unrated", path: `/report/${"a1".repeat(16)}` },
  { name: "compare", path: `/compare?ids=${ECO},${AVENUE}` },
  { name: "alerts", path: "/alerts?email=buyer%40example.com" },
  { name: "my-reports", path: "/reports", saved: [ECO, AVENUE] },
];

const VIEWPORTS = [
  { name: "desktop", width: 1440, height: 900 },
  { name: "phone", width: 390, height: 844 },
];

for (const lang of ["en", "hi"] as const) {
  for (const viewport of VIEWPORTS) {
    for (const page of PAGES) {
      test(`${page.name} · ${lang} · ${viewport.name}`, async ({ page: browser }) => {
        await visit(browser, lang, viewport, page);
      });
    }
  }
}

async function visit(
  page: Page,
  lang: "en" | "hi",
  viewport: { name: string; width: number; height: number },
  target: { name: string; path: string; settle?: boolean; saved?: string[] },
) {
  const problems: string[] = [];
  page.on("console", (message) => message.type() === "error" && problems.push(message.text()));
  page.on("pageerror", (error) => problems.push(error.message));
  await page.route("https://live.tinyfish.example/**", (route) =>
    route.fulfill({ contentType: "text/html", body: "<p>live view</p>" }),
  );
  await page.setViewportSize({ width: viewport.width, height: viewport.height });
  await page.context().addCookies([{ name: "neevcheck-lang", value: lang, url: "http://localhost:3010" }]);
  if (target.saved) {
    await page.addInitScript((ids) => localStorage.setItem("neevcheck-reports", JSON.stringify(ids)), target.saved);
  }

  await page.goto(target.path.replace("__ECO__", ECO));
  // Pages fill in after a client request; wait for the network to go quiet, and for the stream.
  await page.waitForLoadState("networkidle");
  if (target.settle) await page.waitForTimeout(4500);

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow, "sideways scroll").toBeLessThanOrEqual(0);
  expect(await page.locator("body").innerText()).not.toMatch(LEFTOVERS);
  expect(await cutOffText(page), "text cut off by its box").toEqual([]);
  expect(problems, "console errors").toEqual([]);

  const links = await page.locator("a[href^='/']").evaluateAll((anchors) =>
    [...new Set(anchors.map((a) => (a as HTMLAnchorElement).getAttribute("href") ?? ""))],
  );
  for (const href of links) {
    if (href.startsWith("/#") || href === "/") continue;
    const response = await page.request.get(href);
    expect(response.status(), `link ${href}`).toBeLessThan(400);
  }

  if (SHOTS) {
    mkdirSync(SHOTS, { recursive: true });
    await page.screenshot({ path: resolve(SHOTS, `${target.name}-${lang}-${viewport.name}.png`), fullPage: true });
  }
}

/** Single-line elements whose text is wider than the box that holds it and is clipped, not scrolled. */
async function cutOffText(page: Page): Promise<string[]> {
  return page.evaluate(() =>
    [...document.querySelectorAll<HTMLElement>("h1, h2, h3, button, a, label, th, td, li, span, p")]
      .filter((el) => {
        const style = getComputedStyle(el);
        const clips = style.overflow === "hidden" && style.textOverflow !== "ellipsis" && style.webkitLineClamp === "none";
        return clips && el.children.length === 0 && el.scrollWidth > el.clientWidth + 1 && el.clientWidth > 8;
      })
      .map((el) => `${el.tagName.toLowerCase()}: ${el.textContent?.trim().slice(0, 60)}`),
  );
}
