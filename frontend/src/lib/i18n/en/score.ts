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
  label: (value: number | null, max: number, band: string) =>
    value === null ? `NeevScore not given, ${band}` : `NeevScore ${value} out of ${max}, ${band}`,
  outOf: (max: number) => `out of ${max}`,
  short: (value: number | null, band: string) =>
    value === null ? band : `NeevScore ${value} · ${band}`,
  /** Stands where the number would be when too little was read to give one. */
  dash: "—",
  unrated: (read: number, total: number) =>
    `Not enough evidence yet · ${read} of ${total} record types read`,
};
