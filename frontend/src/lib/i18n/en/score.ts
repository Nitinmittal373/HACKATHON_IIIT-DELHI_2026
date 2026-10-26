import type { BandV2 } from "@/lib/types";

const bands: Record<BandV2, string> = {
  Low: "Low risk",
  Watch: "Watch",
  Elevated: "Elevated risk",
  High: "High risk",
  insufficient_evidence: "Not enough evidence yet",
};

/** The words for NeevScore: one band map, used by every screen. The scale comes from /api/meta. */
export const score = {
  bands,
  label: (value: number, max: number, band: string) => `NeevScore ${value} out of ${max}, ${band}`,
  outOf: (max: number) => `out of ${max}`,
  short: (value: number, band: string) => `NeevScore ${value} · ${band}`,
};
