"use client";

import { motion } from "motion/react";

import { Bar, Badge, Card, Eyebrow } from "@/components/ui/primitives";
import { useLang } from "@/lib/i18n";
import type { Score } from "@/lib/types";
import { bandColor, bandTone, cn } from "@/lib/utils";

const MIN = 300;
const MAX = 900;
const frac = (score: number) => (score - MIN) / (MAX - MIN);
const hasNumber = (band: string) => band !== "Not enough data";

/** Circular NeevScore. A band of "Not enough data" never shows a number. */
export function ScoreRing({ score, band, size = 120, stroke = 9 }: { score: number; band: string; size?: number; stroke?: number }) {
  const r = 50 - stroke / 2 - 1;
  const c = 2 * Math.PI * r;
  const show = hasNumber(band);
  const target = c * (1 - (show ? frac(score) : 0));
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox="0 0 100 100" role="img" aria-label={show ? `NeevScore ${score} of 900, ${band}` : band}>
        <circle cx="50" cy="50" r={r} fill="none" stroke="var(--track)" strokeWidth={stroke} />
        <motion.circle
          cx="50" cy="50" r={r} fill="none" stroke={bandColor(band)} strokeWidth={stroke} strokeLinecap="round"
          strokeDasharray={c} initial={{ strokeDashoffset: c }} animate={{ strokeDashoffset: target }}
          transition={{ duration: 1.4, ease: [0.2, 0.8, 0.2, 1] }} transform="rotate(-90 50 50)"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="tabular font-extrabold leading-none tracking-tight" style={{ fontSize: size * 0.26 }}>
          {show ? score : "–"}
        </span>
        <span className="mt-1 text-[11px] text-faint">{show ? "of 900" : "no score"}</span>
      </div>
    </div>
  );
}

/** Half-circle gauge used in hero cards. */
export function ScoreGauge({ score, band, width = 220 }: { score: number; band: string; width?: number }) {
  const len = Math.PI * 80;
  const show = hasNumber(band);
  return (
    <div className="relative mx-auto" style={{ width, height: width * 0.56 }}>
      <svg width={width} height={width * 0.56} viewBox="0 0 200 112" role="img" aria-label={show ? `NeevScore ${score} of 900` : band}>
        <path d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke="var(--track)" strokeWidth="14" strokeLinecap="round" />
        <motion.path
          d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke={bandColor(band)} strokeWidth="14" strokeLinecap="round"
          strokeDasharray={len} initial={{ strokeDashoffset: len }} animate={{ strokeDashoffset: len * (1 - (show ? frac(score) : 0)) }}
          transition={{ duration: 1.4, ease: [0.2, 0.8, 0.2, 1] }}
        />
      </svg>
      <div className="absolute inset-x-0 bottom-0 text-center">
        <div className="tabular text-5xl font-extrabold leading-none tracking-tight">{show ? score : "–"}</div>
        <div className="mt-1 text-xs text-faint">{show ? "of 900" : "no score"}</div>
      </div>
    </div>
  );
}

export function BandBadge({ band, className }: { band: string; className?: string }) {
  return (
    <Badge tone={bandTone(band)} className={cn("text-[13px]", className)}>
      {band}
    </Badge>
  );
}

const PILLAR_ORDER = ["P1_regulatory", "P3_legal_insolvency", "P2_track_record", "P4_corporate_health", "P5_land_authority", "P6_sentiment"];

export function PillarBars({ score }: { score: Score }) {
  return (
    <div className="flex flex-col gap-3 text-[13px]">
      {PILLAR_ORDER.filter((k) => score.pillars[k]).map((k) => {
        const p = score.pillars[k];
        const color = p.penalty >= 80 ? "#EF5A4C" : p.penalty >= 40 ? "#F2B84B" : "#4FC1A6";
        return (
          <div key={k}>
            <div className="flex justify-between gap-3">
              <span>
                {p.name} <span className="text-faint">· {Math.round(p.weight * 100)}%</span>
              </span>
              <span className={cn("tabular font-mono", !p.checked && "text-faint")}>{p.checked ? `${p.penalty}/100` : "not checked"}</span>
            </div>
            <Bar value={p.checked ? p.penalty : 0} color={color} className="mt-1.5" />
          </div>
        );
      })}
      <p className="text-[11px] text-faint">Bars show penalty: 0 is clean, 100 is worst.</p>
    </div>
  );
}

/** The "show your working" panel: anyone can reproduce the score from it. */
export function ScoreCalculation({ score }: { score: Score }) {
  const { t } = useLang();
  const terms = PILLAR_ORDER.map((k) => score.pillars[k])
    .filter((p) => p && p.penalty > 0)
    .map((p) => `${p.weight.toFixed(2)} × ${p.penalty}`);
  const capped = score.hard_stop && score.score < score.formula_score;
  return (
    <Card className="p-5">
      <Eyebrow>{t("report.calc")}</Eyebrow>
      <dl className="mt-3 grid grid-cols-[1fr_auto] gap-x-4 gap-y-2 font-mono text-[12.5px]">
        <dt className="text-muted">Start</dt>
        <dd className="text-right">900</dd>
        <dt className="text-muted">− 6 × weighted penalty ({score.weighted_penalty})</dt>
        <dd className="text-right">−{Math.round(score.weighted_penalty * 6)}</dd>
        <dt className="text-muted">Formula score</dt>
        <dd className="text-right">{score.formula_score}</dd>
        {capped && (
          <>
            <dt className="text-high-fg">Hard stop {score.hard_stop_code} · cap at 449</dt>
            <dd className="text-right text-high-fg">−{score.formula_score - score.score}</dd>
          </>
        )}
        <dt className="border-t border-line pt-2 font-semibold">Shown</dt>
        <dd className="border-t border-line pt-2 text-right font-bold">{hasNumber(score.band) ? score.score : "–"}</dd>
      </dl>
      <p className="mt-3 text-xs leading-relaxed text-faint">
        Weighted penalty = {terms.length ? terms.join(" + ") : "0"}. Same records always give the same score. Formula v{score.version}.
      </p>
    </Card>
  );
}
