/** Copy for the Check, How it works and For RWAs pages. Plain and specific: real numbers only. */
export const pages = {
  check: {
    metaTitle: "Check a project · NeevCheck",
    metaDescription:
      "Search a UP-RERA project by number, name, builder or locality, or from a brochure PDF or QR code. See what a check reads and what it costs.",
    title: "Check a project",
    lead: "Search by UP-RERA number, project name or builder. If you only have a place, a brochure, a QR code or a court order, use More ways to find it.",
    galleryTitle: "Recently checked famous projects",
    galleryLead:
      "Saved reports of well-known projects. Open one to see the proof behind its score.",
    galleryItem: (name: string, score: string, date: string) => `${name}, ${score}, read ${date}`,
    galleryRead: (date: string) => `Read ${date}`,
    galleryOpen: "Open report",
    readsTitle: "What a check reads",
    reads: [
      "UP-RERA: registration, promised and revised completion dates, extensions, complaint counts.",
      "Company registry: whether the builder's company is active, its directors and its group.",
      "Insolvency orders: NCLT and NCLAT cases that name the builder.",
      "Land authority lists: dues and approvals.",
      "Lender notices: SARFAESI and auction notices.",
      "News and court reports about the project or the builder.",
    ],
    readsNote:
      "Consumer cases on e-Jagriti sit behind a CAPTCHA. NeevCheck never bypasses one, so they are not checked automatically and the report links to the site.",
    costTitle: "What a check costs",
    costFree: "Opening, sharing and reusing a saved report is free and needs no account.",
    costReuse: (days: number) =>
      `If the project was checked less than ${days} days ago, you get that report at no cost.`,
    costSignIn: "A new live check needs a Google sign-in.",
    costPerDay: (count: number) => `Each account can start ${count} live checks a day.`,
    costRecheck: (days: number) => `Re-check now works once per project every ${days} days.`,
    costLeft: (count: number) => `You have ${count} live ${count === 1 ? "check" : "checks"} left today.`,
    costClosed:
      "Today's live checks are used up. Saved reports are still open; new checks open again tomorrow.",
    costInvite: "Live checks are invite-only right now. Saved reports are still open.",
    costSearches: "Searches are limited per day too. A search you repeat is served from the saved answer.",
  },
  how: {
    metaTitle: "How it works · NeevCheck",
    metaDescription: (min: number, max: number) =>
      `How NeevCheck turns six kinds of public records into a score from ${min} to ${max}, and where each record comes from.`,
    title: "How NeevCheck works",
    lead: (min: number, max: number) =>
      `NeevCheck reads public records for one project and turns them into a score from ${min} to ${max}. Every point links to the record it came from.`,
    stepsTitle: "The steps",
    steps: (max: number) => [
      {
        title: "Find the project",
        body: "Search by UP-RERA number, project name or builder. You confirm which registered phase is yours.",
      },
      {
        title: "Read the records",
        body: "TinyFish browser agents and page readers open the public records and copy what they say, with the link and the time they read it.",
      },
      {
        title: "Score what was found",
        body: `Everyone starts at ${max}. Points come off only for records we find. A record we cannot read never adds points.`,
      },
      {
        title: "Show the proof",
        body: "Each point in the report links to its source. Anything we could not read is listed, with a link so you can check it yourself.",
      },
    ],
    pillarsTitle: "Six pillars and their weights",
    pillarsLead: "Each pillar loses points for what we find in its records. The weights are fixed.",
    pillarNotes: {
      P1: "RERA registration, completion dates, extensions and penalty orders.",
      P2: "Complaints against the builder, and other delayed projects of its group.",
      P3: "Insolvency, complaints about this project and consumer cases.",
      P4: "Company status, directors, charges and lender notices.",
      P5: "Land authority dues and approvals.",
      P6: "News stories. News is capped, so it cannot decide a score alone.",
    },
    scaleTitle: (min: number, max: number) => `The ${min} to ${max} scale`,
    scaleLead: (max: number) =>
      `${max} means no risk found in the records we read. Lower means more risk. The bands are:`,
    bandLine: (label: string, min: number, max: number) => `${label}: ${min} to ${max}`,
    unratedTitle: "What “Not enough evidence yet” means",
    unrated: [
      "A band is shown only when UP-RERA was read and at least 4 of the 6 pillars were read.",
      "Otherwise there is no number, because a number nobody can stand behind is worse than none.",
      "Records that were read still count. Records that were not read never add or remove points; they only lower confidence.",
    ],
    partlyTitle: "Partly read pillars",
    partly:
      "If only the UP-RERA complaint counts were read for a pillar, the report says “Partly read (UP-RERA complaints)”.",
    sourcesTitle: "Where the records come from",
    sourcesLead: "Every source is public. Open any of them to check a point yourself.",
    sources: [
      { name: "UP-RERA", what: "Registration, dates, extensions, complaints.", key: "uprera" },
      { name: "Company registry", what: "Company status and directors.", key: "registry" },
      { name: "Insolvency orders (NCLT, IBBI)", what: "Cases that name the builder.", key: "insolvency" },
      { name: "Land authority lists", what: "Dues and approvals.", key: "land" },
      { name: "Lender notices (IBAPI)", what: "SARFAESI and auction notices.", key: "sarfaesi" },
      { name: "News and court reports", what: "Stories and orders about the project.", key: "news" },
      {
        name: "Consumer cases (e-Jagriti)",
        what: "Behind a CAPTCHA, so not checked automatically.",
        key: "consumer",
      },
    ],
    onlyUpTitle: "Why only Uttar Pradesh",
    onlyUp:
      "NeevCheck reads UP-RERA only. Other states' portals ask for a CAPTCHA or limit access, and NeevCheck never bypasses either.",
    privacyLead: "What we keep about you is on the",
    privacyLink: "Privacy page",
  },
  rwa: {
    metaTitle: "For RWAs · NeevCheck",
    metaDescription:
      "How a residents' group can watch a project with Neev Sentinel and get an alert, with a stop link, when a public record changes.",
    title: "For RWAs and residents' groups",
    lead: "A residents' group can watch the project it lives in or is waiting on, and hear about it when a public record changes.",
    stepsTitle: "How watching works",
    steps: [
      { title: "Open the report", body: "Search the project and open its report." },
      {
        title: "Watch it",
        body: "Press Watch with Sentinel and sign in with Google. One account can watch 3 projects.",
      },
      {
        title: "We re-check every week",
        body: "Sentinel reads the records again each week and tells you only when something changed, in English or Hindi.",
      },
      {
        title: "Alerts have a stop link",
        body: "Each alert email ends with a link that stops that watch. You can also stop it on the Alerts page.",
      },
    ],
    budgetNote:
      "A re-check is a live check. When the site's live-check budget for the day is used up, Sentinel waits for the next day.",
    signInLead: "Sign in with Google to watch a project and keep its alerts with your account.",
    signIn: "Sign in",
    signedInLead: "You are signed in. Your watches and alerts are on the Alerts page.",
    alerts: "Open Alerts",
    check: "Check a project",
  },
};
