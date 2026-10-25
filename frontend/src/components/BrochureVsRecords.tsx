import type { ExampleReport } from "@/lib/exampleReport";
import styles from "./BrochureVsRecords.module.css";

/** Typical sales claims. They are what brokers say, not data. */
const CLAIMS = ["“Possession on time.”", "“Fully approved and registered.”", "“A trusted builder, no issues.”"];

export function BrochureVsRecords({ report }: { report: ExampleReport }) {
  return (
    <section className="wrap section" aria-labelledby="problem-title">
      <div className={`${styles.head} rv`}>
        <div className="eyebrow">The problem</div>
        <h2 id="problem-title" className={`h2 ${styles.title}`}>
          The brochure tells you a story. <span className={styles.underline}>The records tell you the truth.</span>
        </h2>
      </div>

      <div className={`${styles.versus} rv`}>
        <div className={styles.heard}>
          <div className={`mono ${styles.label}`}>WHAT YOU HEAR</div>
          {CLAIMS.map((claim, index) => (
            <p key={claim} className={styles.claim} style={{ ["--d" as string]: `${index * 0.15}s` }}>
              {claim}
            </p>
          ))}
        </div>
        <div className={styles.mid} aria-hidden="true">
          <span>vs</span>
        </div>
        <div className={styles.records}>
          <div className={`mono ${styles.label} ${styles.recordsLabel}`}>WHAT THE RECORDS SAY</div>
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
            From the live check of {report.reraId}, read {report.readOn}.
          </p>
        </div>
      </div>
    </section>
  );
}
