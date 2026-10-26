/** Copy for the builder family tree. */
export const family = {
  title: "Builder family tree",
  lead: "The promoter, its directors, the companies the registry lists as related, and their UP-RERA projects.",
  graphLabel: "Family tree diagram. Move between nodes with Tab and press Enter for details.",
  listTitle: "List view",
  tiers: {
    promoter: "Promoter",
    directors: "Directors (name and DIN)",
    companies: "Related companies",
    projects: "UP-RERA projects",
  },
  kinds: {
    promoter: "Promoter",
    director: "Director",
    company: "Related company",
    project: "UP-RERA project",
  },
  flags: {
    cirp: "In insolvency",
    struck_off: "Struck off",
    lapsed: "Registration lapsed",
    delayed: "Delayed over 12 months",
    unread: "Page not read",
  },
  statusUnknown: "Registry status not read",
  none: "None found",
  detailsTitle: "Details",
  detailsHint: "Choose a node to see what the records say about it.",
  status: (status: string) => `Registry status: ${status}`,
  din: (din: string) => `DIN ${din}`,
  sourcePage: "Open the page this came from",
  linkNote:
    "The registry lists these companies as related. It does not say which director links to which company.",
  legend: "Red outline with a label: insolvency, struck off or lapsed. Dashed outline: delayed or not read.",
  node: (kind: string, name: string, flag: string | null) =>
    flag ? `${kind}: ${name}. ${flag}` : `${kind}: ${name}`,
};
