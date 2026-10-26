"use client";

import { createContext, useContext, type ReactNode } from "react";

import type { Meta } from "@/lib/types";

const MetaContext = createContext<Meta | null>(null);

/** The layout reads /api/meta once on the server and hands it down, so no client fetches it. */
export function MetaProvider({ meta, children }: { meta: Meta; children: ReactNode }) {
  return <MetaContext.Provider value={meta}>{children}</MetaContext.Provider>;
}

export function useMeta(): Meta {
  const meta = useContext(MetaContext);
  if (!meta) throw new Error("useMeta must be used inside <MetaProvider>");
  return meta;
}
