import Link from "next/link";

import { getStrings } from "@/lib/i18n/server";
import styles from "./Footer.module.css";

/** A short footer: what NeevCheck is, and a link to every page. */
export async function Footer() {
  const { t } = await getStrings();
  const links = [
    { href: "/check", label: t.nav.check },
    { href: "/how-it-works", label: t.nav.how },
    { href: "/rwa", label: t.nav.rwa },
    { href: "/alerts", label: t.nav.alerts },
    { href: "/privacy", label: t.privacy.footerLink },
  ];
  return (
    <footer className={styles.footer}>
      <div className={`wrap ${styles.row}`}>
        <span>
          {t.home.footer.left} <span className={styles.note}>· {t.home.footer.note}</span>
        </span>
        <nav aria-label={t.home.footer.right} className={styles.links}>
          {links.map((link) => (
            <Link key={link.href} href={link.href} className={styles.link}>
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
    </footer>
  );
}
