import Link from "next/link";

import { NeevScore } from "@/components/NeevScore";
import type { Outcome } from "@/lib/checkState";
import type { Strings } from "@/lib/i18n";
import styles from "./ResultCard.module.css";

interface Props {
  outcome: Outcome;
  checkId: string;
  reraId: string;
  t: Strings;
}

/** What the check ended with: the score and a way to the report, or an honest failure. */
export function ResultCard({ outcome, checkId, reraId, t }: Props) {
  if (outcome.status === "failed") {
    return (
      <section className={`card ${styles.card} ${styles.failed}`} role="alert">
        <div>
          <h2 className={styles.title}>{t.cam.failedTitle}</h2>
          <p className={styles.note}>{outcome.message}</p>
          <p className={styles.note}>{t.cam.failedBody}</p>
        </div>
        <Link href={`/check?q=${encodeURIComponent(reraId)}`} className="btn">
          {t.cam.retry}
        </Link>
      </section>
    );
  }

  const score = outcome.score;
  const provisional = !score || score.provisional || score.band === "insufficient_evidence";
  const band = score ? t.score.bands[score.band] : "";
  return (
    <section className={`card ${styles.card}`} aria-live="polite">
      {score && <NeevScore value={score.value} band={score.band} size={96} delay={0.1} />}
      <div className={styles.text}>
        <h2 className={styles.title}>
          {score && !provisional ? t.score.short(score.value, band) : t.cam.resultProvisional}
        </h2>
        <p className={styles.note}>
          {provisional ? t.cam.resultProvisionalNote : t.cam.resultNote}
        </p>
      </div>
      <Link href={`/report/${checkId}`} className="btn btnBig">
        {t.cam.seeReport}
        <svg className="arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M5 12h14M13 6l6 6-6 6" />
        </svg>
      </Link>
    </section>
  );
}
