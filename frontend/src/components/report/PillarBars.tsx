import type { Strings } from "@/lib/i18n";
import type { ScoreV2 } from "@/lib/types";
import styles from "./PillarBars.module.css";

/** One bar per pillar: its weight, and how much of it was lost. A bar is risk, not a grade. */
export function PillarBars({ score, t }: { score: ScoreV2; t: Strings }) {
  const unread = new Set(score.pillars_unread);
  const costOf = (pillar: ScoreV2["pillars"][number]): string => {
    if (unread.has(pillar.id)) return t.credit.unread;
    const lost = Math.abs(Math.round(pillar.points));
    const cost = pillar.penalty ? t.credit.pillarCost(pillar.penalty, lost) : t.credit.noPenalty;
    if (!pillar.partly_read) return cost;
    const covered = t.credit.partlyCovers[pillar.partly_read] ?? pillar.partly_read;
    return `${t.credit.partlyRead(covered)} · ${cost}`;
  };

  return (
    <section aria-labelledby="pillars-title">
      <h3 id="pillars-title" className={styles.title}>
        {t.credit.pillarsTitle}
      </h3>
      <p className={styles.lead}>{t.credit.pillarsLead}</p>
      <ul className={styles.list}>
        {score.pillars.map((pillar) => {
          return (
            <li key={pillar.id} className={styles.row}>
              <div className={styles.top}>
                <span className={styles.name}>{t.credit.pillars[pillar.id]}</span>
                <span className={`mono ${styles.weight}`}>
                  {t.credit.weight(Math.round(pillar.weight * 100))}
                </span>
              </div>
              <div
                className={styles.track}
                role="meter"
                aria-label={t.credit.pillars[pillar.id]}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={pillar.penalty}
                aria-valuetext={costOf(pillar)}
              >
                <div className={styles.fill} style={{ width: `${pillar.penalty}%` }} />
              </div>
              <span className={styles.cost}>{costOf(pillar)}</span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
