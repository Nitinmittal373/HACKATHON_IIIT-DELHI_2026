import { ScoreRing } from "@/components/ScoreRing";
import type { ExampleReport } from "@/lib/exampleReport";
import type { Strings } from "@/lib/i18n";
import styles from "./ReportStage.module.css";

const ORB_CLASSES = [styles.o1, styles.o2, styles.o3, styles.o4];

/** The report card that rises into view with four findings floating around it. */
export function ReportStage({ report, t }: { report: ExampleReport; t: Strings }) {
  return (
    <div className={styles.stage} id="sample-report">
      <div className={styles.glow} aria-hidden="true" />
      <div className={styles.rise}>
        <article className={styles.card} aria-label={t.home.report.ariaLabel(report.name)}>
          <div className={styles.top}>
            <span className={`mono ${styles.kicker}`}>
              {t.home.report.kicker(report.readOn.toUpperCase())}
            </span>
            <span className={`${styles.band} ${styles[report.band]}`}>{report.bandLabel}</span>
          </div>
          <div className={styles.body}>
            <ScoreRing value={report.score} band={report.band} />
            <div>
              <p className={styles.name}>{report.name}</p>
              <p className={`mono ${styles.id}`}>
                {report.reraId} · {report.promoter}
              </p>
              <ul className={styles.drivers}>
                {report.drivers.map((driver, index) => (
                  <li key={driver.label} className={styles.driver}>
                    <span>{driver.label}</span>
                    <i
                      className={`${styles.bar} ${styles[driver.tone]}`}
                      style={{ ["--fill" as string]: `${driver.fill}%`, ["--delay" as string]: `${index * 0.15}s` }}
                      aria-hidden="true"
                    />
                    <b>−{Math.abs(driver.points)}</b>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </article>
      </div>
      {report.findings.slice(0, ORB_CLASSES.length).map((finding, index) => (
        <div key={finding.bold} className={`${styles.orb} ${ORB_CLASSES[index]}`} aria-hidden="true">
          <span className={`${styles.dot} ${styles[finding.tone]}`} />
          <span>
            <b>{finding.bold}</b> {finding.text}
          </span>
        </div>
      ))}
    </div>
  );
}
