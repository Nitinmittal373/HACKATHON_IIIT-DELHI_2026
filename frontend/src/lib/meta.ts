import { API_URL } from "@/lib/api";
import { META_FALLBACK } from "@/lib/meta.fallback";
import type { Meta } from "@/lib/types";

const META_TIMEOUT_MS = 3_000;
const FRESH_FOR_MS = 60 * 60_000;
// After a failure, ask again soon but not on every page: a sleeping server must not slow each visit.
const RETRY_AFTER_MS = 60_000;

let known: { meta: Meta; expires: number } | null = null;

function isMeta(value: unknown): value is Meta {
  const meta = value as Partial<Meta> | null;
  return (
    typeof meta?.scale?.min === "number" &&
    typeof meta.scale.max === "number" &&
    Array.isArray(meta.bands) &&
    meta.bands.length > 0 &&
    Array.isArray(meta.pillars) &&
    meta.score_version === META_FALLBACK.score_version
  );
}

/**
 * The score scale, band edges and pillar weights from GET /api/meta, read on the server and
 * remembered for an hour. If the API cannot be reached the generated fallback, written from the
 * same backend constants, is used, so a page never draws a scale of its own.
 */
export async function loadMeta(): Promise<Meta> {
  const now = Date.now();
  if (known && known.expires > now) return known.meta;
  try {
    const response = await fetch(`${API_URL}/api/meta`, {
      cache: "no-store",
      signal: AbortSignal.timeout(META_TIMEOUT_MS),
    });
    const body: unknown = response.ok ? await response.json() : null;
    if (isMeta(body)) {
      known = { meta: body, expires: now + FRESH_FOR_MS };
      return body;
    }
  } catch {
    // Unreachable or too slow: fall through to the fallback below.
  }
  known = { meta: known?.meta ?? META_FALLBACK, expires: now + RETRY_AFTER_MS };
  return known.meta;
}
