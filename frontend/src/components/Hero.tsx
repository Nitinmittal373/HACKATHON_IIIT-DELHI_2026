"use client";

import Link from "next/link";

import { Glow } from "@/components/Glow";
import { MoreWays } from "@/components/find/MoreWays";
import { ReportStage } from "@/components/ReportStage";
import { SearchBar } from "@/components/SearchBar";
import { Skyline } from "@/components/Skyline";
import { heroCard } from "@/lib/heroCard";
import { useLang } from "@/lib/LangProvider";
import { useMeta } from "@/lib/MetaProvider";
import { useRecentChecks } from "@/lib/useRecentChecks";
import { useStates } from "@/lib/useStates";
import styles from "./Hero.module.css";

// Real numbers read from each portal, one per state, taken from GET /api/states.
const CHIP_STATES = ["UP", "MH", "HR", "KA"];
const FALLBACK_CHIPS = ["UPRERAPRJ8334", "Gaur City", "Supertech"];
const WORD_STEP_SECONDS = 0.06;

/** Search-first hero: headline, search, quick examples and the latest real report. */
export function Hero() {
  const { lang, t } = useLang();
  const meta = useMeta();
  const words = t.hero.headline;
  const recent = useRecentChecks();
  const load = useStates();
  const chips =
    load.status === "ready"
      ? CHIP_STATES.flatMap((code) => load.states.find((s) => s.code === code)?.examples.slice(0, 1) ?? [])
      : FALLBACK_CHIPS;
  const latest = recent.status === "ready" ? recent.checks[0] : undefined;
  const card = latest ? heroCard(latest, t, lang, meta) : null;

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

        <div className={styles.fadeUp} style={{ animationDelay: "0.55s" }}>
          <MoreWays />
        </div>

        <div className={`${styles.try} ${styles.fadeUp}`} style={{ animationDelay: "0.6s" }}>
          <span>{t.hero.try}</span>
          {chips.map((query) => (
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

        <ReportStage card={card} t={t} />
        <p className={styles.note}>
          {card && (
            <>
              {t.home.report.latestNote(card.readOn)}{" "}
              <Link href={`/report/${card.id}`} className={styles.noteLink}>
                {t.home.report.open}
              </Link>
            </>
          )}
          {recent.status === "ready" && !card && t.home.report.skeletonNote}
        </p>
      </div>
    </section>
  );
}
