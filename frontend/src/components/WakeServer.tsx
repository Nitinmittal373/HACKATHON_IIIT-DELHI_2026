"use client";

import { useEffect } from "react";

import { wakeServer } from "@/lib/api";

/**
 * Renders nothing. On load it pings the API so a sleeping free-plan server starts while the
 * visitor is still reading the page, not after they press search.
 */
export function WakeServer() {
  useEffect(() => {
    void wakeServer();
  }, []);
  return null;
}
