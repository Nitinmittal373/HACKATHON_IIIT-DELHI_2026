"use client";

import { useEffect, useState } from "react";

import { recentChecks } from "@/lib/api";
import type { RecentCheck } from "@/lib/types";

export type RecentState =
  | { status: "loading" }
  | { status: "ready"; checks: RecentCheck[] }
  | { status: "failed" };

/**
 * The latest finished checks, fetched in the browser after the page has loaded, so a sleeping
 * free-plan server never holds up the home page itself.
 */
export function useRecentChecks(): RecentState {
  const [state, setState] = useState<RecentState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;
    recentChecks().then(
      (checks) => !cancelled && setState({ status: "ready", checks }),
      () => !cancelled && setState({ status: "failed" }),
    );
    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}
