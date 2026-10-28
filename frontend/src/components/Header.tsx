"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { AccountMenu } from "@/components/AccountMenu";
import { Logo } from "@/components/Logo";
import { useLang } from "@/lib/LangProvider";
import styles from "./Header.module.css";

const PAGES = [
  { href: "/check", label: "check" },
  { href: "/how-it-works", label: "how" },
  { href: "/rwa", label: "rwa" },
  { href: "/alerts", label: "alerts" },
] as const;

export function Header() {
  const { lang, setLang, t } = useLang();
  const pathname = usePathname();

  return (
    <header className={styles.header}>
      <nav className={`wrap ${styles.nav}`} aria-label={t.common.mainNav}>
        <Link href="/" aria-label={t.common.homeLabel} className={styles.home}>
          <Logo />
        </Link>
        <div className={styles.links}>
          {PAGES.map(({ href, label }) => {
            const current = pathname === href || pathname.startsWith(`${href}/`);
            return (
              <Link key={href} href={href} aria-current={current ? "page" : undefined}>
                {t.nav[label]}
              </Link>
            );
          })}
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
