import Link from "next/link";

import { NeevScore } from "@/components/NeevScore";
import { dayOf } from "@/lib/format";
import type { Lang, Strings } from "@/lib/i18n";
import type { Alert, AlertChange } from "@/lib/types";
import styles from "./AlertCard.module.css";

interface Props {
  alert: Alert;
  t: Strings;
  lang: Lang;
}

/** One change Sentinel found: the score before and after, and exactly what is different. */
export function AlertCard({ alert, t, lang }: Props) {
  const before = alert.old_display_score;
  const after = alert.new_display_score;
  const groups: [string, AlertChange[], string][] = [
    [t.alerts.added, alert.added, "added"],
    [t.alerts.changed, alert.changed, "changed"],
    [t.alerts.removed, alert.removed, "removed"],
  ];

  return (
    <article className={`card ${styles.card}`}>
      <header className={styles.head}>
        <span className={styles.icon} aria-hidden="true" />
        <div className={styles.titles}>
          <h2 className={styles.project}>{alert.project_name ?? alert.rera_id}</h2>
          <span className={`mono ${styles.when}`}>
            {t.alerts.when} {dayOf(alert.created_at, lang)}
          </span>
        </div>
        <span className={styles.score} aria-label={t.alerts.scoreChange(before?.value, after?.value)}>
          {before ? <NeevScore value={before.value} band={before.band} variant="chip" /> : <span aria-hidden="true">–</span>}
          <span aria-hidden="true">→</span>
          {after ? <NeevScore value={after.value} band={after.band} variant="chip" /> : <span aria-hidden="true">–</span>}
        </span>
      </header>
      {groups.map(([label, changes, kind]) =>
        changes.length === 0 ? null : (
          <section key={kind} className={styles.group}>
            <h3 className={`${styles.label} ${styles[kind]}`}>{label}</h3>
            <ul>
              {changes.map((change) => (
                <li key={change.title}>
                  {change.source_url ? (
                    <a href={change.source_url} target="_blank" rel="noopener noreferrer">
                      {change.title}
                      <span className="sr"> ({t.common.opensInNewTab})</span>
                    </a>
                  ) : (
                    change.title
                  )}
                </li>
              ))}
            </ul>
          </section>
        ),
      )}
      <Link href={`/report/${alert.check_id}`} className={styles.report}>
        {t.alerts.openReport}
      </Link>
    </article>
  );
}
