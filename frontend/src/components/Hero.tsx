"use client";

import Link from "next/link";

import { Glow } from "@/components/Glow";
import { ReportStage } from "@/components/ReportStage";
import { SearchBar } from "@/components/SearchBar";
import { Skyline } from "@/components/Skyline";
import type { ExampleReport } from "@/lib/exampleReport";
import { useLang } from "@/lib/LangProvider";
import styles from "./Hero.module.css";

const TRY_THESE = ["UPRERAPRJ8334", "Gaur City", "Supertech"];
const WORD_STEP_SECONDS = 0.06;

/** Search-first hero: headline, search, quick examples and the rising report card. */
export function Hero({ report }: { report: ExampleReport }) {
  const { lang, t } = useLang();
  const words = t.hero.headline;

  return (
    <section className={styles.hero}>
      <Glow dots />
      <Skyline variant="hero" />
      <div className={`wrap ${styles.content}`}>
        <div className={`${styles.pill} ${styles.fadeUp}`}>
          <span className={styles.live} aria-hidden="true" />
          {t.hero.pill}
        </div>

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

        <div className={`${styles.try} ${styles.fadeUp}`} style={{ animationDelay: "0.6s" }}>
          <span>{t.hero.try}</span>
          {TRY_THESE.map((query) => (
            <Link
              key={query}
              href={`/check?q=${encodeURIComponent(query)}`}
              prefetch={false}
              className={`${styles.chip} ${query.startsWith("UPRERA") ? "mono" : ""}`}
            >
              {query}
            </Link>
          ))}
        </div>

        <ReportStage report={report} t={t} />
        <p className={styles.note}>
          {t.home.exampleNote(report.reraId, report.readOn)}
        </p>
      </div>
    </section>
  );
}
