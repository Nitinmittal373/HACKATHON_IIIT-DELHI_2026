"use client";

import Link from "next/link";

import { MoreWays } from "@/components/find/MoreWays";
import { SearchBar } from "@/components/SearchBar";
import { SignInHint } from "@/components/SignInHint";
import { Skyline } from "@/components/Skyline";
import { useLang } from "@/lib/LangProvider";
import styles from "./Hero.module.css";

// Examples read from up-rera.in itself.
const CHIPS = ["UPRERAPRJ8334", "Gaur City", "Supertech"];
const WORD_STEP_SECONDS = 0.06;

/** The only centred block on the site: the headline, one line, the search and quick examples. */
export function Hero() {
  const { lang, t } = useLang();
  const words = t.hero.headline;

  return (
    <section className={styles.hero}>
      <Skyline variant="hero" />
      <div className={`wrap ${styles.content}`}>
        <h1 className={`${styles.title} ${lang === "hi" ? `dev ${styles.hindi}` : ""}`}>
          {words.map((word, index) => (
            <span key={`${lang}-${word}`}>
              <span
                className={`${styles.word} ${index === words.length - 1 ? styles.accent : ""}`}
                style={{ animationDelay: `${(index + 1) * WORD_STEP_SECONDS}s` }}
              >
                {word}
              </span>{" "}
            </span>
          ))}
        </h1>

        <p className={styles.subtitle}>{t.hero.subtitle}</p>

        <div className={styles.fadeUp} style={{ animationDelay: "0.5s" }}>
          <SearchBar
            label={t.hero.searchLabel}
            placeholder={t.hero.placeholder}
            submitLabel={t.hero.submit}
          />
        </div>

        <SignInHint className={styles.fadeUp} />

        <div className={styles.fadeUp} style={{ animationDelay: "0.55s" }}>
          <MoreWays />
        </div>

        <div className={`${styles.try} ${styles.fadeUp}`} style={{ animationDelay: "0.6s" }}>
          <span>{t.hero.try}</span>
          {CHIPS.map((query) => (
            <Link
              key={query}
              href={`/check?q=${encodeURIComponent(query)}`}
              prefetch={false}
              className={`${styles.chip} ${/\d/.test(query) ? "mono" : ""}`}
            >
              {query}
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
