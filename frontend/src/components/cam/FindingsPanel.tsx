import type { Strings } from "@/lib/i18n";
import { findingTone, isSecondaryOk } from "@/lib/verdict";
import type { Finding } from "@/lib/types";
import styles from "./FindingsPanel.module.css";

interface Props {
  findings: Finding[];
  t: Strings;
}

type VerdictLabels = Strings["cam"]["verdict"];

function labelFor(finding: Finding, labels: VerdictLabels): string {
  if (isSecondaryOk(finding)) return labels.secondary;
  return finding.verdict === "red_flag" ? labels.fail : labels[finding.verdict];
}

/** Findings so far, newest on top, each coloured by its verdict and tied to its source. */
export function FindingsPanel({ findings, t }: Props) {
  return (
    <section className={`card ${styles.panel}`} aria-labelledby="findings-title">
      <div className={styles.head}>
        <h2 id="findings-title">{t.cam.findingsTitle}</h2>
        <span className={`mono num ${styles.count}`}>{t.cam.records(findings.length)}</span>
      </div>
      {findings.length === 0 ? (
        <p className={styles.empty}>{t.cam.noFindings}</p>
      ) : (
        <ol className={styles.list} aria-live="polite">
          {findings.map((finding) => (
            <li key={finding.id} className={`${styles.item} tone-${findingTone(finding)}`}>
              <span className={styles.dot} aria-hidden="true" />
              <span className={styles.text}>
                <span className={styles.title}>{finding.title}</span>
                <span className={`mono ${styles.meta}`}>
                  {t.cam.sourceLabels[finding.source]} · {labelFor(finding, t.cam.verdict)}
                </span>
              </span>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
