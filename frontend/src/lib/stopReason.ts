import type { Strings } from "@/lib/i18n";

/**
 * Reasons the API words itself because the lane never ran an agent: credit paused, a CAPTCHA
 * site that is not checked automatically, a builder known only by a trade name. Null otherwise.
 */
export function plainReason(reason: string | null, t: Strings): string | null {
  if (!reason) return null;
  if (reason.startsWith("Paused:")) return t.cam.pausedCredits;
  if (reason.startsWith("Not checked automatically")) return t.cam.notCheckedCaptcha;
  if (reason.startsWith("Skipped:")) return t.cam.skippedTradeName;
  return null;
}

/** The reason a source stopped, worded for the reader. CAPTCHAs and timeouts are named plainly. */
export function stopReason(reason: string | null, t: Strings): string {
  if (!reason) return t.cam.unreadReason;
  const plain = plainReason(reason, t);
  if (plain) return plain;
  if (/captcha/i.test(reason)) return t.cam.blockedCaptcha;
  if (reason === "timeout" || /^No answer within/i.test(reason)) return t.cam.blockedTimeout;
  return t.cam.blockedOther(reason);
}
