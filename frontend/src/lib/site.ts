/** The deployed site's address; share previews, the sitemap and robots.txt need it absolute. */
export const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

/** The scoring method, on GitHub, because the report is not served next to the repository's files. */
export const SCORING_DOC_URL =
  "https://github.com/Nitinmittal373/HACKATHON_IIIT-DELHI_2026/blob/main/docs/scoring.md";
