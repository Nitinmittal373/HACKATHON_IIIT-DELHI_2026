"use client";

import { createCheck } from "@/lib/api";
import { idStore } from "@/lib/storedIds";
import type { Check, Project } from "@/lib/types";

/** "My reports" without accounts: the checks a visitor started, newest first, in this browser. */
const history = idStore("neevcheck-reports", 50);

/** The projects picked to compare, newest first; at most three. Shared by My reports and reports. */
const tray = idStore("neevcheck-compare", 3);

export const rememberCheck = history.add;
export const forgetChecks = history.remove;
export const useHistory = history.useIds;

export const addToCompare = tray.add;
export const removeFromCompare = tray.remove;
export const useCompareTray = tray.useIds;

/** Starts a live check (or reuses one from the last day) and adds it to "My reports". */
export async function startCheck(
  project: Pick<Project, "rera_id" | "details_url">,
  options: { fresh?: boolean } = {},
): Promise<Check> {
  const check = await createCheck(project, options);
  rememberCheck(check.id);
  return check;
}
