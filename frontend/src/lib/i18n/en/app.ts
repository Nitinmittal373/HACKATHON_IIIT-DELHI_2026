export const app = {
  nav: {
    check: "Check a project",
    reports: "My reports",
    how: "How it works",
    rwa: "For RWAs",
    alerts: "Alerts",
  },
  hero: {
    pill: "Built for homebuyers across India",
    headline: ["Know", "your", "builder", "before", "you", "book."],
    subtitle:
      "Any RERA project in India. Deepest coverage in Uttar Pradesh. NeevCheck reads the state RERA portal, company records, insolvency orders and court news, and gives you a clear risk score with proof.",
    searchLabel: "RERA number or project name, any state",
    placeholder: "RERA number or project name, any state",
    submit: "Check project",
    try: "Try",
  },
  common: {
    back: "Back",
    tryAgain: "Try again",
    home: "Back to home",
    language: "Language",
    mainNav: "Main",
    homeLabel: "NeevCheck home",
    openSource: "Open source page",
    opensInNewTab: "opens in a new tab",
  },
  errors: {
    unreachableTitle: "We can't reach the NeevCheck service",
    unreachableBody:
      "The service that reads the records is not answering. Nothing was lost; please try again in a minute.",
    somethingTitle: "Something went wrong",
    somethingBody: "We could not load this page. Please try again.",
    notFoundTitle: "We could not find this page",
    notFoundBody: "The link may be wrong, or the check may be too old. Start a new check below.",
    rateLimited: (seconds: number) =>
      `Too many checks from this address. Please try again in ${seconds} ${seconds === 1 ? "second" : "seconds"}.`,
    dailyCap:
      "NeevCheck has reached its limit of live checks for today, so this one cannot start. Please try again tomorrow.",
    walletEmpty:
      "The agents that read the records are paused because the TinyFish account is out of credit. Please try again later.",
  },
};
