import { app as appEn } from "@/lib/i18n/en/app";
import { check as checkEn } from "@/lib/i18n/en/check";
import { report as reportEn } from "@/lib/i18n/en/report";
import { app as appHi } from "@/lib/i18n/hi/app";
import { check as checkHi } from "@/lib/i18n/hi/check";
import { report as reportHi } from "@/lib/i18n/hi/report";

export type Lang = "en" | "hi";

const en = { ...appEn, ...checkEn, report: reportEn };

/** Every piece of interface copy. The Hindi dictionary must have exactly the same keys. */
export type Strings = typeof en;

const hi: Strings = { ...appHi, ...checkHi, report: reportHi };

export const STRINGS: Record<Lang, Strings> = { en, hi };

export const LANG_COOKIE = "neevcheck-lang";

export function isLang(value: string | undefined): value is Lang {
  return value === "en" || value === "hi";
}
