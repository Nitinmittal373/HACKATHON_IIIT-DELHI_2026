import type { BandV2, Meta } from "@/lib/types";

/** The risk colour of a band, using the same tokens everywhere. "neutral" is not rated. */
export type RiskTone = "low" | "moderate" | "high" | "critical" | "neutral";

export const BAND_TONE: Record<BandV2, RiskTone> = {
  Low: "low",
  Watch: "moderate",
  Elevated: "high",
  High: "critical",
  insufficient_evidence: "neutral",
};

/** Where a value sits on the backend's scale, 0 to 1. */
export function scalePosition(meta: Meta, value: number): number {
  const { min, max } = meta.scale;
  return Math.min(1, Math.max(0, (value - min) / (max - min)));
}

/** How wide a band is, as a share of the whole scale, 0 to 1. */
export function bandShare(meta: Meta, band: Meta["bands"][number]): number {
  const { min, max } = meta.scale;
  return (band.max - band.min + 1) / (max - min + 1);
}

/** The band a value falls in according to the backend's edges, or null outside the scale. */
export function bandOf(meta: Meta, value: number): Meta["bands"][number]["key"] | null {
  return meta.bands.find((band) => value >= band.min && value <= band.max)?.key ?? null;
}

/** "Weight 25%" style share of a pillar, from its weight. */
export function weightPercent(weight: number): number {
  return Math.round(weight * 100);
}
