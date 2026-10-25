import type { ExampleReport } from "@/lib/exampleReport";
import type { Strings } from "@/lib/i18n";
import styles from "./BrochureVsRecords.module.css";

/** The claims are what brokers typically say, not data; the facts come from the recorded check. */
export function BrochureVsRecords({ report, t }: { report: ExampleReport; t: Strings }) {
  return (
    <section className="wrap section" aria-labelledby="problem-title">
      <div className={`${styles.head} rv`}>
        <div className="eyebrow">{t.home.problem.eyebrow}</div>
        <h2 id="problem-title" className={`h2 ${styles.title}`}>
          {t.home.problem.titleStart} <span className={styles.underline}>{t.home.problem.titleEnd}</span>
        </h2>
      </div>

      <div className={`${styles.versus} rv`}>
        <div className={styles.heard}>
          <div className={`mono ${styles.label}`}>{t.home.problem.heard}</div>
          {t.home.problem.claims.map((claim, index) => (
            <p key={claim} className={styles.claim} style={{ ["--d" as string]: `${index * 0.15}s` }}>
              {claim}
            </p>
          ))}
        </div>
        <div className={styles.mid} aria-hidden="true">
          <span>{t.home.problem.vs}</span>
        </div>
        <div className={styles.records}>
          <div className={`mono ${styles.label} ${styles.recordsLabel}`}>{t.home.problem.records}</div>
          {report.facts.map((fact, index) => (
            <div key={fact.title} className={styles.fact} style={{ ["--d" as string]: `${0.2 + index * 0.15}s` }}>
              <span className={`${styles.dot} ${styles[fact.tone]}`} aria-hidden="true" />
              <span>
                <b>{fact.title}</b>
                <em className="mono">{fact.meta}</em>
              </span>
            </div>
          ))}
          <p className={styles.note}>
            {t.home.problem.note(report.reraId, report.readOn)}
          </p>
        </div>
      </div>
    </section>
  );
}
