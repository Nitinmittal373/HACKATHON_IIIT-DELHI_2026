import type { Strings } from "@/lib/i18n";
import { actionPlan } from "@/lib/actionPlan";
import type { Report } from "@/lib/types";
import styles from "./ActionPlan.module.css";

export function ActionPlan({ report, t }: { report: Report; t: Strings }) {
  return (
    <section className={`card ${styles.card}`} aria-labelledby="plan-title">
      <h2 id="plan-title" className={styles.title}>
        {t.report.planTitle}
      </h2>
      <ol className={styles.list}>
        {actionPlan(report).map((key, index) => (
          <li key={key} className={styles.step}>
            <span className={`num ${styles.number}`}>{index + 1}</span>
            <span>
              <b>{t.report.plan[key].bold}</b> {t.report.plan[key].rest}
            </span>
          </li>
        ))}
      </ol>
    </section>
  );
}
