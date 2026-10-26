import type { Strings } from "@/lib/i18n";
import type { Meta, Report } from "@/lib/types";
import styles from "./DriversCard.module.css";

interface Props {
  report: Report;
  ids: Map<string, string>;
  meta: Meta;
  t: Strings;
}

/** Where every lost point came from, with the evidence number to look it up. */
export function DriversCard({ report, ids, meta, t }: Props) {
  const { display_score: display, score_v2: score } = report;
  const titles = new Map(report.findings.map((finding) => [finding.id, finding.title]));

  return (
    <section className={`card ${styles.card}`} aria-labelledby="why-title">
      <h2 id="why-title" className={styles.title}>
        {display.value === null ? t.report.whyUnrated : t.report.why(display.value)}
      </h2>
      <p className={styles.lead}>{t.report.whyLead(meta.scale.max)}</p>
      {score.drivers.length === 0 ? (
        <p className={styles.none}>{t.report.noDrivers}</p>
      ) : (
        <ul className={styles.list}>
          {score.drivers.map((driver) => (
            <li key={driver.finding_id} className={styles.row}>
              <span>
                <span className={styles.name}>{titles.get(driver.finding_id)}</span>
                <span className={`mono ${styles.sub}`}>
                  {t.credit.pillars[driver.pillar]} · {driver.code} · {ids.get(driver.finding_id)}
                </span>
              </span>
              <span className={styles.track} aria-hidden="true">
                <span
                  className={`${styles.fill} ${driver.penalty >= 50 ? styles.heavy : ""}`}
                  style={{ width: `${driver.penalty}%` }}
                />
              </span>
              <span className={`num ${styles.points} ${driver.penalty >= 50 ? styles.heavy : ""}`}>
                {`−${Math.abs(Math.round(driver.points))}`}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
