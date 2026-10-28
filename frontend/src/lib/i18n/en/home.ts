export const home = {
  recent: {
    // Only the visitor's own checks are ever listed: nobody sees another person's.
    accountTitle: "Your recent checks",
    accountLead: "The last checks saved to your account. Only you see this list. Each one opens its full report, with every source.",
    browserTitle: "Checked in this browser",
    browserLead: "Checks you started here without signing in. They stay in this browser. Sign in to keep them with your account.",
    item: (name: string, score: number | null, band: string, date: string) =>
      score === null
        ? `${name}: not enough evidence yet, checked ${date}`
        : `${name}: NeevScore ${score}, ${band}, checked ${date}`,
  },
  footer: {
    left: "NeevCheck · Public records, read live",
    note: "Not a credit rating",
    right: "UP-RERA projects only",
  },
};
