import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

import type { CheckOutcome, EvidenceStatus, Lane, SourceType } from "./types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export type Tone = "high" | "warn" | "ok" | "info" | "neutral";

export function bandTone(band: string): Tone {
  if (band === "High risk") return "high";
  if (band === "Elevated") return "warn";
  if (band === "Watch") return "warn";
  if (band === "Low risk") return "ok";
  return "neutral";
}

/** Ring / gauge colour for a band. Bands also differ in label, never colour alone. */
export function bandColor(band: string): string {
  return (
    {
      "High risk": "#EF5A4C",
      Elevated: "#F08A4B",
      Watch: "#F2B84B",
      "Low risk": "#4FC1A6",
    } as Record<string, string>
  )[band] ?? "#8C9892";
}

export const LANE_LABEL: Record<Lane, string> = {
  rera: "UP-RERA record",
  news: "News & buyer protests",
  mca: "Company records",
  ibbi: "Insolvency (IBBI / NCLT)",
  authority: "Land authority dues",
};

export const LANE_METHOD: Record<Lane, string> = {
  rera: "Web agent",
  mca: "Web agent",
  ibbi: "Search",
  authority: "Search",
  news: "Search",
};

export const STATUS_LABEL: Record<EvidenceStatus, string> = {
  verified: "Verified",
  partially_verified: "Partially verified",
  requires_review: "Requires review",
};

export const STATUS_TONE: Record<EvidenceStatus, Tone> = {
  verified: "ok",
  partially_verified: "info",
  requires_review: "warn",
};

export const SOURCE_LABEL: Record<SourceType, string> = {
  official: "Official",
  registry_mirror: "Registry mirror",
  news: "News",
  other: "Other",
};

export const OUTCOME_LABEL: Record<CheckOutcome, string> = {
  found: "Found",
  not_found: "Not found in checked records",
  unavailable: "Unavailable",
  captcha: "Blocked by CAPTCHA",
  skipped: "Skipped",
};

export const OUTCOME_TONE: Record<CheckOutcome, Tone> = {
  found: "ok",
  not_found: "neutral",
  unavailable: "warn",
  captcha: "warn",
  skipped: "neutral",
};

export function domainOf(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

/** Only http(s) links are ever rendered; scraped text is shown as text, never HTML. */
export function safeHref(url: string): string | undefined {
  return /^https?:\/\//i.test(url) ? url : undefined;
}

export function shortDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso.slice(0, 10);
  return d.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

export function titleCase(s: string | null | undefined): string {
  if (!s) return "";
  return s
    .toLowerCase()
    .replace(/\b([a-z])/g, (m) => m.toUpperCase())
    .replace(/\b(Ii|Iii|Iv)\b/g, (m) => m.toUpperCase());
}
