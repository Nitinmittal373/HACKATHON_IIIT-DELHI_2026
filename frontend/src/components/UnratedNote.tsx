"use client";

import { useLang } from "@/lib/LangProvider";
import type { DisplayScore } from "@/lib/types";
import styles from "./UnratedNote.module.css";

/** "Not enough evidence yet · 2 of 6 record types read", beside a dash that has no number. */
export function UnratedNote({ score }: { score: DisplayScore }) {
  const { t } = useLang();
  if (score.value !== null) return null;
  return <span className={styles.note}>{t.score.unrated(score.records_read, score.records_total)}</span>;
}
