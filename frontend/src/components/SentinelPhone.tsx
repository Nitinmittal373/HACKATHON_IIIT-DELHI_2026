import styles from "./SentinelPhone.module.css";

interface Props {
  /** Short project name shown in the alert. */
  project: string;
  score: number;
}

/** Neev Sentinel: a phone lock screen with two alerts, one in English and one in Hindi. */
export function SentinelPhone({ project, score }: Props) {
  return (
    <section className="wrap section" id="sentinel" aria-labelledby="sentinel-title">
      <div className={styles.layout}>
        <div className="rv">
          <div className="eyebrow">Neev Sentinel · coming soon</div>
          <h2 id="sentinel-title" className={`h2 ${styles.title}`}>
            We keep watching after you book
          </h2>
          <p className={styles.lead}>
            Every week we re-read the records for your project and tell you only when something
            changes, in English or <span className="dev">हिंदी</span>.
          </p>
          <dl className={styles.stats}>
            <div>
              <dt>re-checks</dt>
              <dd className="num">Weekly</dd>
            </div>
            <div>
              <dt>spam alerts</dt>
              <dd className="num">0</dd>
            </div>
            <div>
              <dt>languages</dt>
              <dd className="num">2</dd>
            </div>
          </dl>
        </div>

        <figure className={`${styles.phoneWrap} rv`}>
          <div className={styles.phone} role="img" aria-label="Illustration of two Neev Sentinel alerts on a phone lock screen, one in English and one in Hindi">
            <div className={`mono ${styles.top}`}>9:41</div>
            <div className={`num ${styles.time}`}>9:41</div>
            <div className={styles.date}>Monday, 26 October</div>
            <div className={`${styles.card} ${styles.first}`}>
              <div className={styles.cardHead}>
                <span className={styles.appIcon} />
                <b>NeevCheck</b>
                <em>now</em>
              </div>
              <div className={styles.cardBody}>
                <b>{project}</b>
                <br />
                New record: a court order on this builder&apos;s projects. Score unchanged at {score}.
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
          <figcaption className={styles.caption}>Illustration of an alert, not a real one.</figcaption>
        </figure>
      </div>
    </section>
  );
}
