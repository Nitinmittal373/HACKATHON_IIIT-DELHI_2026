import type { Strings } from "@/lib/i18n";

const UP_NAME = /UP-RERA/g;

/**
 * Report and check copy was written for UP-RERA. For another state the same sentences name that
 * state's authority instead, so one dictionary serves every state and the two cannot drift.
 */
export function relabel(strings: Strings, rera: string): Strings {
  if (rera === "UP-RERA") return strings;
  return swap(strings, rera) as Strings;
}

function swap(value: unknown, rera: string): unknown {
  if (typeof value === "string") return value.replace(UP_NAME, rera);
  if (typeof value === "function") {
    return (...args: unknown[]) => swap((value as (...a: unknown[]) => unknown)(...args), rera);
  }
  if (Array.isArray(value)) return value.map((item) => swap(item, rera));
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, swap(item, rera)]));
  }
  return value;
}
