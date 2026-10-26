export const home = {
  marqueeLabel: "Sources we read",
  report: {
    ariaLabel: (name: string, score: string) => `Latest NeevCheck report: ${name}, ${score}`,
    kicker: (date: string) => `LATEST REPORT · READ ${date}`,
    latestNote: (date: string) => `The most recent real check on NeevCheck, read live on ${date}.`,
    open: "Open this report",
    registered: (date: string) => `registered ${date}`,
    sources: (count: number) => `read ${count} ${count === 1 ? "source" : "sources"}`,
    confidence: "of record types read",
    skeletonLabel: "Placeholder for your report",
    skeletonKicker: "NEEVCHECK REPORT",
    skeletonTitle: "Your report appears here",
    skeletonBody: "Search a project above. Every point on your report links to the record it came from.",
    skeletonNote: "No check has finished on NeevCheck yet. Yours can be the first.",
  },
  recent: {
    title: "Recently checked on NeevCheck",
    lead: "Real checks run by other buyers. Each one opens its full report, with every source.",
    item: (name: string, score: number | null, band: string, date: string) =>
      score === null
        ? `${name}: not enough evidence yet, checked ${date}`
        : `${name}: NeevScore ${score}, ${band}, checked ${date}`,
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
    title: (min: number, max: number) => `One honest number, ${min} to ${max}`,
    lead: (max: number) =>
      `Everyone starts at ${max}. Points come off only for records we find. A source we cannot read lowers confidence, never adds points.`,
    caption: (name: string) =>
      `Marker: ${name}, the latest real check on NeevCheck. With fewer than half the record types read, the score is shown without a band.`,
    captionEmpty:
      "No check has finished on NeevCheck yet, so there is no marker. With fewer than half the record types read, a score is shown without a band.",
    weightsLabel: "How the six pillars are weighted",
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
      `New record: a court order on this builder's projects. NeevScore unchanged at ${score}.`,
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
