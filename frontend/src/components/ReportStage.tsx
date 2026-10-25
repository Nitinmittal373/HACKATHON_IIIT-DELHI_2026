import Link from "next/link";

import { ScoreRing } from "@/components/ScoreRing";
import type { HeroCard } from "@/lib/heroCard";
import type { Strings } from "@/lib/i18n";
import styles from "./ReportStage.module.css";

const ORB_CLASSES = [styles.o1, styles.o2, styles.o3, styles.o4];

/**
 * The report card that rises into view. It shows the latest real check on NeevCheck, or, before
 * there is one, an empty frame that says where the visitor's report will appear: no made-up numbers.
 */
export function ReportStage({ card, t }: { card: HeroCard | null; t: Strings }) {
  return (
    <div className={styles.stage} id="latest-report">
      <div className={styles.glow} aria-hidden="true" />
      <div className={styles.rise}>{card ? <RealCard card={card} t={t} /> : <EmptyCard t={t} />}</div>
      {card?.orbs.slice(0, ORB_CLASSES.length).map((orb, index) => (
        <div key={orb.bold} className={`${styles.orb} ${ORB_CLASSES[index]}`} aria-hidden="true">
          <span className={`${styles.dot} ${styles[orb.tone]}`} />
          <span>
            <b>{orb.bold}</b> {orb.text}
          </span>
        </div>
      ))}
    </div>
  );
}

function RealCard({ card, t }: { card: HeroCard; t: Strings }) {
  const band = t.report.bands[card.band];
  return (
    <Link
      href={`/report/${card.id}`}
      className={`${styles.card} ${styles.link}`}
      aria-label={t.home.report.ariaLabel(card.name, card.score, band)}
    >
      <div className={styles.top}>
        <span className={`mono ${styles.kicker}`}>{t.home.report.kicker(card.readOn.toUpperCase())}</span>
        <span className={`${styles.band} ${styles[card.band]}`}>{band}</span>
      </div>
      <div className={styles.body}>
        <ScoreRing value={card.score} band={card.band} />
        <div>
          <p className={styles.name}>{card.name}</p>
          <p className={`mono ${styles.id}`}>
            {card.reraId}
            {card.promoter && ` · ${card.promoter}`}
          </p>
          <ul className={styles.drivers}>
            {card.drivers.map((driver, index) => (
              <li key={driver.label} className={styles.driver}>
                <span className={styles.label} title={driver.label}>
                  {driver.label}
                </span>
                <i
                  className={`${styles.bar} ${styles[driver.tone]}`}
                  style={{ ["--fill" as string]: `${driver.fill}%`, ["--delay" as string]: `${index * 0.15}s` }}
                  aria-hidden="true"
                />
                <b>−{driver.points}</b>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </Link>
  );
}

function EmptyCard({ t }: { t: Strings }) {
  return (
    <article className={styles.card} aria-label={t.home.report.skeletonLabel}>
      <div className={styles.top}>
        <span className={`mono ${styles.kicker}`}>{t.home.report.skeletonKicker}</span>
        <span className={`${styles.band} ${styles.placeholderTag}`} aria-hidden="true" />
      </div>
      <div className={styles.body}>
        <div className={styles.placeholderRing} aria-hidden="true" />
        <div>
          <p className={styles.name}>{t.home.report.skeletonTitle}</p>
          <p className={styles.skeletonBody}>{t.home.report.skeletonBody}</p>
          <ul className={styles.drivers} aria-hidden="true">
            {[72, 56, 40].map((width) => (
              <li key={width} className={styles.driver}>
                <span className={styles.placeholderLine} style={{ width: `${width}%` }} />
                <i className={styles.bar} />
                <b />
              </li>
            ))}
          </ul>
        </div>
      </div>
    </article>
  );
}
