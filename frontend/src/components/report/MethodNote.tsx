import type { Strings } from "@/lib/i18n";
import type { Meta, Report } from "@/lib/types";
import styles from "./MethodNote.module.css";

interface Props {
  report: Report;
  meta: Meta;
  t: Strings;
}

/** How the score is made, and the one place the first version's 0-100 score is still shown. */
export function MethodNote({ report, meta, t }: Props) {
  const display = report.display_score;
  return (
    <section className={`card ${styles.card}`} aria-labelledby="method-title">
      <h2 id="method-title" className={styles.title}>
        {t.credit.methodTitle}
      </h2>
      <p className={styles.body}>{t.credit.methodBody(meta.scale.max)}</p>
      {display.value === null ? (
        <p className={styles.classic}>
          {t.credit.provisionalLine(
            display.provisional_value ?? report.score_v2.value,
            meta.scale.max,
            display.records_read,
            display.records_total,
          )}
        </p>
      ) : (
        <p className={styles.classic}>{t.credit.classicLine(report.score.value)}</p>
      )}
    </section>
  );
}
