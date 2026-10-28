"use client";

import { bridgeToken } from "@/lib/bridgeSession";
import { createCheck } from "@/lib/api";
import { ANON, addLocalReport, removeLocalReports, useAnonIds } from "@/lib/localReports";
import { forgetRecentChecks } from "@/lib/recentChecks";
import { idStore } from "@/lib/storedIds";
import type { Check, Project } from "@/lib/types";

/** The projects picked to compare, newest first; at most three. Shared by My reports and reports. */
const tray = idStore("neevcheck-compare", 3);

/** The reports made in this browser while signed out; a signed-in visitor's come from the API. */
export const useHistory = useAnonIds;
export const forgetChecks = removeLocalReports;

export const addToCompare = tray.add;
export const removeFromCompare = tray.remove;
export const useCompareTray = tray.useIds;
export const clearCompareTray = () => tray.remove(tray.read());

// Set while someone is signed in: a new check is then sent with their token and saved to them.
let signedInAs: string | null = null;

export function setSignedInAs(accountId: string | null) {
  signedInAs = accountId;
}

/** A sign-in token, or null when it cannot be had; the check then simply starts signed out. */
async function tokenOrNull(): Promise<string | null> {
  try {
    return await bridgeToken();
  } catch {
    return null;
  }
}

/** The token a signed-in visitor's searches carry, so they get the larger daily limit. */
export async function searchToken(): Promise<string | undefined> {
  return (signedInAs ? await tokenOrNull() : null) ?? undefined;
}

/** Starts a live check (or reuses a recent report) and adds it to "My reports". */
export async function startCheck(
  project: Pick<Project, "rera_id" | "details_url">,
  options: { fresh?: boolean } = {},
): Promise<Check> {
  const token = signedInAs ? await tokenOrNull() : null;
  const check = await createCheck(project, options, token ?? undefined);
  // The API has saved it to the account when a token went along; the tag says whose it is here.
  addLocalReport(check.id, token && signedInAs ? signedInAs : ANON);
  forgetRecentChecks();
  return check;
}
