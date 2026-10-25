import { app as appEn } from "@/lib/i18n/en/app";
import { home as homeEn } from "@/lib/i18n/en/home";
import { check as checkEn } from "@/lib/i18n/en/check";
import { report as reportEn } from "@/lib/i18n/en/report";
import { reports as reportsEn } from "@/lib/i18n/en/reports";
import { alerts as alertsEn, sentinel as sentinelEn } from "@/lib/i18n/en/sentinel";
import { app as appHi } from "@/lib/i18n/hi/app";
import { home as homeHi } from "@/lib/i18n/hi/home";
import { check as checkHi } from "@/lib/i18n/hi/check";
import { report as reportHi } from "@/lib/i18n/hi/report";
import { reports as reportsHi } from "@/lib/i18n/hi/reports";
import { alerts as alertsHi, sentinel as sentinelHi } from "@/lib/i18n/hi/sentinel";

export type Lang = "en" | "hi";

const en = {
  ...appEn,
  ...checkEn,
  home: homeEn,
  report: reportEn,
  reports: reportsEn,
  sentinel: sentinelEn,
  alerts: alertsEn,
};

/** Every piece of interface copy. The Hindi dictionary must have exactly the same keys. */
export type Strings = typeof en;

const hi: Strings = {
  ...appHi,
  ...checkHi,
  home: homeHi,
  report: reportHi,
  reports: reportsHi,
  sentinel: sentinelHi,
  alerts: alertsHi,
};

export const STRINGS: Record<Lang, Strings> = { en, hi };

export const LANG_COOKIE = "neevcheck-lang";

export function isLang(value: string | undefined): value is Lang {
  return value === "en" || value === "hi";
}
