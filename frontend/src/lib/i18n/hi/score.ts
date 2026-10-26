import type { score as English } from "@/lib/i18n/en/score";

/** The Hindi copy has exactly the same keys as the English. */
export const score: typeof English = {
  bands: {
    Low: "कम जोखिम",
    Watch: "निगरानी रखें",
    Elevated: "बढ़ा हुआ जोखिम",
    High: "ज़्यादा जोखिम",
    insufficient_evidence: "अभी पर्याप्त प्रमाण नहीं",
  },
  label: (value, max, band) =>
    value === null ? `नींवस्कोर नहीं दिया गया, ${band}` : `नींवस्कोर ${max} में से ${value}, ${band}`,
  outOf: (max) => `${max} में से`,
  short: (value, band) => (value === null ? band : `नींवस्कोर ${value} · ${band}`),
  dash: "—",
  unrated: (read, total) => `अभी पर्याप्त प्रमाण नहीं · ${total} में से ${read} तरह के रिकॉर्ड पढ़े गए`,
};
