"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { describeApiError } from "@/lib/apiMessages";
import { indianDay } from "@/lib/format";
import { startCheck } from "@/lib/history";
import { useLang } from "@/lib/LangProvider";
import type { Project } from "@/lib/types";
import styles from "./RecheckNote.module.css";

interface Props {
  hours: number;
  /** The day the records were read, already formatted. */
  readOn: string;
  project: Pick<Project, "rera_id" | "details_url">;
  /** When "Re-check now" opens again for this project; null while it is open. */
  nextRecheckAt: string | null;
}

// Records change: a delay order or an insolvency admission can land in any week.
const STALE_AFTER_HOURS = 7 * 24;

/** When the records were read, and a way to read them again; past a week it says so plainly. */
export function RecheckNote({ hours, readOn, project, nextRecheckAt }: Props) {
  const stale = hours > STALE_AFTER_HOURS;
  const router = useRouter();
  const { lang, t } = useLang();
  const waiting = Boolean(nextRecheckAt);
  const [starting, setStarting] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  async function recheck() {
    setStarting(true);
    setProblem(null);
    try {
      const check = await startCheck(project, { fresh: true });
      router.push(`/check/${check.id}`);
    } catch (error) {
      setProblem(describeApiError(error, t, lang));
      setStarting(false);
    }
  }

  return (
    <p className={`${styles.note} ${stale ? styles.stale : ""} noPrint`}>
      <span>
        <b>{t.insights.freshness.readOn(readOn)}</b> · {t.report.checkedAgo(hours)}
      </span>
      {stale && <span>{t.insights.freshness.stale}</span>}
      {waiting ? (
        <span className={styles.wait}>{t.insights.freshness.nextRecheck(indianDay(nextRecheckAt ?? "", lang))}</span>
      ) : (
        <button type="button" className={stale ? "btn" : styles.button} onClick={recheck} disabled={starting}>
          {stale ? t.insights.freshness.recheck : t.report.recheck}
        </button>
      )}
      {problem && (
        <span className={styles.problem} role="alert">
          {problem}
        </span>
      )}
    </p>
  );
}
