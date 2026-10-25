"use client";

import Link from "next/link";

import { formatDay } from "@/lib/format";
import { useLang } from "@/lib/LangProvider";
import { useRecentChecks } from "@/lib/useRecentChecks";
import styles from "./RecentStrip.module.css";

/** Real checks other visitors finished, newest first. Hidden until there is at least one. */
export function RecentStrip() {
  const { lang, t } = useLang();
  const recent = useRecentChecks();
  if (recent.status !== "ready") return null;
  const checks = recent.checks.filter((check) => check.score !== null && check.band !== null);
  if (checks.length === 0) return null;

  return (
    <section className={`wrap ${styles.strip}`} aria-labelledby="recent-title">
      <h2 id="recent-title" className={styles.title}>
        {t.home.recent.title}
      </h2>
      <p className={styles.lead}>{t.home.recent.lead}</p>
      <ul className={styles.list}>
        {checks.map((check) => {
          const name = check.project ?? check.rera_id;
          const band = t.report.bands[check.band ?? "insufficient_evidence"];
          const date = formatDay((check.completed_at ?? check.created_at).slice(0, 10), lang);
          return (
            <li key={check.id}>
              <Link
                href={`/report/${check.id}`}
                className={styles.item}
                aria-label={t.home.recent.item(name, check.score ?? 0, band, date)}
              >
                <span className={`num ${styles.score}`}>{check.score}</span>
                <span className={styles.text}>
                  <span className={styles.name}>{name}</span>
                  <span className={`mono ${styles.meta}`}>
                    {check.rera_id} · {date}
                  </span>
                  <span className={`bandTag ${styles.band}`} data-band={check.band}>
                    {band}
                  </span>
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
