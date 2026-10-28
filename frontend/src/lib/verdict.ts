import type { Finding, Verdict } from "@/lib/types";

export type Tone = "ok" | "review" | "fail" | "context" | "neutral";

/**
 * "Confirmed" belongs to official records. A fact read from news or another secondary source
 * is grey and says so, whatever the verdict.
 */
export function isSecondaryOk(finding: Pick<Finding, "verdict" | "reliability">): boolean {
  return finding.verdict === "ok" && finding.reliability !== "primary";
}

export function findingTone(finding: Pick<Finding, "verdict" | "reliability">): Tone {
  return isSecondaryOk(finding) ? "neutral" : toneOf(finding.verdict);
}

/** Which colour family a verdict is drawn in (the .tone-* classes in globals.css). */
export function toneOf(verdict: Verdict): Tone {
  switch (verdict) {
    case "ok":
      return "ok";
    case "review":
      return "review";
    case "fail":
    case "red_flag":
      return "fail";
    case "context":
      return "context";
    default:
      return "neutral";
  }
}
