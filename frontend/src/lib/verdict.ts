import type { Verdict } from "@/lib/types";

export type Tone = "ok" | "review" | "fail" | "context" | "neutral";

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
