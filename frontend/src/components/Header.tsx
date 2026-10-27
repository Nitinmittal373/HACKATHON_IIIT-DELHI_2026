"use client";

import Link from "next/link";

import { AccountMenu } from "@/components/AccountMenu";
import { Logo } from "@/components/Logo";
import { useLang } from "@/lib/LangProvider";
import styles from "./Header.module.css";

export function Header() {
  const { lang, setLang, t } = useLang();

  return (
    <header className={styles.header}>
      <nav className={`wrap ${styles.nav}`} aria-label={t.common.mainNav}>
        <Link href="/" aria-label={t.common.homeLabel} className={styles.home}>
          <Logo />
        </Link>
        <div className={styles.links}>
          <Link href="/#search">{t.nav.check}</Link>
          <Link href="/#how-it-works">{t.nav.how}</Link>
          <Link href="/#sentinel">{t.nav.rwa}</Link>
          <Link href="/alerts">{t.nav.alerts}</Link>
        </div>
        <div className={styles.lang} role="group" aria-label={t.common.language}>
          <button type="button" aria-pressed={lang === "en"} onClick={() => setLang("en")} lang="en">
            EN
          </button>
          <button type="button" aria-pressed={lang === "hi"} onClick={() => setLang("hi")} lang="hi" className="dev">
            हिं
          </button>
        </div>
        <AccountMenu />
        {/* Without an account a visitor's checks are kept in this browser and listed here. */}
        <Link href="/reports" className={`btn ${styles.cta}`}>
          {t.nav.reports}
        </Link>
      </nav>
    </header>
  );
}
