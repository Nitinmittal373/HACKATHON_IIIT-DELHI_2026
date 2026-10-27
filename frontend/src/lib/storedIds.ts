"use client";

import { useMemo, useSyncExternalStore } from "react";

import { CHECK_ID_PATTERN } from "@/lib/ids";

export interface IdStore {
  /** Puts the id first, removing any earlier copy, and keeps at most the store's limit. */
  add: (id: string) => void;
  remove: (ids: string[]) => void;
  /** The saved ids in order; null while rendering on the server, before storage is read. */
  useIds: () => string[] | null;
  /** The saved ids right now, for code that is not a component. */
  read: () => string[];
}

/**
 * A short list of check ids kept in this browser's localStorage. Storage can be missing or full
 * (private windows, blocked site data), so every access is guarded and the list is then empty.
 */
export function idStore(key: string, limit: number): IdStore {
  const changed = `${key}-changed`;

  function raw(): string {
    try {
      return window.localStorage.getItem(key) ?? "[]";
    } catch {
      return "[]";
    }
  }

  function save(ids: string[]) {
    try {
      window.localStorage.setItem(key, JSON.stringify(ids.slice(0, limit)));
    } catch {
      // Storage is unavailable; the list just will not remember this.
    }
    window.dispatchEvent(new Event(changed));
  }

  function subscribe(onChange: () => void): () => void {
    // "storage" covers other tabs; the custom event covers this one.
    window.addEventListener("storage", onChange);
    window.addEventListener(changed, onChange);
    return () => {
      window.removeEventListener("storage", onChange);
      window.removeEventListener(changed, onChange);
    };
  }

  return {
    add: (id) => save([id, ...parse(raw()).filter((known) => known !== id)]),
    read: () => parse(raw()),
    remove: (ids) => save(parse(raw()).filter((known) => !ids.includes(known))),
    useIds: () => {
      const text = useSyncExternalStore(subscribe, raw, () => null);
      return useMemo(() => (text === null ? null : parse(text)), [text]);
    },
  };
}

function parse(text: string): string[] {
  try {
    const value: unknown = JSON.parse(text);
    if (!Array.isArray(value)) return [];
    return value.filter((id): id is string => typeof id === "string" && CHECK_ID_PATTERN.test(id));
  } catch {
    return [];
  }
}
