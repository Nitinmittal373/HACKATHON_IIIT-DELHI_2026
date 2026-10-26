import type { Tone } from "@/lib/exampleReport";
import { formatDay } from "@/lib/format";
import type { Lang, Strings } from "@/lib/i18n";
import { reasonLabel } from "@/lib/scoreV2";
import type { DisplayScore, Meta, RecentCheck } from "@/lib/types";

export interface CardDriver {
  label: string;
  /** Share of the bar to fill, in percent. */
  fill: number;
  points: number;
  tone: Tone;
}

export interface CardOrb {
  tone: Tone;
  bold: string;
  text: string;
}

/** What the home page's report card shows: a real finished check, nothing made up. */
export interface HeroCard {
  id: string;
  name: string;
  reraId: string;
  promoter: string;
  display: DisplayScore;
  /** The score in words for a screen reader, with the scale from /api/meta. */
  scoreLabel: string;
  readOn: string;
  drivers: CardDriver[];
  orbs: CardOrb[];
}

// A reason that costs a tenth of the whole scale is drawn as serious.
const SERIOUS_SHARE = 0.1;
const MIN_FILL = 8;

export function heroCard(check: RecentCheck, t: Strings, lang: Lang, meta: Meta): HeroCard | null {
  const display = check.display_score;
  if (display === null) return null;
  const readOn = formatDay((check.completed_at ?? check.created_at).slice(0, 10), lang);
  const percent = Math.round(display.confidence * 100);
  const orbs: CardOrb[] = [
    ...(check.registered_on
      ? [{ tone: "ok" as const, bold: "UP-RERA", text: t.home.report.registered(formatDay(check.registered_on, lang)) }]
      : []),
    { tone: "brand", bold: "TinyFish", text: t.home.report.sources(check.sources_read) },
    { tone: percent >= 50 ? "ok" : "warn", bold: `${percent}%`, text: t.home.report.confidence },
  ];
  const biggest = Math.max(...check.reasons.map((reason) => Math.abs(reason.points)), 1);
  const serious = (meta.scale.max - meta.scale.min) * SERIOUS_SHARE;
  return {
    id: check.id,
    name: check.project ?? check.rera_id,
    reraId: check.rera_id,
    promoter: check.promoter ?? "",
    display,
    scoreLabel: t.score.label(display.value, meta.scale.max, t.score.bands[display.band]),
    readOn,
    drivers: check.reasons.map((reason) => ({
      label: reasonLabel(reason, t.credit.codes, lang),
      fill: Math.max(MIN_FILL, (Math.abs(reason.points) / biggest) * 100),
      points: Math.round(Math.abs(reason.points)),
      tone: Math.abs(reason.points) >= serious ? "bad" : "warn",
    })),
    orbs,
  };
}
