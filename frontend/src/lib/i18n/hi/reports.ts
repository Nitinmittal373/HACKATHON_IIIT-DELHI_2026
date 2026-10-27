import type { reports as en } from "@/lib/i18n/en/reports";

export const reports: typeof en = {
  title: "मेरी रिपोर्टें",
  lead: "बिना साइन इन किए आपने इस ब्राउज़र में जो जाँचें शुरू कीं। ये यहीं रहती हैं। रिपोर्टें अपने खाते में रखने के लिए साइन इन करें।",
  loading: "आपकी रिपोर्टें लोड हो रही हैं…",
  emptyTitle: "अभी कोई रिपोर्ट नहीं",
  emptyBody: "अपनी पहली लाइव जाँच के लिए कोई प्रोजेक्ट खोजें। आपकी हर जाँच यहाँ दिखेगी।",
  status: {
    queued: "चल रही है",
    running: "चल रही है",
    completed: "पूरी",
    failed: "विफल",
  },
  checkedOn: (date: string) => `${date} को जाँचा गया`,
  noScore: "कोई स्कोर नहीं",
  noScoreFailed: "UP-RERA पढ़ा नहीं जा सका, इसलिए कोई स्कोर नहीं है।",
  noScoreRunning: "एजेंट अभी रिकॉर्ड पढ़ रहे हैं।",
  open: "खोलें",
  compare: "तुलना करें",
  inCompare: "तुलना में",
  recheck: "फिर जाँचें",
  rechecking: "शुरू हो रही है…",
  remove: "हटाएँ",
  actionsFor: (name: string) => `${name} के लिए विकल्प`,
  compareCount: (count: number) => `तुलना के लिए 3 में से ${count} चुने गए`,
  compareHint: "साथ-साथ तुलना के लिए दो या तीन पूरी जाँचें चुनें।",
  compareGo: "प्रोजेक्ट की तुलना करें",
  compareFull: "एक बार में अधिकतम तीन प्रोजेक्ट की तुलना हो सकती है।",
  pruned: (count: number) =>
    count === 1
      ? "एक पुरानी रिपोर्ट अब सर्वर पर नहीं है, इसलिए उसे इस सूची से हटा दिया गया।"
      : `${count} पुरानी रिपोर्टें अब सर्वर पर नहीं हैं, इसलिए उन्हें इस सूची से हटा दिया गया।`,
  loadFailed: "अभी आपकी रिपोर्टें लोड नहीं हो सकीं।",
};
