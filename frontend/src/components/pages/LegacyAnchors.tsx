"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

// Links that were shared when the home page held every section keep working.
const MOVED: Record<string, string> = {
  "#search": "/check",
  "#more": "/check",
  "#how-it-works": "/how-it-works",
  "#sentinel": "/rwa",
};

/** Sends an old /#anchor address to the page that now holds that section. */
export function LegacyAnchors() {
  const router = useRouter();
  useEffect(() => {
    const target = MOVED[window.location.hash];
    if (target) router.replace(target);
  }, [router]);
  return null;
}
