import Link from "next/link";

import { Glow } from "@/components/Glow";
import type { Strings } from "@/lib/i18n";
import styles from "./CtaBand.module.css";

export function CtaBand({ t }: { t: Strings }) {
  return (
    <section className="wrap" style={{ paddingTop: 80, paddingBottom: 100 }} aria-labelledby="cta-title">
      <div className={`${styles.band} rv`}>
        <Glow soft />
        <div className={styles.content}>
          <h2 id="cta-title" className={`h2 ${styles.title}`}>
            {t.home.cta.titleStart}
            <br />
            <span className={styles.accent}>{t.home.cta.titleEnd}</span>
          </h2>
          <p className={styles.sub}>{t.home.cta.sub}</p>
          <Link href="/#search" className={`btn btnBig ${styles.button}`}>
            {t.home.cta.button}
            <svg
              className="arrow"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M5 12h14M13 6l6 6-6 6" />
            </svg>
          </Link>
        </div>
      </div>
    </section>
  );
}
