/**
 * Captures the README pictures from a local production build that replays saved fixtures. It
 * never calls TinyFish: the site is pointed at e2e/mock-api.ts, which answers with the recorded
 * check of UPRERAPRJ8334.
 *
 *   npx playwright install chromium          # once
 *   node e2e/mock-api.ts                     # terminal 1 (MOCK_EVENT_DELAY_MS=450 slows the War Room)
 *   NEXT_PUBLIC_API_URL=http://localhost:8010 npm run build   # terminal 2, then:
 *   AUTH_SECRET=x AUTH_GOOGLE_ID=x AUTH_GOOGLE_SECRET=x AUTH_BRIDGE_SECRET=x \
 *     NEXTAUTH_URL=http://localhost:3010 npx next start -p 3010
 *   BASE_URL=http://localhost:3010 npm run capture
 *
 * The dummy Google settings only turn the sign-in button on; nothing reaches Google.
 * It writes hero.gif, war-room.gif and screens/report.png, screens/login.png, and refuses to
 * keep a GIF of 1 MB or more.
 */
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { chromium, type Page } from "@playwright/test";
import gifenc from "gifenc";
import { PNG } from "pngjs";

// gifenc is a CommonJS package, so its functions come from the default export.
const { GIFEncoder, applyPalette, quantize } = gifenc;

const BASE_URL = process.env.BASE_URL ?? "http://localhost:3010";
// The recorded check the mock API serves.
const CHECK_ID = process.env.CHECK_ID ?? "4ad9752355f9455aa9d242c93950ea04";
const ASSETS = resolve(dirname(fileURLToPath(import.meta.url)), "../../docs/assets");
const MAX_GIF_BYTES = 1_000_000;
const SETTLE_MS = 6000; // the hero's longest entrance animation ends at about 5 s

interface GifOptions {
  path: string;
  size: { width: number; height: number };
  /** Where to take pictures; a function so the War Room can follow its own stream. */
  seconds: number;
  gapMs: number;
  colors: number;
  /** Shortest time a frame stays on screen, in the finished animation. */
  minDelayMs: number;
  /** Text to wait for before the first picture, so the animation does not open on a blank page. */
  readyText?: string;
}

function save(relativePath: string, bytes: Uint8Array): void {
  const target = resolve(ASSETS, relativePath);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, bytes);
  console.log(`saved ${relativePath} (${Math.round(bytes.length / 1024)} KB)`);
}

async function settle(page: Page, path: string, width: number, height: number): Promise<void> {
  await page.setViewportSize({ width, height });
  await page.goto(`${BASE_URL}${path}`, { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(SETTLE_MS);
}

async function recordGif(page: Page, url: string, options: GifOptions): Promise<void> {
  await page.setViewportSize(options.size);
  const frames: { rgba: Uint8Array; at: number }[] = [];
  await page.goto(url, { waitUntil: "domcontentloaded" });
  if (options.readyText) await page.getByText(options.readyText).first().waitFor({ timeout: 30_000 });
  const start = Date.now();
  while (Date.now() - start < options.seconds * 1000) {
    const png = PNG.sync.read(await page.screenshot());
    frames.push({ rgba: new Uint8Array(png.data), at: Date.now() - start });
    await page.waitForTimeout(options.gapMs);
  }

  const encoder = GIFEncoder();
  frames.forEach((frame, index) => {
    const next = frames[index + 1]?.at ?? frame.at + 1500;
    const palette = quantize(frame.rgba, options.colors);
    encoder.writeFrame(applyPalette(frame.rgba, palette), options.size.width, options.size.height, {
      palette,
      delay: Math.max(next - frame.at, options.minDelayMs),
    });
  });
  encoder.finish();
  const bytes = encoder.bytes();
  if (bytes.length >= MAX_GIF_BYTES) {
    throw new Error(`${options.path} is ${bytes.length} bytes; keep each GIF under 1 MB (fewer colours or frames)`);
  }
  save(options.path, bytes);
}

const browser = await chromium.launch();
try {
  const page = await browser.newPage();
  await page.context().addCookies([{ name: "neevcheck-lang", value: "en", url: BASE_URL }]);

  // The saved report, as a buyer reads it.
  await settle(page, `/report/${CHECK_ID}`, 1280, 900);
  save("screens/report.png", await page.screenshot());

  // The optional sign-in page.
  await settle(page, "/login", 1280, 720);
  save("screens/login.png", await page.screenshot());

  await recordGif(page, BASE_URL, {
    path: "hero.gif",
    size: { width: 860, height: 560 },
    seconds: 7,
    gapMs: 160,
    colors: 48,
    minDelayMs: 40,
  });

  await recordGif(page, `${BASE_URL}/check/${CHECK_ID}`, {
    path: "war-room.gif",
    size: { width: 880, height: 640 },
    seconds: 22,
    gapMs: 1100,
    colors: 56,
    minDelayMs: 260,
    readyText: "War Room",
  });
} finally {
  await browser.close();
}
