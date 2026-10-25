"use client";

import Link from "next/link";

import { addToCompare, removeFromCompare, useCompareTray } from "@/lib/history";
import { useLang } from "@/lib/LangProvider";
import styles from "./ReportActions.module.css";

/** Puts this report in the compare tray; with two or more there, offers to compare now. */
export function AddToCompare({ reportId }: { reportId: string }) {
  const { t } = useLang();
  const tray = useCompareTray() ?? [];
  const added = tray.includes(reportId);
  const ids = [...tray].reverse().join(",");

  return (
    <>
      <button
        type="button"
        className="btn2"
        aria-pressed={added}
        onClick={() => (added ? removeFromCompare([reportId]) : addToCompare(reportId))}
      >
        {added ? t.compare.inCompare : t.compare.addToCompare}
      </button>
      {added && (
        <span className={styles.status} role="status">
          {tray.length >= 2 ? (
            <Link href={`/compare?ids=${ids}`} className={styles.compareLink}>
              {t.compare.compareNow}
            </Link>
          ) : (
            t.compare.addedNeedOne
          )}
        </span>
      )}
    </>
  );
}
