export const sentinel = {
  open: "Watch with Sentinel",
  title: "Watch this project",
  lead: "We re-check it every week and tell you only when a record really changes. Your email is used for nothing else.",
  email: "Your email",
  emailPlaceholder: "you@example.com",
  language: "Language of the alert",
  english: "English",
  hindi: "हिंदी",
  submit: "Start watching",
  saving: "Saving…",
  cancel: "Cancel",
  doneTitle: "Watching this project",
  doneBody:
    "Alerts always show on the Alerts page. An email is sent too when this service has email set up.",
  seeAlerts: "See your alerts",
  close: "Close",
  limit: "One email can watch up to 3 projects. Stop watching one before adding another.",
  invalidEmail: "Enter a valid email address.",
  failed: "We could not save this watch. Please try again.",
  card: "We re-check this project every week and tell you only when a record changes.",
};

export const alerts = {
  title: "Your alerts",
  lead: "Changes Sentinel found in the projects you watch. Enter the email you used to watch them.",
  emailLabel: "Email",
  show: "Show alerts",
  empty: "No alerts yet. Sentinel only tells you when a record really changes.",
  scoreChange: (before: number | null, after: number | null) =>
    `NeevScore ${before ?? "–"} → ${after ?? "–"}`,
  added: "New",
  removed: "No longer found",
  changed: "Changed",
  openReport: "Open the report",
  failedTitle: "We could not load your alerts",
  invalidEmail: "Enter a valid email address.",
  when: "Found",
};
