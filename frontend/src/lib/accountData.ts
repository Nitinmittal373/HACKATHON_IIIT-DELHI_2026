"use client";

import { forgetBridgeToken } from "@/lib/bridgeSession";
import { clearCompareTray } from "@/lib/history";
import { dropReportsOfOthers } from "@/lib/localReports";
import { forgetRecentChecks } from "@/lib/recentChecks";

/**
 * Forgets everything in this browser that belongs to an account: its token, the cached lists,
 * the reports tagged with its id and the compare picks. Reports made while signed out stay,
 * since they belong to nobody. Run on sign-out and after "Delete my data".
 */
export function clearAccountData() {
  forgetBridgeToken();
  forgetRecentChecks();
  dropReportsOfOthers(null);
  clearCompareTray();
}
