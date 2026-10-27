"use client";

import { useMemo, useSyncExternalStore } from "react";

import { CHECK_ID_PATTERN } from "@/lib/ids";

/** The owner of a report made while nobody was signed in. Any other owner is an account id. */
export const ANON = "anon";

export interface LocalReport {
  id: string;
  owner: string;
}

const KEY = "neevcheck-reports";
const CHANGED = "neevcheck-reports-changed";
const LIMIT = 50;

function raw(): string {
  try {
    return window.localStorage.getItem(KEY) ?? "[]";
  } catch {
    return "[]";
  }
}

function save(reports: LocalReport[]) {
  try {
    window.localStorage.setItem(KEY, JSON.stringify(reports.slice(0, LIMIT)));
  } catch {
    // Storage is unavailable; the list just will not remember this.
  }
  window.dispatchEvent(new Event(CHANGED));
}

function subscribe(onChange: () => void): () => void {
  // "storage" covers other tabs; the custom event covers this one.
  window.addEventListener("storage", onChange);
  window.addEventListener(CHANGED, onChange);
  return () => {
    window.removeEventListener("storage", onChange);
    window.removeEventListener(CHANGED, onChange);
  };
}

/**
 * Reads the stored list. A bare id string is a report from before owners were kept, made
 * without an account, so it counts as "anon".
 */
function parse(text: string): LocalReport[] {
  try {
    const value: unknown = JSON.parse(text);
    if (!Array.isArray(value)) return [];
    return value.flatMap((entry): LocalReport[] => {
      if (typeof entry === "string") return CHECK_ID_PATTERN.test(entry) ? [{ id: entry, owner: ANON }] : [];
      const { id, owner } = (entry ?? {}) as Partial<LocalReport>;
      if (typeof id !== "string" || !CHECK_ID_PATTERN.test(id)) return [];
      return [{ id, owner: typeof owner === "string" && owner ? owner : ANON }];
    });
  } catch {
    return [];
  }
}

export function readLocalReports(): LocalReport[] {
  return parse(raw());
}

/** Puts the report first, removing any earlier copy of the same check. */
export function addLocalReport(id: string, owner: string) {
  save([{ id, owner }, ...readLocalReports().filter((report) => report.id !== id)]);
}

export function removeLocalReports(ids: string[]) {
  save(readLocalReports().filter((report) => !ids.includes(report.id)));
}

/** Keeps only the reports made while signed out, and those of `keep` if an account is given. */
export function dropReportsOfOthers(keep: string | null) {
  const before = readLocalReports();
  const kept = before.filter((report) => report.owner === ANON || report.owner === keep);
  if (kept.length !== before.length) save(kept);
}

/** The ids of reports made while signed out, newest first; null while rendering on the server. */
export function useAnonIds(): string[] | null {
  const text = useSyncExternalStore(subscribe, raw, () => null);
  return useMemo(
    () => (text === null ? null : parse(text).flatMap((r) => (r.owner === ANON ? [r.id] : []))),
    [text],
  );
}

export function readAnonIds(): string[] {
  return readLocalReports().flatMap((report) => (report.owner === ANON ? [report.id] : []));
}
