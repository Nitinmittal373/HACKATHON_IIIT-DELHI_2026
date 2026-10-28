import { formatDay } from "@/lib/format";
import type { Lang, Strings } from "@/lib/i18n";
import type { Finding } from "@/lib/types";
import { findingTone } from "@/lib/verdict";
import styles from "./Timeline.module.css";

interface Props {
  events: Finding[];
  t: Strings;
  lang: Lang;
}

/** Dated events taken straight from the findings; nothing is added to fill gaps. */
export function Timeline({ events, t, lang }: Props) {
  return (
    <section className={`card ${styles.card}`} aria-labelledby="timeline-title">
      <h2 id="timeline-title" className={styles.title}>
        {t.report.timelineTitle}
      </h2>
      {events.length === 0 ? (
        <p className={styles.none}>{t.report.noTimeline}</p>
      ) : (
        <ol className={styles.list}>
          {events.map((event) =>
            event.occurred_on ? (
              <li key={event.id} className={`${styles.item} tone-${findingTone(event)}`}>
                <time className={`mono ${styles.date}`} dateTime={event.occurred_on}>
                  {formatDay(event.occurred_on, lang)}
                </time>
                <span className={styles.text}>{event.title}</span>
              </li>
            ) : null,
          )}
        </ol>
      )}
    </section>
  );
}
