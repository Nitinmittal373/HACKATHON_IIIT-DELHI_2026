import type { Tone } from "@/lib/exampleReport";
import { formatDay } from "@/lib/format";
import type { Lang, Strings } from "@/lib/i18n";
import type { Band, RecentCheck } from "@/lib/types";

export interface CardDriver {
  label: string;
  /** Share of the bar to fill, 0 to 100. */
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
  score: number;
  band: Band;
  readOn: string;
  drivers: CardDriver[];
  orbs: CardOrb[];
}

// A 20-point penalty fills the bar; the biggest single penalties are around 14.
const FILL_PER_POINT = 5;
const SERIOUS_POINTS = 10;

export function heroCard(check: RecentCheck, t: Strings, lang: Lang): HeroCard | null {
  if (check.score === null || check.band === null) return null;
  const readOn = formatDay((check.completed_at ?? check.created_at).slice(0, 10), lang);
  const percent = Math.round((check.confidence ?? 0) * 100);
  const orbs: CardOrb[] = [
    ...(check.registered_on
      ? [{ tone: "ok" as const, bold: "UP-RERA", text: t.home.report.registered(formatDay(check.registered_on, lang)) }]
      : []),
    { tone: "brand", bold: "TinyFish", text: t.home.report.sources(check.sources_read) },
    { tone: percent >= 50 ? "ok" : "warn", bold: `${percent}%`, text: t.home.report.confidence },
  ];
  return {
    id: check.id,
    name: check.project ?? check.rera_id,
    reraId: check.rera_id,
    promoter: check.promoter ?? "",
    score: check.score,
    band: check.band,
    readOn,
    drivers: check.drivers.map((driver) => ({
      label: driver.title,
      fill: Math.min(100, Math.abs(driver.points) * FILL_PER_POINT),
      points: Math.round(Math.abs(driver.points)),
      tone: Math.abs(driver.points) >= SERIOUS_POINTS ? "bad" : "warn",
    })),
    orbs,
  };
}
