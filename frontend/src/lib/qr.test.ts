import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import { PNG } from "pngjs";

import { decodeImageData } from "./qr.ts";

// A QR code rendered from a made-up address that carries a MahaRERA number, as a hoarding's would.
const FIXTURE = "src/lib/fixtures/qr-maharera.png";

function picture(file: string): ImageData {
  const { data, width, height } = PNG.sync.read(readFileSync(file));
  return { data: new Uint8ClampedArray(data), width, height } as unknown as ImageData;
}

test("the text inside a QR code photo is read", async () => {
  const text = await decodeImageData(picture(FIXTURE));
  assert.equal(text, "https://maharerait.example.test/projects?certificate_no=P51900008345");
});

test("a picture with no QR code gives nothing", async () => {
  const blank = { data: new Uint8ClampedArray(64 * 64 * 4).fill(255), width: 64, height: 64 };
  assert.equal(await decodeImageData(blank as unknown as ImageData), null);
});
