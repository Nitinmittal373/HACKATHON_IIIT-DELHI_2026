import type { Strings } from "@/lib/i18n";
import type { Report } from "@/lib/types";
import styles from "./DriversCard.module.css";

interface Props {
  report: Report;
  ids: Map<string, string>;
  t: Strings;
}

/** Where every lost point came from, with the evidence number to look it up. */
export function DriversCard({ report, ids, t }: Props) {
  const { score } = report;
  return (
    <section className={`card ${styles.card}`} aria-labelledby="why-title">
      <h2 id="why-title" className={styles.title}>
        {t.report.why(score.value)}
      </h2>
      <p className={styles.lead}>{t.report.whyLead}</p>
      {score.drivers.length === 0 ? (
        <p className={styles.none}>{t.report.noDrivers}</p>
      ) : (
        <ul className={styles.list}>
          {score.drivers.map((driver) => (
            <li key={driver.finding_id} className={styles.row}>
              <span>
                <span className={styles.name}>{driver.title}</span>
                <span className={`mono ${styles.sub}`}>
                  {t.report.areas[driver.area]} · {ids.get(driver.finding_id)}
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
