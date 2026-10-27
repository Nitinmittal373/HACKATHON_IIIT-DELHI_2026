import type { RecentCheck } from "@/lib/types";

const FRESH_FOR_MS = 60_000;

// The hero card, the score scale and the strip all ask at once; they share one request.
let cached: { key: string; at: number; checks: Promise<RecentCheck[]> } | null = null;

export function forgetRecentChecks() {
  cached = null;
}

/** One request per scope ("account:<id>" or "browser:<ids>") per minute. */
export function sharedRecentChecks(key: string, fetch: () => Promise<RecentCheck[]>): Promise<RecentCheck[]> {
  if (!cached || cached.key !== key || Date.now() - cached.at > FRESH_FOR_MS) {
    const checks = fetch();
    cached = { key, at: Date.now(), checks };
    checks.catch(() => (cached = null));
  }
  return cached.checks;
}
