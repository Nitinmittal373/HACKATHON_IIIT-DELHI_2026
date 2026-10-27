/** The date the privacy page was last changed, as YYYY-MM-DD. Change it with the text. */
export const PRIVACY_UPDATED = "2026-10-28";

export const PRIVACY_EMAIL = "ryzenoccult@gmail.com";

export const privacy = {
  metaTitle: "Privacy · NeevCheck",
  title: "Privacy",
  updated: (date: string) => `Last updated ${date}`,
  lead: "NeevCheck reads public records. We keep very little about you, and this page says exactly what.",
  sections: [
    {
      title: "If you sign in with Google",
      points: [
        "We keep your name, your email, your Google account id and the list of reports you saved.",
        "We take nothing else from Google: no contacts, no files, no calendar.",
      ],
    },
    {
      title: "Checking a project needs no account",
      points: [
        "Search, checks, reports and sharing are open to everyone.",
        "A check reads only public records. It does not look at you or your account.",
      ],
    },
    {
      title: "Alerts",
      points: [
        "If you watch a project, we keep the email you give us.",
        "We use it only to send alerts about the projects you watch, and for nothing else.",
        "You can stop watching a project at any time.",
      ],
    },
    {
      title: "No ads, no selling, no sharing",
      points: [
        "There are no ads and no trackers for advertising.",
        "We do not sell or share your data.",
        "The site is hosted on Vercel and the service on Render, so your requests pass through them.",
      ],
    },
  ],
  remove: {
    title: "Delete your data",
    menu: 'Sign in, open your account menu and choose "Delete my data". Your account and saved reports are removed.',
    emailLead: "Or email us and we will do it for you:",
  },
  footerLink: "Privacy",
  loginLink: "Read our privacy page",
};
