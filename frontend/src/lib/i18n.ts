/** Copy that changes with the EN / हिं toggle. The hero and navigation come first; more screens follow. */

export type Lang = "en" | "hi";

export interface Strings {
  nav: { check: string; sample: string; how: string; rwa: string; signIn: string };
  hero: {
    pill: string;
    /** The headline word by word; the last word is set in orange. */
    headline: string[];
    subtitle: string;
    searchLabel: string;
    placeholder: string;
    submit: string;
    try: string;
  };
}

export const STRINGS: Record<Lang, Strings> = {
  en: {
    nav: {
      check: "Check a project",
      sample: "Sample report",
      how: "How it works",
      rwa: "For RWAs",
      signIn: "Sign in",
    },
    hero: {
      pill: "Built for homebuyers in Uttar Pradesh",
      headline: ["Know", "your", "builder", "before", "you", "book."],
      subtitle:
        "NeevCheck reads UP-RERA, company records, insolvency orders and court news for any under-construction project in UP, and gives you a clear risk score with proof.",
      searchLabel: "Project name or UP-RERA number",
      placeholder: "Project name or UP-RERA number",
      submit: "Check project",
      try: "Try",
    },
  },
  hi: {
    nav: {
      check: "प्रोजेक्ट जाँचें",
      sample: "नमूना रिपोर्ट",
      how: "यह कैसे काम करता है",
      rwa: "RWA के लिए",
      signIn: "साइन इन",
    },
    hero: {
      pill: "उत्तर प्रदेश के घर खरीदारों के लिए",
      headline: ["बुक", "करने", "से", "पहले", "अपने", "बिल्डर", "को", "जानें।"],
      subtitle:
        "NeevCheck उत्तर प्रदेश के हर निर्माणाधीन प्रोजेक्ट के लिए UP-RERA, कंपनी रिकॉर्ड, दिवाला आदेश और अदालती खबरें पढ़ता है, और सबूत के साथ एक साफ़ जोखिम स्कोर देता है।",
      searchLabel: "प्रोजेक्ट का नाम या UP-RERA नंबर",
      placeholder: "प्रोजेक्ट का नाम या UP-RERA नंबर",
      submit: "प्रोजेक्ट जाँचें",
      try: "आज़माएँ",
    },
  },
};
