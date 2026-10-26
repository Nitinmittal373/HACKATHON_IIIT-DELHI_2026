/** Copy for the state picker, the state badge and the coverage page. */
export const states = {
  allIndia: "All India",
  pickerLabel: "State",
  searchedIn: (names: string) => `Searched: ${names}`,
  badgeLabel: (state: string, rera: string) => `${state}, ${rera}`,
  levels: {
    full: "Full",
    partial: "Partial",
    search_only: "Search only",
  },
  /** How the facts on a report or a result were read, by coverage level. */
  reading: {
    full: "Read from the official RERA page",
    partial: "Read from the official RERA search",
    searchOnly: (rera: string) =>
      `From the official portal's search results. Open the full record on ${rera}`,
  },
  builderFromListings: (rera: string) =>
    `Builder identified from public listings; verify on ${rera}.`,
  openOn: (rera: string) => `Open on ${rera}`,
  notYetChecked: "Not yet checked on the portal",
  coverage: {
    title: "Which states NeevCheck can read",
    lead: "Any RERA-registered project in India can be searched. How much of its record can be read depends on the state's portal. Where a portal cannot be read in full, the report says so and links to the full record.",
    legendTitle: "What the levels mean",
    legend: {
      full: "The project page is opened and every field is read: promoter, dates, extensions, status, complaints.",
      partial: "A page or list is opened, but it shows only some fields.",
      search_only:
        "The portal cannot be opened by a program (it blocks it, asks for a CAPTCHA or a login, or loads data with scripts). NeevCheck shows only what the portal's own pages show in search results and never gets past a CAPTCHA or login.",
    },
    columns: {
      state: "State",
      authority: "Authority",
      level: "Level",
      read: "What we read",
      examples: "Examples",
      portal: "Portal",
    },
    formatNotVerified: "Number format not yet verified",
    noExamples: "None yet",
    open: "Open portal",
    loadFailed: "The list of states could not be loaded. Please try again in a minute.",
    nationalTitle: "Reads for every state",
    national:
      "Company registry, insolvency orders (IBBI and NCLT), group companies, lender auction notices and news are read for every state. Land dues lists exist for Uttar Pradesh only; for other states that check is shown as unread and never counts against a project.",
  },
  footer: "Coverage",
  homeLine: "Any RERA project in India. Deepest coverage in Uttar Pradesh.",
};
