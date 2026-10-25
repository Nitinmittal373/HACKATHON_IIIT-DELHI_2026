"use client";

import Link from "next/link";

import { useLang } from "@/lib/LangProvider";
import styles from "./CompareBar.module.css";

/** Sticks to the bottom of the window once a report is picked for comparing. */
export function CompareBar({ picked, max }: { picked: string[]; max: number }) {
  const { t } = useLang();
  if (picked.length === 0) return null;
  const ready = picked.length >= 2;

  return (
    <div className={`card ${styles.bar}`} role="region" aria-label={t.reports.compareGo}>
      <p className={styles.text} role="status">
        <b>{t.reports.compareCount(picked.length)}</b>
        <span>{picked.length >= max ? t.reports.compareFull : t.reports.compareHint}</span>
      </p>
      {ready ? (
        <Link href={`/compare?ids=${picked.join(",")}`} className="btn">
          {t.reports.compareGo}
        </Link>
      ) : (
        <button type="button" className="btn" disabled>
          {t.reports.compareGo}
        </button>
      )}
    </div>
  );
}
