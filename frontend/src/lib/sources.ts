import type { SourceName } from "@/lib/types";

/** The six sources in the order the Agent Cam shows them. */
export const SOURCE_ORDER: SourceName[] = [
  "uprera",
  "registry",
  "insolvency",
  "land",
  "consumer",
  "news",
];

interface SourceInfo {
  /** Where a buyer can check this themselves; shown for unread and blocked sources. */
  officialUrl: string;
  /** Host shown in the Agent Cam address bar before a finding names a page. */
  site: string;
}

export const SOURCE_INFO: Record<SourceName, SourceInfo> = {
  uprera: { officialUrl: "https://www.up-rera.in/", site: "up-rera.in" },
  registry: { officialUrl: "https://www.mca.gov.in/", site: "mca.gov.in" },
  insolvency: { officialUrl: "https://nclt.gov.in/", site: "nclt.gov.in" },
  land: { officialUrl: "https://www.noidaauthorityonline.in/", site: "noidaauthorityonline.in" },
  consumer: { officialUrl: "https://e-jagriti.gov.in/advance-case-search", site: "e-jagriti.gov.in" },
  news: { officialUrl: "https://www.supremecourt.gov.in/", site: "news sites" },
};
