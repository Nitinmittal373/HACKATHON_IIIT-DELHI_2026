import { API_URL } from "@/lib/api";
import type { StateInfo } from "@/lib/types";

const REVALIDATE_SECONDS = 3600;
const TIMEOUT_MS = 20_000;

/** The state list for server-rendered pages, cached for an hour; null when the API is down. */
export async function loadStates(): Promise<StateInfo[] | null> {
  try {
    const response = await fetch(`${API_URL}/api/states`, {
      next: { revalidate: REVALIDATE_SECONDS },
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
    return response.ok ? ((await response.json()) as StateInfo[]) : null;
  } catch {
    return null;
  }
}
