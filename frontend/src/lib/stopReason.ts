import type { Strings } from "@/lib/i18n";

/** The reason a source stopped, worded for the reader. CAPTCHAs and timeouts are named plainly. */
export function stopReason(reason: string | null, t: Strings): string {
  if (!reason) return t.cam.unreadReason;
  if (/captcha/i.test(reason)) return t.cam.blockedCaptcha;
  if (reason === "timeout" || /^No answer within/i.test(reason)) return t.cam.blockedTimeout;
  return t.cam.blockedOther(reason);
}
