export const insights = {
  track: {
    title: (promoter: string) => `Other UP-RERA projects by ${promoter}`,
    note: "Found by searching UP-RERA for the promoter's full legal name. Search shows some projects, not always all of them.",
    loading: "Searching UP-RERA…",
    none: "Search found no other UP-RERA project that names this promoter.",
    failed: "We could not search UP-RERA just now.",
    unnamed: "Name not shown on search",
    registered: (date: string) => `Registered ${date}`,
    check: "Check",
    checkLabel: (name: string) => `Check ${name}`,
  },
  whatsapp: {
    button: "Share on WhatsApp",
    text: (project: string, score: string, link: string) =>
      `NeevCheck: ${project}, ${score}, on public records. ${link}`,
  },
  questions: {
    title: "Questions to ask the builder",
    lead: "Chosen from what the records show. Ask for each answer in writing.",
    copy: "Copy all",
    copied: "Questions copied",
    copyFailed: "Could not copy; select the text instead",
    items: {
      delay: "What is the revised possession date? Please give it to me in writing, with the UP-RERA order that extended the completion date.",
      complaints: "What were the UP-RERA complaints against this project and the company about, and how many are still open?",
      insolvency: "Does the NCLT insolvency order cover this project? Who is the resolution professional, and what happens to money buyers have paid?",
      land: "Have the project's land dues to the development authority been paid? Can I see the no-dues letter?",
      cases: "Are any consumer or court cases pending against the company or this project?",
      progress: "When was the last quarterly progress report filed on UP-RERA, and what stage is construction at today?",
      approvals: "Which approvals are in place (building plan, fire, environment), and until when are they valid?",
      account: "What is the project's RERA collection account number, so that I pay only into that account?",
    },
  },
  freshness: {
    readOn: (date: string) => `Records read on ${date}`,
    stale: "These records are more than a week old.",
    recheck: "Re-check now",
    nextRecheck: (date: string) => `Next re-check possible on ${date}`,
  },
};
