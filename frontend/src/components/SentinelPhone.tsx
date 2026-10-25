import type { Strings } from "@/lib/i18n";
import styles from "./SentinelPhone.module.css";

interface Props {
  /** Short project name shown in the alert. */
  project: string;
  score: number;
  t: Strings;
}

/** Neev Sentinel: a phone lock screen with two alerts, one in English and one in Hindi. */
export function SentinelPhone({ project, score, t }: Props) {
  return (
    <section className="wrap section" id="sentinel" aria-labelledby="sentinel-title">
      <div className={styles.layout}>
        <div className="rv">
          <div className="eyebrow">{t.home.sentinel.eyebrow}</div>
          <h2 id="sentinel-title" className={`h2 ${styles.title}`}>
            {t.home.sentinel.title}
          </h2>
          <p className={styles.lead}>
            {t.home.sentinel.lead}
          </p>
          <dl className={styles.stats}>
            {t.home.sentinel.stats.map(([label, value]) => (
              <div key={label}>
                <dt>{label}</dt>
                <dd className="num">{value}</dd>
              </div>
            ))}
          </dl>
        </div>

        <figure className={`${styles.phoneWrap} rv`}>
          <div className={styles.phone} role="img" aria-label={t.home.sentinel.aria}>
            <div className={`mono ${styles.top}`}>9:41</div>
            <div className={`num ${styles.time}`}>9:41</div>
            <div className={styles.date}>{t.home.sentinel.date}</div>
            <div className={`${styles.card} ${styles.first}`}>
              <div className={styles.cardHead}>
                <span className={styles.appIcon} />
                <b>NeevCheck</b>
                <em>{t.home.sentinel.now}</em>
              </div>
              <div className={styles.cardBody}>
                <b>{project}</b>
                <br />
                {t.home.sentinel.alert(score)}
              </div>
            </div>
            <div className={`${styles.card} ${styles.second} dev`}>
              <div className={styles.cardHead}>
                <span className={styles.appIcon} />
                <b>NeevCheck</b>
                <em>अभी</em>
              </div>
              <div className={styles.cardBody}>
                <b>नई जानकारी</b>
                <br />
                आपके प्रोजेक्ट का रिकॉर्ड बदला है।
              </div>
            </div>
          </div>
          <figcaption className={styles.caption}>{t.home.sentinel.caption}</figcaption>
        </figure>
      </div>
    </section>
  );
}
