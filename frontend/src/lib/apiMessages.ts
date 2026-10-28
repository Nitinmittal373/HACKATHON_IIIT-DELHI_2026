import { ApiError } from "@/lib/api";
import { indianDay } from "@/lib/format";
import type { Lang, Strings } from "@/lib/i18n";

/** A calm, specific sentence for whatever went wrong when calling the API. */
export function describeApiError(error: unknown, t: Strings, lang: Lang = "en"): string {
  if (!(error instanceof ApiError)) return t.errors.somethingBody;
  if (error.status === 0) return t.errors.unreachableBody;
  switch (error.code) {
    case "signin_required":
      return t.errors.signinRequired;
    case "account_limit":
      return t.errors.accountLimit;
    case "site_budget":
      return /month/i.test(error.message) ? t.errors.siteBudgetMonth : t.errors.siteBudget;
    case "invite_only":
      return t.errors.inviteOnly;
    case "recheck_wait":
      return t.errors.recheckWait(error.resetsAt ? indianDay(error.resetsAt, lang) : "—");
    case "search_limit":
      return t.errors.searchLimitOut;
    case "site_search_limit":
      return t.errors.siteSearchLimit;
  }
  if (error.status === 429) return t.errors.rateLimited(error.retryAfter ?? 60);
  if (error.status === 402 || /credit|wallet|balance/i.test(error.message)) return t.errors.walletEmpty;
  return t.errors.somethingBody;
}

/** What went wrong with a search, named by the code the API sent: never a generic error. */
export function describeSearchError(
  error: unknown,
  t: Strings,
  signedIn = false,
): { text: string; reason: string | null } {
  if (!(error instanceof ApiError)) return { text: t.confirm.searchFailedBody, reason: null };
  switch (error.code) {
    case "search_limit":
      return { text: signedIn ? t.errors.searchLimitIn : t.errors.searchLimitOut, reason: null };
    case "site_search_limit":
      return { text: t.errors.siteSearchLimit, reason: null };
    case "timeout":
    case "client_timeout":
      return { text: t.confirm.searchTimeout, reason: null };
    case "tinyfish_key":
      return { text: t.confirm.searchKey, reason: null };
    case "wallet_empty":
      return { text: t.errors.walletEmpty, reason: null };
    case "rate_limited":
      return { text: t.confirm.searchBusy(error.retryAfter ?? 60), reason: null };
  }
  if (error.status === 0) return { text: t.errors.unreachableBody, reason: null };
  // Anything else: the general sentence, plus the API's own words so the cause is not hidden.
  return { text: t.confirm.searchFailedBody, reason: error.message };
}
