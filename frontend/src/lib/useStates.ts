"use client";

import { useEffect, useState } from "react";

import { getStates } from "@/lib/api";
import type { StateInfo } from "@/lib/types";

export type StatesLoad =
  | { status: "loading" }
  | { status: "ready"; states: StateInfo[] }
  | { status: "failed" };

/** The states the API lists. A failure only hides the picker's extras; search keeps working. */
export function useStates(): StatesLoad {
  const [load, setLoad] = useState<StatesLoad>({ status: "loading" });
  useEffect(() => {
    let cancelled = false;
    getStates().then(
      (states) => !cancelled && setLoad({ status: "ready", states }),
      () => !cancelled && setLoad({ status: "failed" }),
    );
    return () => {
      cancelled = true;
    };
  }, []);
  return load;
}
