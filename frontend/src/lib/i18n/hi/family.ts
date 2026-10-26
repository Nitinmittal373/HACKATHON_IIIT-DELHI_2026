import type { family as English } from "@/lib/i18n/en/family";

/** The Hindi copy has exactly the same keys as the English. */
export const family: typeof English = {
  title: "बिल्डर का पारिवारिक वृक्ष",
  lead: "प्रमोटर, उसके निदेशक, रजिस्ट्री में संबंधित बताई गई कंपनियाँ और उनके UP-RERA प्रोजेक्ट।",
  graphLabel: "पारिवारिक वृक्ष का चित्र। Tab से नोड बदलें और विवरण के लिए Enter दबाएँ।",
  listTitle: "सूची दृश्य",
  tiers: {
    promoter: "प्रमोटर",
    directors: "निदेशक (नाम और DIN)",
    companies: "संबंधित कंपनियाँ",
    projects: "UP-RERA प्रोजेक्ट",
  },
  kinds: {
    promoter: "प्रमोटर",
    director: "निदेशक",
    company: "संबंधित कंपनी",
    project: "UP-RERA प्रोजेक्ट",
  },
  flags: {
    cirp: "दिवाला प्रक्रिया में",
    struck_off: "रजिस्टर से हटाई गई",
    lapsed: "पंजीकरण समाप्त",
    delayed: "12 महीने से ज़्यादा देरी",
    unread: "पन्ना पढ़ा नहीं गया",
  },
  statusUnknown: "रजिस्ट्री की स्थिति पढ़ी नहीं गई",
  none: "कोई नहीं मिला",
  detailsTitle: "विवरण",
  detailsHint: "रिकॉर्ड क्या कहते हैं, यह देखने के लिए कोई नोड चुनें।",
  status: (status) => `रजिस्ट्री की स्थिति: ${status}`,
  din: (din) => `DIN ${din}`,
  sourcePage: "जिस पन्ने से यह आया, उसे खोलें",
  linkNote:
    "रजिस्ट्री इन कंपनियों को संबंधित बताती है। यह नहीं बताती कि कौन-सा निदेशक किस कंपनी से जुड़ा है।",
  legend: "लाल रेखा और लेबल: दिवाला, रजिस्टर से हटाई गई या पंजीकरण समाप्त। टूटी रेखा: देरी या पढ़ा नहीं गया।",
  node: (kind, name, flag) => (flag ? `${kind}: ${name}। ${flag}` : `${kind}: ${name}`),
};
