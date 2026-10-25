/**
 * Captures the README images from the running app: the hero screenshot, the full home page,
 * a phone-width screenshot and the hero animation.
 *
 *   npx playwright install chromium     # once
 *   npm run build && npm start          # in another terminal
 *   npm run capture
 *
 * BASE_URL points at the running app (default http://localhost:3000).
 */
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { chromium, type Page } from "@playwright/test";
import gifenc from "gifenc";
import { PNG } from "pngjs";

// gifenc is a CommonJS package, so its functions come from the default export.
const { GIFEncoder, applyPalette, quantize } = gifenc;

const BASE_URL = process.env.BASE_URL ?? "http://localhost:3000";
const ASSETS = resolve(dirname(fileURLToPath(import.meta.url)), "../../docs/assets");
const SETTLE_MS = 7000; // the hero's longest entrance animation ends at about 5 s
const GIF_SIZE = { width: 1000, height: 640 };
const GIF_SECONDS = 7;
const GIF_COLORS = 128;
// Scroll-driven reveals only play while scrolling; for a still picture show their final state.
const REVEAL_OFF = ".rv, [class*=ScoreScale_marker] { animation: none !important; }";

function save(relativePath: string, bytes: Uint8Array): void {
  const target = resolve(ASSETS, relativePath);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, bytes);
  console.log(`saved ${relativePath} (${Math.round(bytes.length / 1024)} KB)`);
}

async function open(page: Page): Promise<void> {
  await page.goto(BASE_URL, { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
}

async function screens(page: Page): Promise<void> {
  await page.setViewportSize({ width: 1440, height: 900 });
  await open(page);
  await page.waitForTimeout(SETTLE_MS);
  save("screens/hero.png", await page.screenshot());

  // Sections reveal as they scroll into view; for one tall picture show them all.
  await page.addStyleTag({ content: REVEAL_OFF });
  save("screens/home-full.png", await page.screenshot({ fullPage: true }));

  await page.setViewportSize({ width: 390, height: 844 });
  await open(page);
  await page.waitForTimeout(SETTLE_MS);
  await page.addStyleTag({ content: REVEAL_OFF });
  save("screens/home-mobile.png", await page.screenshot({ fullPage: true }));
}

async function heroGif(page: Page): Promise<void> {
  await page.setViewportSize(GIF_SIZE);
  const encoder = GIFEncoder();
  const frames: { rgba: Uint8Array; at: number }[] = [];

  await page.goto(BASE_URL, { waitUntil: "domcontentloaded" });
  const start = Date.now();
  while (Date.now() - start < GIF_SECONDS * 1000) {
    const png = PNG.sync.read(await page.screenshot());
    frames.push({ rgba: new Uint8Array(png.data), at: Date.now() - start });
  }

  frames.forEach((frame, index) => {
    const next = frames[index + 1]?.at ?? frame.at + 1000;
    const palette = quantize(frame.rgba, GIF_COLORS);
    encoder.writeFrame(applyPalette(frame.rgba, palette), GIF_SIZE.width, GIF_SIZE.height, {
      palette,
      delay: Math.max(next - frame.at, 40),
    });
  });
  encoder.finish();
  save("hero.gif", encoder.bytes());
}

const browser = await chromium.launch();
try {
  const page = await browser.newPage();
  await screens(page);
  await heroGif(page);
} finally {
  await browser.close();
}
