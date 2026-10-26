import { app as appEn } from "@/lib/i18n/en/app";
import { home as homeEn } from "@/lib/i18n/en/home";
import { insights as insightsEn } from "@/lib/i18n/en/insights";
import { check as checkEn } from "@/lib/i18n/en/check";
import { complaint as complaintEn } from "@/lib/i18n/en/complaint";
import { credit as creditEn } from "@/lib/i18n/en/credit";
import { family as familyEn } from "@/lib/i18n/en/family";
import { compare as compareEn } from "@/lib/i18n/en/compare";
import { report as reportEn } from "@/lib/i18n/en/report";
import { reports as reportsEn } from "@/lib/i18n/en/reports";
import { alerts as alertsEn, sentinel as sentinelEn } from "@/lib/i18n/en/sentinel";
import { app as appHi } from "@/lib/i18n/hi/app";
import { home as homeHi } from "@/lib/i18n/hi/home";
import { insights as insightsHi } from "@/lib/i18n/hi/insights";
import { check as checkHi } from "@/lib/i18n/hi/check";
import { complaint as complaintHi } from "@/lib/i18n/hi/complaint";
import { credit as creditHi } from "@/lib/i18n/hi/credit";
import { family as familyHi } from "@/lib/i18n/hi/family";
import { compare as compareHi } from "@/lib/i18n/hi/compare";
import { report as reportHi } from "@/lib/i18n/hi/report";
import { reports as reportsHi } from "@/lib/i18n/hi/reports";
import { alerts as alertsHi, sentinel as sentinelHi } from "@/lib/i18n/hi/sentinel";

export type Lang = "en" | "hi";

const en = {
  ...appEn,
  ...checkEn,
  home: homeEn,
  credit: creditEn,
  complaint: complaintEn,
  family: familyEn,
  report: reportEn,
  reports: reportsEn,
  compare: compareEn,
  insights: insightsEn,
  sentinel: sentinelEn,
  alerts: alertsEn,
};

/** Every piece of interface copy. The Hindi dictionary must have exactly the same keys. */
export type Strings = typeof en;

const hi: Strings = {
  ...appHi,
  ...checkHi,
  home: homeHi,
  credit: creditHi,
  complaint: complaintHi,
  family: familyHi,
  report: reportHi,
  reports: reportsHi,
  compare: compareHi,
  insights: insightsHi,
  sentinel: sentinelHi,
  alerts: alertsHi,
};

export const STRINGS: Record<Lang, Strings> = { en, hi };

export const LANG_COOKIE = "neevcheck-lang";

export function isLang(value: string | undefined): value is Lang {
  return value === "en" || value === "hi";
}
