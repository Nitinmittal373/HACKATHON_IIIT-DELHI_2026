import type { Lang } from "@/lib/i18n";

const LOCALES: Record<Lang, string> = { en: "en-GB", hi: "hi-IN" };
const HOUR_MS = 3_600_000;

/** "2017-08-09" -> "09 Aug 2017". Dates without a time are shown exactly as recorded. */
export function formatDay(day: string, lang: Lang): string {
  const date = new Date(`${day}T00:00:00Z`);
  if (Number.isNaN(date.getTime())) return day;
  return new Intl.DateTimeFormat(LOCALES[lang], {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(date);
}

/** The clock time of a moment, in Indian time, as the records are dated. */
export function formatTime(moment: string, lang: Lang): string | null {
  const date = new Date(moment);
  if (Number.isNaN(date.getTime())) return null;
  return new Intl.DateTimeFormat(LOCALES[lang], {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "Asia/Kolkata",
  }).format(date);
}

/** The calendar day of a moment in Indian time, such as when a limit opens again. */
export function indianDay(moment: string, lang: Lang): string {
  const date = new Date(moment);
  if (Number.isNaN(date.getTime())) return moment;
  return new Intl.DateTimeFormat(LOCALES[lang], {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "Asia/Kolkata",
  }).format(date);
}

export function dayOf(moment: string, lang: Lang): string {
  return formatDay(moment.slice(0, 10), lang);
}

export function hoursSince(moment: string, now: number = Date.now()): number {
  return Math.max(0, Math.floor((now - new Date(moment).getTime()) / HOUR_MS));
}
