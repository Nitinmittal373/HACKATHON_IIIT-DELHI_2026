export const home = {
  exampleNote: (reraId: string, date: string) =>
    `An example, not a live check: every value is from the check of ${reraId} read on ${date}.`,
  marqueeLabel: "Sources we read",
  report: {
    ariaLabel: (name: string) => `Example report for ${name}`,
    kicker: (date: string) => `EXAMPLE REPORT · READ ${date}`,
  },
  problem: {
    eyebrow: "The problem",
    titleStart: "The brochure tells you a story.",
    titleEnd: "The records tell you the truth.",
    heard: "WHAT YOU HEAR",
    claims: ["“Possession on time.”", "“Fully approved and registered.”", "“A trusted builder, no issues.”"],
    vs: "vs",
    records: "WHAT THE RECORDS SAY",
    note: (reraId: string, date: string) => `From the live check of ${reraId}, read ${date}.`,
  },
  demo: {
    eyebrow: "Powered by TinyFish",
    title: "Watch an agent read the records for you",
    lead: "A TinyFish browser agent opens each official site, finds your project and copies the exact record, with the link and the minute it read it.",
    steps: [
      "Finds your project on UP-RERA",
      "Reads the registration date",
      "Reads the promised completion date",
      "Counts every extension",
    ],
    cta: "Try it on a project",
    rows: ["Project name", "Promoter", "Registration date", "Proposed completion", "Extensions"],
    head: "Project details",
    example: "EXAMPLE",
    aria: (name: string) => `Illustration of an agent reading the UP-RERA page of ${name}`,
    caption: (reraId: string, date: string) =>
      `Illustration of a live check. The values are from the check of ${reraId} read on ${date}.`,
  },
  scale: {
    eyebrow: "NeevScore",
    title: "One honest number, 0 to 100",
    lead: "Everyone starts at 100. Points come off only for records we find. A source we cannot read lowers confidence, never adds points.",
    caption:
      "Marker: the score of the example check above. With fewer than half the key checks read, the score is shown without a band.",
    weights: [
      "UP-RERA compliance 25%",
      "Project execution 20%",
      "Legal & courts 15%",
      "Financial & insolvency 15%",
      "Builder history 15%",
      "News 10%",
    ],
    bands: { critical: "Critical", high: "High", moderate: "Moderate", low: "Low" },
  },
  sentinel: {
    eyebrow: "Neev Sentinel",
    title: "We keep watching after you book",
    lead: "Every week we re-read the records for your project and tell you only when something changes, in English or हिंदी.",
    stats: [
      ["re-checks", "Weekly"],
      ["spam alerts", "0"],
      ["languages", "2"],
    ],
    aria: "Illustration of two Neev Sentinel alerts on a phone lock screen, one in English and one in Hindi",
    date: "Monday, 26 October",
    now: "now",
    alert: (score: number) =>
      `New record: a court order on this builder's projects. Score unchanged at ${score}.`,
    caption: "Illustration of an alert, not a real one.",
  },
  faq: {
    title: "Questions, answered",
    items: [
      {
        question: "Is NeevCheck a credit rating or legal advice?",
        answer:
          "No. It is decision support built from public records. Every point links to the original record so you, your family or your lawyer can check it.",
      },
      {
        question: "Where does the data come from?",
        answer:
          "Official sources: UP-RERA, the company registry, insolvency orders from IBBI and NCLT, land authority lists and court and news reports. A TinyFish browser agent reads them live and saves the link and time.",
      },
      {
        question: "What if a website asks for a CAPTCHA?",
        answer:
          "We stop. NeevCheck never bypasses a CAPTCHA. That source is marked “Unable to verify”, which lowers confidence, not the score.",
      },
      {
        question: "Does finding nothing make a project safe?",
        answer:
          "No. Absence of a record never adds points. It only means nothing was found in the sources we could read.",
      },
    ],
  },
  cta: {
    titleStart: "Your home deserves",
    titleEnd: "a background check.",
    sub: "Free for your first projects. No phone number needed.",
    button: "Check a project now",
  },
  footer: {
    left: "NeevCheck · Team RYZEN, KIET · HackIIITD 2026",
    right: "Built on public records, read by TinyFish agents",
  },
};
