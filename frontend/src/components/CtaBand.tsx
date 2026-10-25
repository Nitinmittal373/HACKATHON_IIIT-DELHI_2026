import Link from "next/link";

import { Glow } from "@/components/Glow";
import styles from "./CtaBand.module.css";

export function CtaBand() {
  return (
    <section className="wrap" style={{ paddingTop: 80, paddingBottom: 100 }} aria-labelledby="cta-title">
      <div className={`${styles.band} rv`}>
        <Glow soft />
        <div className={styles.content}>
          <h2 id="cta-title" className={`h2 ${styles.title}`}>
            Your home deserves
            <br />
            <span className={styles.accent}>a background check.</span>
          </h2>
          <p className={styles.sub}>Free for your first projects. No phone number needed.</p>
          <Link href="/#search" className={`btn btnBig ${styles.button}`}>
            Check a project now
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
