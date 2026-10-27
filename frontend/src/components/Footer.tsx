import Link from "next/link";

import { getStrings } from "@/lib/i18n/server";
import styles from "./Footer.module.css";

export async function Footer() {
  const { t } = await getStrings();
  return (
    <footer className={styles.footer}>
      <div className={`wrap ${styles.row}`}>
        <span>
          {t.home.footer.left} <span className={styles.note}>· {t.home.footer.note}</span>
        </span>
        <span>
          {t.home.footer.right} ·{" "}
          <Link href="/privacy" className={styles.link}>
            {t.privacy.footerLink}
          </Link>
        </span>
      </div>
    </footer>
  );
}
