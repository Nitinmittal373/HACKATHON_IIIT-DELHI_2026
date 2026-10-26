import type { Strings } from "@/lib/i18n";
import type { Comparison } from "@/lib/types";
import styles from "./Compare.module.css";

/** One line that names the best project on the records, or says why none can be named. */
export function BestSummary({ comparison, t }: { comparison: Comparison; t: Strings }) {
  const best = comparison.projects.find((project) => project.check_id === comparison.best);
  let text = t.compare.notEnough;
  if (best) text = t.compare.best(best.project.name ?? best.project.rera_id, best.display_score.value);
  else if (comparison.reason === "tie") text = t.compare.tie;

  return (
    <p className={styles.summary} role="status">
      {best && <b>{t.compare.bestTitle}: </b>}
      {text}
    </p>
  );
}
