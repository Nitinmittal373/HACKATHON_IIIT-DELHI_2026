"use client";

import { useMemo, useSyncExternalStore } from "react";

import { createCheck } from "@/lib/api";
import { CHECK_ID_PATTERN } from "@/lib/ids";
import type { Check, Project } from "@/lib/types";

/**
 * "My reports" without accounts: the ids of the checks a visitor started, newest first, kept in
 * this browser only. Storage can be missing or full (private windows), so every access is
 * guarded and the app simply shows an empty list.
 */
const KEY = "neevcheck-reports";
const CHANGED = "neevcheck-reports-changed";
const MAX_SAVED = 50;

function raw(): string {
  try {
    return window.localStorage.getItem(KEY) ?? "[]";
  } catch {
    return "[]";
  }
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

function save(ids: string[]) {
  try {
    window.localStorage.setItem(KEY, JSON.stringify(ids.slice(0, MAX_SAVED)));
  } catch {
    // Storage is unavailable; the list just will not remember this visit.
  }
  window.dispatchEvent(new Event(CHANGED));
}

export function rememberCheck(id: string) {
  save([id, ...parse(raw()).filter((known) => known !== id)]);
}

export function forgetChecks(ids: string[]) {
  save(parse(raw()).filter((known) => !ids.includes(known)));
}

function subscribe(onChange: () => void): () => void {
  // "storage" covers other tabs; CHANGED covers this one.
  window.addEventListener("storage", onChange);
  window.addEventListener(CHANGED, onChange);
  return () => {
    window.removeEventListener("storage", onChange);
    window.removeEventListener(CHANGED, onChange);
  };
}

/** The saved ids, newest first; null while rendering on the server, before storage is read. */
export function useHistory(): string[] | null {
  const text = useSyncExternalStore(subscribe, raw, () => null);
  return useMemo(() => (text === null ? null : parse(text)), [text]);
}

/** Starts a live check (or reuses one from the last day) and adds it to "My reports". */
export async function startCheck(
  project: Pick<Project, "rera_id" | "details_url">,
  options: { fresh?: boolean } = {},
): Promise<Check> {
  const check = await createCheck(project, options);
  rememberCheck(check.id);
  return check;
}
