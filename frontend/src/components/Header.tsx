"use client";

import Link from "next/link";

import { Logo } from "@/components/Logo";
import { useLang } from "@/lib/LangProvider";
import styles from "./Header.module.css";

export function Header() {
  const { lang, setLang, t } = useLang();

  return (
    <header className={styles.header}>
      <nav className={`wrap ${styles.nav}`} aria-label="Main">
        <Link href="/" aria-label="NeevCheck home" className={styles.home}>
          <Logo />
        </Link>
        <div className={styles.links}>
          <Link href="/#search">{t.nav.check}</Link>
          <Link href="/#sample-report">{t.nav.sample}</Link>
          <Link href="/#how-it-works">{t.nav.how}</Link>
          <Link href="/#sentinel">{t.nav.rwa}</Link>
        </div>
        <div className={styles.lang} role="group" aria-label="Language">
          <button type="button" aria-pressed={lang === "en"} onClick={() => setLang("en")} lang="en">
            EN
          </button>
          <button type="button" aria-pressed={lang === "hi"} onClick={() => setLang("hi")} lang="hi" className="dev">
            हिं
          </button>
        </div>
        <button type="button" className={`btn ${styles.signIn}`}>
          {t.nav.signIn}
        </button>
      </nav>
    </header>
  );
}
