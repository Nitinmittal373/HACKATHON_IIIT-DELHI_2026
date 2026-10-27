"use client";

import { createCheck } from "@/lib/api";
import { idStore } from "@/lib/storedIds";
import type { Check, Project } from "@/lib/types";

/** "My reports" without accounts: the checks a visitor started, newest first, in this browser. */
const history = idStore("neevcheck-reports", 50);

/** The projects picked to compare, newest first; at most three. Shared by My reports and reports. */
const tray = idStore("neevcheck-compare", 3);

export const rememberCheck = history.add;
export const readLocalHistory = history.read;
export const forgetChecks = history.remove;
export const useHistory = history.useIds;

export const addToCompare = tray.add;
export const removeFromCompare = tray.remove;
export const useCompareTray = tray.useIds;

// Set while someone is signed in: a new check is then saved to their account too.
let accountSaver: ((id: string) => Promise<void>) | null = null;

export function setAccountSaver(saver: ((id: string) => Promise<void>) | null) {
  accountSaver = saver;
}

/** Starts a live check (or reuses one from the last day) and adds it to "My reports". */
export async function startCheck(
  project: Pick<Project, "rera_id" | "details_url">,
  options: { fresh?: boolean } = {},
): Promise<Check> {
  const check = await createCheck(project, options);
  rememberCheck(check.id);
  // A failure here only means the report stays in this browser until the next sign-in sync.
  void accountSaver?.(check.id).catch(() => undefined);
  return check;
}
