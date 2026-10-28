import { account as accountEn } from "@/lib/i18n/en/account";
import { app as appEn } from "@/lib/i18n/en/app";
import { home as homeEn } from "@/lib/i18n/en/home";
import { pages as pagesEn } from "@/lib/i18n/en/pages";
import { insights as insightsEn } from "@/lib/i18n/en/insights";
import { check as checkEn } from "@/lib/i18n/en/check";
import { complaint as complaintEn } from "@/lib/i18n/en/complaint";
import { credit as creditEn } from "@/lib/i18n/en/credit";
import { legal as legalEn } from "@/lib/i18n/en/legal";
import { family as familyEn } from "@/lib/i18n/en/family";
import { find as findEn } from "@/lib/i18n/en/find";
import { compare as compareEn } from "@/lib/i18n/en/compare";
import { privacy as privacyEn } from "@/lib/i18n/en/privacy";
import { report as reportEn } from "@/lib/i18n/en/report";
import { reports as reportsEn } from "@/lib/i18n/en/reports";
import { score as scoreEn } from "@/lib/i18n/en/score";
import { alerts as alertsEn, sentinel as sentinelEn } from "@/lib/i18n/en/sentinel";
import { account as accountHi } from "@/lib/i18n/hi/account";
import { app as appHi } from "@/lib/i18n/hi/app";
import { home as homeHi } from "@/lib/i18n/hi/home";
import { pages as pagesHi } from "@/lib/i18n/hi/pages";
import { insights as insightsHi } from "@/lib/i18n/hi/insights";
import { check as checkHi } from "@/lib/i18n/hi/check";
import { complaint as complaintHi } from "@/lib/i18n/hi/complaint";
import { credit as creditHi } from "@/lib/i18n/hi/credit";
import { legal as legalHi } from "@/lib/i18n/hi/legal";
import { family as familyHi } from "@/lib/i18n/hi/family";
import { find as findHi } from "@/lib/i18n/hi/find";
import { compare as compareHi } from "@/lib/i18n/hi/compare";
import { privacy as privacyHi } from "@/lib/i18n/hi/privacy";
import { report as reportHi } from "@/lib/i18n/hi/report";
import { reports as reportsHi } from "@/lib/i18n/hi/reports";
import { score as scoreHi } from "@/lib/i18n/hi/score";
import { alerts as alertsHi, sentinel as sentinelHi } from "@/lib/i18n/hi/sentinel";

export type Lang = "en" | "hi";

const en = {
  ...appEn,
  ...checkEn,
  account: accountEn,
  home: homeEn,
  pages: pagesEn,
  credit: creditEn,
  complaint: complaintEn,
  family: familyEn,
  find: findEn,
  legal: legalEn,
  privacy: privacyEn,
  report: reportEn,
  reports: reportsEn,
  score: scoreEn,
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
  account: accountHi,
  home: homeHi,
  pages: pagesHi,
  credit: creditHi,
  complaint: complaintHi,
  family: familyHi,
  find: findHi,
  legal: legalHi,
  privacy: privacyHi,
  report: reportHi,
  reports: reportsHi,
  score: scoreHi,
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
