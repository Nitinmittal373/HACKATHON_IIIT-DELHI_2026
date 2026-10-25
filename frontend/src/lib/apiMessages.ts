import { ApiError } from "@/lib/api";
import type { Strings } from "@/lib/i18n";

/** A calm, specific sentence for whatever went wrong when calling the API. */
export function describeApiError(error: unknown, t: Strings): string {
  if (!(error instanceof ApiError)) return t.errors.somethingBody;
  if (error.status === 0) return t.errors.unreachableBody;
  if (error.status === 429) {
    return error.code === "daily_cap" ? t.errors.dailyCap : t.errors.rateLimited(error.retryAfter ?? 60);
  }
  if (error.status === 402 || /credit|wallet|balance/i.test(error.message)) return t.errors.walletEmpty;
  return t.errors.somethingBody;
}
