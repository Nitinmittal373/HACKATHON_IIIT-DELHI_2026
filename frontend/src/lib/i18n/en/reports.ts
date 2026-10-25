export const reports = {
  title: "My reports",
  lead: "Checks you started on this device. They are kept in this browser only: there are no accounts.",
  loading: "Loading your reports…",
  emptyTitle: "No reports yet",
  emptyBody: "Search a project to run your first live check. Every check you start is listed here.",
  status: {
    queued: "Running",
    running: "Running",
    completed: "Done",
    failed: "Failed",
  },
  checkedOn: (date: string) => `Checked ${date}`,
  noScore: "No score",
  noScoreFailed: "UP-RERA could not be read, so there is no score.",
  noScoreRunning: "The agents are still reading the records.",
  open: "Open",
  compare: "Compare",
  inCompare: "In compare",
  recheck: "Re-check",
  rechecking: "Starting…",
  remove: "Remove",
  actionsFor: (name: string) => `Actions for ${name}`,
  compareCount: (count: number) => `${count} of 3 picked to compare`,
  compareHint: "Pick two or three finished checks to compare them side by side.",
  compareGo: "Compare projects",
  compareFull: "You can compare up to three projects at a time.",
  pruned: (count: number) =>
    count === 1
      ? "One older report is no longer on the server, so it was removed from this list."
      : `${count} older reports are no longer on the server, so they were removed from this list.`,
  loadFailed: "We could not load your reports just now.",
};
