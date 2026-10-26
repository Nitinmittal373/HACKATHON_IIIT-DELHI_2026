import { STATE_NAMES_HI } from "@/lib/i18n/hi/states";
import type { Lang } from "@/lib/i18n";
import type { StateInfo } from "@/lib/types";

export type Coverage = StateInfo["coverage"];

/** The state's name in the visitor's language. */
export function stateLabel(code: string, apiName: string, lang: Lang): string {
  return lang === "hi" ? (STATE_NAMES_HI[code] ?? apiName) : apiName;
}

const DASHES = /[‐-—]/g;

/**
 * The state whose number format the text matches, or null. The patterns come from the API and
 * are written for Python's re.IGNORECASE, which a JavaScript "i" flag reads the same way.
 */
export function detectState(query: string, states: StateInfo[]): StateInfo | null {
  const text = query.trim().replace(DASHES, "-").replace(/\s+/g, " ");
  if (text.length < 5) return null;
  const compact = text.replace(/\s/g, "");
  for (const state of states) {
    for (const pattern of state.id_patterns) {
      const exact = new RegExp(`^(?:${pattern})$`, "i");
      if (exact.test(text) || exact.test(compact)) return state;
    }
  }
  return null;
}
