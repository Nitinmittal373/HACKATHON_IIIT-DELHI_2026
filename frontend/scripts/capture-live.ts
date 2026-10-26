/**
 * Captures the README media that needs a real check: the War Room animation, the report, the
 * "More ways to find it" panel, a find-anything confirm page, the coverage page and a comparison. It starts live checks, so it
 * needs the backend running with a TinyFish key; each report spends at most three agent runs.
 *
 *   npx playwright install chromium          # once
 *   (backend and `npm start` running)
 *   BASE_URL=http://localhost:3000 npm run capture:live
 *
 * COMPARE_QUERY is a second project of the same builder, so its company-level sources come from
 * the cache and cost no agent run.
 */
import { createHash } from "node:crypto";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { chromium, type Page } from "@playwright/test";
import gifenc from "gifenc";
import { PNG } from "pngjs";

const { GIFEncoder, applyPalette, quantize } = gifenc;

const BASE_URL = process.env.BASE_URL ?? "http://localhost:3000";
const PROJECT = process.env.PROJECT ?? "UPRERAPRJ8334";
const FIND_QUERY = process.env.FIND_QUERY ?? "Lodha World Towers";
const COMPARE_QUERY = process.env.COMPARE_QUERY ?? "UPRERAPRJ6742";
const ASSETS = resolve(dirname(fileURLToPath(import.meta.url)), "../../docs/assets");
const SIZE = { width: 880, height: 560 };
const FRAME_EVERY_MS = 2500;
const MAX_FRAMES = 44;
const GIF_COLORS = 64;
const GIF_FRAME_MS = 380;
const CHECK_TIMEOUT_MS = 10 * 60_000;

function save(relativePath: string, bytes: Uint8Array): void {
  const target = resolve(ASSETS, relativePath);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, bytes);
  console.log(`saved ${relativePath} (${Math.round(bytes.length / 1024)} KB)`);
}

async function settle(page: Page, path: string, width = 1280, height = 860): Promise<void> {
  await page.setViewportSize({ width, height });
  await page.goto(`${BASE_URL}${path}`, { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(2500);
}

/** Starts a check of the first result for the query; returns the check's id. */
async function startCheck(page: Page, query: string): Promise<string> {
  await page.goto(`${BASE_URL}/check?q=${encodeURIComponent(query)}`, { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: "Yes, check this project" }).click({ timeout: 120_000 });
  await page.waitForURL(/\/(check|report)\/[0-9a-f]{32}$/, { timeout: 60_000 });
  return page.url().split("/").pop() ?? "";
}

async function finished(page: Page): Promise<void> {
  await page.getByText(/NeevScore \d+|No NeevScore|could not be read/).first().waitFor({ timeout: CHECK_TIMEOUT_MS });
}

/** Frames of the War Room while the lanes read, thinned to a size GitHub shows quickly. */
async function warRoomGif(page: Page): Promise<string> {
  await page.setViewportSize(SIZE);
  const id = await startCheck(page, PROJECT);
  const frames: Uint8Array[] = [];
  const deadline = Date.now() + CHECK_TIMEOUT_MS;
  let last = "";
  while (Date.now() < deadline) {
    const png = PNG.sync.read(await page.screenshot());
    // A picture identical to the last one adds nothing to the animation.
    const key = createHash("md5").update(png.data).digest("hex");
    if (key !== last) frames.push(new Uint8Array(png.data));
    last = key;
    if (await page.getByText(/NeevScore \d+/).first().isVisible().catch(() => false)) break;
    await page.waitForTimeout(FRAME_EVERY_MS);
  }
  const step = Math.max(1, Math.ceil(frames.length / MAX_FRAMES));
  const kept = frames.filter((_, index) => index % step === 0 || index === frames.length - 1);
  const encoder = GIFEncoder();
  for (const rgba of kept) {
    const palette = quantize(rgba, GIF_COLORS);
    encoder.writeFrame(applyPalette(rgba, palette), SIZE.width, SIZE.height, { palette, delay: GIF_FRAME_MS });
  }
  encoder.finish();
  save("war-room.gif", encoder.bytes());
  return id;
}

async function report(page: Page, id: string): Promise<void> {
  await settle(page, `/report/${id}`, 1280, 900);
  save("screens/report-v2.png", await page.screenshot());
}

async function morePanel(page: Page): Promise<void> {
  await settle(page, "/", 1280, 1000);
  await page.getByText("More ways to find it").click();
  await page.waitForTimeout(800);
  save("screens/more-ways.png", await page.screenshot());
}

/** A project only builder and listing sites print: the confirm page says where each number was seen. */
async function confirm(page: Page): Promise<void> {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto(`${BASE_URL}/check?q=${encodeURIComponent(FIND_QUERY)}`, { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: "Yes, check this project" }).waitFor({ timeout: 150_000 });
  await page.waitForTimeout(1500);
  save("screens/confirm.png", await page.screenshot());
}

async function coverage(page: Page): Promise<void> {
  await settle(page, "/coverage", 1280, 900);
  save("screens/coverage.png", await page.screenshot());
}

async function compare(page: Page, first: string): Promise<void> {
  const second = await startCheck(page, COMPARE_QUERY);
  await finished(page);
  await settle(page, `/compare?ids=${first},${second}`, 1280, 900);
  save("screens/compare.png", await page.screenshot());
}

const browser = await chromium.launch();
try {
  const page = await browser.newPage();
  const id = await warRoomGif(page);
  await finished(page);
  await report(page, id);
  await morePanel(page);
  await confirm(page);
  await coverage(page);
  await compare(page, id);
  console.log(`check ${id}`);
} finally {
  await browser.close();
}
