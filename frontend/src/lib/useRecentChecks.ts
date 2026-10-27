"use client";

import { useEffect, useState } from "react";

import { useAccount } from "@/lib/account";
import { bridgeToken } from "@/lib/bridgeSession";
import { listChecks, listAccountRecent } from "@/lib/api";
import { useAnonIds } from "@/lib/localReports";
import { sharedRecentChecks } from "@/lib/recentChecks";
import type { RecentCheck } from "@/lib/types";

export const RECENT_SHOWN = 6;
/** "account": the signed-in account's checks. "browser": checks made here while signed out. */
export type RecentScope = "account" | "browser";

export type RecentState =
  | { status: "loading" }
  | { status: "ready"; scope: RecentScope; checks: RecentCheck[] }
  | { status: "failed" };

/**
 * The visitor's own latest checks, fetched in the browser after the page has loaded, so a
 * sleeping free-plan server never holds up the home page. Signed in, they come only from the
 * account; signed out, only from the reports kept in this browser. Nobody else's are ever read.
 */
export function useRecentChecks(): RecentState {
  const account = useAccount();
  const anonIds = useAnonIds();
  const [result, setResult] = useState<{ key: string; state: RecentState } | null>(null);

  const accountId = account.status === "in" ? account.user.id : null;
  const wanted = anonIds?.slice(0, RECENT_SHOWN) ?? [];
  const key =
    account.status === "loading" || (!accountId && anonIds === null)
      ? null
      : accountId
        ? `account:${accountId}`
        : `browser:${wanted.join(",")}`;

  useEffect(() => {
    if (key === null) return;
    let cancelled = false;
    const scope: RecentScope = accountId ? "account" : "browser";
    const fetch = accountId
      ? async () => listAccountRecent(await bridgeToken())
      : async () => (wanted.length > 0 ? sortAsKept(await listChecks(wanted), wanted) : []);
    sharedRecentChecks(key, fetch).then(
      (checks) => !cancelled && setResult({ key, state: { status: "ready", scope, checks } }),
      () => !cancelled && setResult({ key, state: { status: "failed" } }),
    );
    return () => {
      cancelled = true;
    };
    // `wanted` is derived from `key`, which changes whenever it does.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, accountId]);

  return result !== null && result.key === key ? result.state : { status: "loading" };
}

function sortAsKept(checks: RecentCheck[], ids: string[]): RecentCheck[] {
  return ids.flatMap((id) => checks.find((check) => check.id === id) ?? []);
}
