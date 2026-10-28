import type { home as en } from "@/lib/i18n/en/home";

export const home: typeof en = {
  recent: {
    accountTitle: "आपकी हाल की जाँचें",
    accountLead: "आपके खाते में सहेजी गई आख़िरी जाँचें। यह सूची सिर्फ़ आप देखते हैं। हर एक अपनी पूरी रिपोर्ट और हर स्रोत के साथ खुलती है।",
    browserTitle: "इस ब्राउज़र में जाँचे गए",
    browserLead: "बिना साइन इन किए आपने यहाँ जो जाँचें शुरू कीं। ये इसी ब्राउज़र में रहती हैं। इन्हें अपने खाते में रखने के लिए साइन इन करें।",
    item: (name: string, score: number | null, band: string, date: string) =>
      score === null
        ? `${name}: अभी पर्याप्त प्रमाण नहीं, ${date} को जाँचा गया`
        : `${name}: NeevScore ${score}, ${band}, ${date} को जाँचा गया`,
  },
  footer: {
    left: "NeevCheck · सार्वजनिक रिकॉर्ड, लाइव पढ़े गए",
    note: "क्रेडिट रेटिंग नहीं",
    right: "सिर्फ़ UP-RERA प्रोजेक्ट",
  },
};
