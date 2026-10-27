export const account = {
  signIn: "Sign in",
  signOut: "Sign out",
  deleteData: "Delete my data",
  deleteConfirm:
    "Delete your account, saved reports, watches and alerts? This cannot be undone. Checks themselves are public records and stay.",
  deleteFailed: "We could not delete your data. Please try again, or email us.",
  menuLabel: "Your account",
  avatarAlt: (name: string) => `${name}, signed in`,
  heroLink: "Sign in to save reports and get alerts",
  login: {
    title: "Sign in to NeevCheck",
    lead: "Save your reports to your account and open them on any device.",
    google: "Continue with Google",
    notNeeded:
      "You never need an account to check a project. Search, checks, reports and sharing are open to everyone.",
    privacy: "We keep only your name, email and saved reports.",
    off: "Sign-in is not set up on this deployment yet. Checking a project works without it.",
    signedIn: (name: string) => `You are signed in as ${name}.`,
    toReports: "Open My reports",
  },
  reportsNote: "Saved to your account. Only you can see this list.",
  addBrowser: {
    title: (count: number) =>
      `Add the ${count} ${count === 1 ? "report" : "reports"} from this browser to your account?`,
    lead: "They were made before you signed in. If you add them, they are saved to your account and leave this browser's list.",
    add: "Add",
    notNow: "Not now",
    failed: "We could not add them. Please try again.",
  },
};
