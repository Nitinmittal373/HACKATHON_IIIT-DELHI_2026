"use client";

import { useEffect, useState } from "react";

import { useAccount } from "@/lib/account";
import { getLimits } from "@/lib/api";
import { searchToken } from "@/lib/history";
import type { Limits } from "@/lib/types";

/**
 * What a live check costs and, once signed in, how many the account has left today. Null until
 * the answer arrives (or if it never does): pages then simply leave the extra line out.
 */
export function useLimits(): Limits | null {
  const account = useAccount();
  const accountId = account.status === "in" ? account.user.id : null;
  const [limits, setLimits] = useState<Limits | null>(null);

  useEffect(() => {
    if (account.status === "loading") return;
    let cancelled = false;
    searchToken()
      .then((token) => getLimits(token))
      .then(
        (found) => !cancelled && setLimits(found),
        () => !cancelled && setLimits(null),
      );
    return () => {
      cancelled = true;
    };
  }, [account.status, accountId]);

  return limits;
}
