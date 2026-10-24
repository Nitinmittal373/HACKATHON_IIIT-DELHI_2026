"use client";

import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";

export type Lang = "en" | "hi";

// Key interface text in English and Hindi. Evidence text stays in the language of its source.
const DICT = {
  "nav.how": { en: "How it works", hi: "यह कैसे काम करता है" },
  "nav.score": { en: "NeevScore", hi: "नींव स्कोर" },
  "nav.method": { en: "Methodology", hi: "पद्धति" },
  "nav.faq": { en: "FAQ", hi: "सवाल" },
  "nav.app": { en: "Open app", hi: "ऐप खोलें" },
  "cta.check": { en: "Check a project", hi: "प्रोजेक्ट जाँचें" },
  "cta.run": { en: "Run a check", hi: "जाँच करें" },
  "hero.badge": { en: "Five web agents read public records in about two minutes", hi: "पाँच वेब एजेंट लगभग दो मिनट में सार्वजनिक रिकॉर्ड पढ़ते हैं" },
  "hero.title": { en: "Know your builder before you pay the booking amount.", hi: "बुकिंग से पहले अपने बिल्डर को जानिए।" },
  "hero.sub": {
    en: "NeevCheck reads UP-RERA, company records, insolvency orders, land-authority dues and the news, then gives you one explainable score with a source for every claim.",
    hi: "NeevCheck UP-RERA, कंपनी रिकॉर्ड, दिवालियापन आदेश, प्राधिकरण बकाया और खबरें पढ़कर एक स्कोर देता है। हर दावे के साथ उसका स्रोत।",
  },
  "hero.placeholder": { en: "Project name, UP-RERA number or builder", hi: "प्रोजेक्ट का नाम, UP-RERA नंबर या बिल्डर" },
  "app.projects": { en: "My projects", hi: "मेरे प्रोजेक्ट" },
  "app.warroom": { en: "War Room", hi: "वॉर रूम" },
  "app.reports": { en: "Reports", hi: "रिपोर्ट" },
  "app.compare": { en: "Compare", hi: "तुलना" },
  "app.watch": { en: "Watch & alerts", hi: "निगरानी और अलर्ट" },
  "app.newcheck": { en: "New check", hi: "नई जाँच" },
  "app.method": { en: "How we score", hi: "हम स्कोर कैसे देते हैं" },
  "report.why": { en: "Why this score", hi: "यह स्कोर क्यों" },
  "report.next": { en: "What you can do next", hi: "आप आगे क्या कर सकते हैं" },
  "report.evidence": { en: "Evidence", hi: "सबूत" },
  "report.calc": { en: "How this score was calculated", hi: "यह स्कोर कैसे निकाला गया" },
  "report.checked": { en: "What we checked", hi: "हमने क्या जाँचा" },
  "disclaimer": {
    en: "A risk indicator built from public records. Not a credit rating or legal advice.",
    hi: "सार्वजनिक रिकॉर्ड पर आधारित जोखिम संकेत। यह क्रेडिट रेटिंग या कानूनी सलाह नहीं है।",
  },
} satisfies Record<string, Record<Lang, string>>;

export type TKey = keyof typeof DICT;

const Ctx = createContext<{ lang: Lang; setLang: (l: Lang) => void; t: (k: TKey) => string }>({
  lang: "en",
  setLang: () => {},
  t: (k) => DICT[k].en,
});

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>("en");
  useEffect(() => {
    try {
      const saved = localStorage.getItem("neev-lang");
      if (saved === "hi" || saved === "en") setLangState(saved);
    } catch {
      /* storage blocked: keep English */
    }
  }, []);
  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);
  const setLang = useCallback((l: Lang) => {
    setLangState(l);
    try {
      localStorage.setItem("neev-lang", l);
    } catch {
      /* ignore */
    }
  }, []);
  const t = useCallback((k: TKey) => DICT[k][lang], [lang]);
  return <Ctx.Provider value={{ lang, setLang, t }}>{children}</Ctx.Provider>;
}

export const useLang = () => useContext(Ctx);
