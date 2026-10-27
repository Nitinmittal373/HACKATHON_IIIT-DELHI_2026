"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useId, useState } from "react";

import { NeevScore } from "@/components/NeevScore";
import { UnratedNote } from "@/components/UnratedNote";
import { describeApiError } from "@/lib/apiMessages";
import { dayOf } from "@/lib/format";
import { startCheck } from "@/lib/history";
import { useLang } from "@/lib/LangProvider";
import type { CheckSummary } from "@/lib/types";
import styles from "./ReportCard.module.css";

interface Props {
  check: CheckSummary;
  picked: boolean;
  /** False once three projects are picked; picked cards can still be unpicked. */
  canPick: boolean;
  onTogglePicked: () => void;
  onRemove: () => void;
}

/** One saved check: its score, its status, and what the visitor can do with it. */
export function ReportCard({ check, picked, canPick, onTogglePicked, onRemove }: Props) {
  const router = useRouter();
  const { lang, t } = useLang();
  const titleId = useId();
  const [starting, setStarting] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  const name = check.project ?? check.rera_id;
  const done = check.status === "completed";
  const display = done ? check.display_score : null;
  const status = done ? "done" : check.status === "failed" ? "failed" : "running";

  async function recheck() {
    setStarting(true);
    setProblem(null);
    try {
      const fresh = await startCheck(check, { fresh: true });
      router.push(`/check/${fresh.id}`);
    } catch (error) {
      setProblem(describeApiError(error, t));
      setStarting(false);
    }
  }

  return (
    <article className={`card ${styles.card}`} aria-labelledby={titleId}>
      {display ? (
        <NeevScore score={display} size={84} delay={0.1} />
      ) : (
        <span className={styles.noRing} aria-hidden="true" />
      )}

      <div className={styles.main}>
        <h2 id={titleId} className={styles.name}>
          {name}
        </h2>
        <p className={`mono ${styles.id}`}>
          {check.rera_id}
        </p>
        <p className={styles.tags}>
          {display && <NeevScore score={display} variant="chip" showValue={false} />}
          <span className={styles.status} data-status={status}>
            {t.reports.status[check.status]}
          </span>
          <span className={styles.date}>{t.reports.checkedOn(dayOf(check.created_at, lang))}</span>
        </p>
        {display && <UnratedNote score={display} />}
        {!display && (
          <p className={styles.hint}>
            {check.status === "failed" ? t.reports.noScoreFailed : t.reports.noScoreRunning}
          </p>
        )}
        {problem && (
          <p className={styles.problem} role="alert">
            {problem}
          </p>
        )}
      </div>

      <div className={styles.actions} role="group" aria-label={t.reports.actionsFor(name)}>
        <Link href={done ? `/report/${check.id}` : `/check/${check.id}`} className="btn2">
          {t.reports.open}
        </Link>
        <button
          type="button"
          className="btn2"
          aria-pressed={picked}
          disabled={!done || (!picked && !canPick)}
          title={!picked && !canPick ? t.reports.compareFull : undefined}
          onClick={onTogglePicked}
        >
          {picked ? t.reports.inCompare : t.reports.compare}
        </button>
        <button type="button" className="btn2" onClick={recheck} disabled={starting || status === "running"}>
          {starting ? t.reports.rechecking : t.reports.recheck}
        </button>
        <button type="button" className={`btn2 ${styles.remove}`} onClick={onRemove}>
          {t.reports.remove}
        </button>
      </div>
    </article>
  );
}
