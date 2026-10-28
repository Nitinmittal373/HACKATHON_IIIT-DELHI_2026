/** The date the privacy page was last changed, as YYYY-MM-DD. Change it with the text. */
export const PRIVACY_UPDATED = "2026-10-28";

export const PRIVACY_EMAIL = "neevcheck.help@gmail.com";

export const privacy = {
  metaTitle: "Privacy · NeevCheck",
  title: "Privacy",
  updated: (date: string) => `Last updated ${date}`,
  lead: "NeevCheck reads public records. We keep very little about you, and this page says exactly what.",
  // `email` is whether this service emails alerts; when it does not, the page must not say so.
  sections: (email: boolean): { title: string; points: string[] }[] => [
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
      title: "Who sees what you checked",
      points: [
        "There is no public list of what people check. Nobody sees another person's checks, reports, alerts or recent checks.",
        "Signed in, your reports and recent checks come only from your account. Signed out, they are kept in your own browser and never sent to anyone.",
        "A report opens for anyone who has its link, so you can share one. Sharing is your choice.",
        "Signing out clears your account's reports and alerts from the browser.",
      ],
    },
    {
      title: "Alerts",
      points: email
        ? [
            "Watching a project needs you to be signed in. Alerts appear on your Alerts page, and we also email them to your Google account email, never to an address typed in by someone else.",
            "We use it only to send alerts about the projects you watch, and for nothing else.",
            "Only your account can see and stop your watches and alerts.",
            "Every alert email has a link to stop it, and you can stop watching a project at any time.",
          ]
        : [
            "Watching a project needs you to be signed in. Alerts appear on your Alerts page. We do not send email.",
            "Only your account can see and stop your watches and alerts.",
            "You can stop watching a project at any time, from the Alerts page.",
          ],
    },
    {
      title: "Search limits",
      points: [
        "Searches cost money, so each address may run a fixed number of searches a day. To count them, the server keeps your IP address with a number in its memory for one day, then drops it.",
        "A saved search answer is kept for a few days so the same question is not paid for twice. It holds the question and the public answer, never your address.",
        "A live check you start is stored with your account id, so the daily limit per account can count it. Nothing here is used for anything else.",
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
    menu: 'Sign in, open your account menu and choose "Delete my data". Your account, saved reports, watches and alerts are removed.',
    emailLead: "Or email us and we will do it for you:",
  },
  footerLink: "Privacy",
  loginLink: "Read our privacy page",
};
