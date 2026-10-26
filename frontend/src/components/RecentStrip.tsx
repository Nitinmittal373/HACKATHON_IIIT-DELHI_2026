"use client";

import Link from "next/link";

import { NeevScore } from "@/components/NeevScore";
import { UnratedNote } from "@/components/UnratedNote";
import { formatDay } from "@/lib/format";
import { useLang } from "@/lib/LangProvider";
import { useRecentChecks } from "@/lib/useRecentChecks";
import styles from "./RecentStrip.module.css";

/** Real checks other visitors finished, newest first. Hidden until there is at least one. */
export function RecentStrip() {
  const { lang, t } = useLang();
  const recent = useRecentChecks();
  if (recent.status !== "ready") return null;
  const rated = recent.checks.flatMap((check) =>
    check.display_score ? [{ check, display: check.display_score }] : [],
  );
  if (rated.length === 0) return null;

  return (
    <section className={`wrap ${styles.strip}`} aria-labelledby="recent-title">
      <h2 id="recent-title" className={styles.title}>
        {t.home.recent.title}
      </h2>
      <p className={styles.lead}>{t.home.recent.lead}</p>
      <ul className={styles.list}>
        {rated.map(({ check, display }) => {
          const name = check.project ?? check.rera_id;
          const band = t.score.bands[display.band];
          const date = formatDay((check.completed_at ?? check.created_at).slice(0, 10), lang);
          return (
            <li key={check.id}>
              <Link
                href={`/report/${check.id}`}
                className={styles.item}
                aria-label={t.home.recent.item(name, display.value, band, date)}
              >
                <NeevScore score={display} size={56} delay={0.1} />
                <span className={styles.text}>
                  <span className={styles.name}>{name}</span>
                  <span className={`mono ${styles.meta}`}>
                    {check.rera_id} · {date}
                  </span>
                  <span className={styles.band}>
                    <NeevScore score={display} variant="chip" showValue={false} />
                  </span>
                  <UnratedNote score={display} />
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
