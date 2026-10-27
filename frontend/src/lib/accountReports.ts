"use client";

import { forgetAccountReport, listAccountReports, saveAccountReports } from "@/lib/api";
import { forgetChecks, setAccountSaver, readLocalHistory } from "@/lib/history";

const TOKEN_REFRESH_MS = 9 * 60_000;
let cached: { token: string; at: number } | null = null;

/** A ten-minute sign-in token for the API, asked from this site and reused for nine minutes. */
export async function bridgeToken(): Promise<string> {
  if (cached && Date.now() - cached.at < TOKEN_REFRESH_MS) return cached.token;
  const response = await fetch("/api/bridge-token", { cache: "no-store" });
  if (!response.ok) throw new Error("Could not get a sign-in token");
  const { token } = (await response.json()) as { token: string };
  cached = { token, at: Date.now() };
  return token;
}

export async function accountReports() {
  return listAccountReports(await bridgeToken());
}

export async function saveToAccount(ids: string[]) {
  return saveAccountReports(await bridgeToken(), ids);
}

export async function forgetFromAccount(id: string) {
  return forgetAccountReport(await bridgeToken(), id);
}

/**
 * Called when someone is signed in: new checks go to the account, and the checks kept in this
 * browser move into it the first time (then leave the browser). Returns the clean-up.
 */
export function listChecksOfAccount(): () => void {
  setAccountSaver((id) => saveToAccount([id]).then(() => undefined));
  const local = readLocalHistory();
  if (local.length > 0) {
    saveToAccount(local).then(
      () => forgetChecks(local),
      () => undefined, // the list stays in this browser and moves over on the next visit
    );
  }
  return () => setAccountSaver(null);
}
