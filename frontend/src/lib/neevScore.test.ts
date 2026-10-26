import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import { META_FALLBACK } from "./meta.fallback.ts";
import { BAND_TONE, bandOf, bandShare, scalePosition, weightPercent } from "./neevScore.ts";

// The fixture the browser tests serve is what the real API answered; the fallback is written from
// the same constants. They can only differ if one of them is stale.
const SERVED = JSON.parse(readFileSync("e2e/fixtures/meta.json", "utf-8")) as typeof META_FALLBACK;

test("the build-time fallback is the same meta the API serves", () => {
  assert.deepEqual(META_FALLBACK, SERVED);
});

test("a value lands in the band the backend's edges say, at every edge", () => {
  const edges = META_FALLBACK.bands.flatMap((band) => [
    [band.min, band.key],
    [band.max, band.key],
  ]);
  for (const [value, key] of edges) assert.equal(bandOf(META_FALLBACK, Number(value)), key);
  const { min, max } = META_FALLBACK.scale;
  assert.equal(bandOf(META_FALLBACK, min - 1), null);
  assert.equal(bandOf(META_FALLBACK, max + 1), null);
});

test("the bands tile the scale with no gap and no overlap", () => {
  const ordered = [...META_FALLBACK.bands].sort((a, b) => a.min - b.min);
  assert.equal(ordered[0]?.min, META_FALLBACK.scale.min);
  assert.equal(ordered.at(-1)?.max, META_FALLBACK.scale.max);
  ordered.slice(1).forEach((band, index) => assert.equal(band.min, (ordered[index]?.max ?? 0) + 1));
  const shares = META_FALLBACK.bands.map((band) => bandShare(META_FALLBACK, band));
  assert.ok(Math.abs(shares.reduce((sum, share) => sum + share, 0) - 1) < 1e-9);
});

test("the position on the scale follows the meta, not a fixed range", () => {
  const { min, max } = META_FALLBACK.scale;
  assert.equal(scalePosition(META_FALLBACK, min), 0);
  assert.equal(scalePosition(META_FALLBACK, max), 1);
  assert.equal(scalePosition(META_FALLBACK, min - 50), 0);
  assert.equal(scalePosition(META_FALLBACK, max + 50), 1);
  const other = { ...META_FALLBACK, scale: { min: 0, max: 200 } };
  assert.equal(scalePosition(other, 50), 0.25);
});

test("every band has a risk colour and the unrated band is neutral", () => {
  for (const band of META_FALLBACK.bands) assert.notEqual(BAND_TONE[band.key], "neutral");
  assert.equal(BAND_TONE.insufficient_evidence, "neutral");
});

test("the pillar weights add up to a whole", () => {
  const total = META_FALLBACK.pillars.reduce((sum, pillar) => sum + weightPercent(pillar.weight), 0);
  assert.equal(total, 100);
});
