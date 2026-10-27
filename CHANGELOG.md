# Changelog

## Unreleased

### Added (sign-in)

- **Sign in with Google (optional).** Auth.js with the Google provider, a `/login` page in English and Hindi, a Sign in button next to My reports (the Google avatar with My reports and Sign out once signed in) and a small link under the landing page's search box. Reports are saved per account: the site mints a ten-minute HS256 token with `AUTH_BRIDGE_SECRET`, and the API adds `GET`, `POST` and `DELETE /api/me/reports` (rate limited, stored in Postgres or SQLite as `user_reports`). The checks kept in this browser move into the account on first sign-in, and Alerts starts with the account's e-mail. Search, checks, reports and sharing never need an account. New dependency: `next-auth` 4.24.15.

- **Privacy page and Delete my data.** `/privacy` in English and Hindi, linked from the footer and the login page, says what is kept when you sign in, that checks need no account, how alert emails are used, and how to delete your data. The account menu has a **Delete my data** option backed by `DELETE /api/me` (same bridge token, rate limited), which removes the account's saved reports.

- **Stop-alerts link in every alert email.** Each email ends with "Stop alerts for this project:" and a link to `/alerts/stop?token=...` (EN and HI), built from `SITE_URL` or `NEXT_PUBLIC_SITE_URL`. Tokens are 32 random bytes, stored hashed. The page only shows a **Stop alerts** button; the button sends `POST /api/sentinel/unsubscribe`, which is rate limited and answers the same for any token. Alert cards also have a **Stop watching** button. The privacy page now says every alert email has a link to stop it. The contact address is neevcheck.help@gmail.com.

- **Alerts belong to the signed-in account.** Watching a project, reading alerts and stopping a watch from the app now need the bridge token. The alert email is the account's Google-verified email (one typed in the request is ignored), watches are stored against the account id, `GET /api/sentinel/alerts` no longer looks up a typed email, and another account's watch answers 404 like a missing one. The email link keeps working without sign-in. Watches made before accounts stay working for email and the link, are hidden from the app, and link to the account that signs in with the same verified email. The Alerts page and Watch this project ask the visitor to sign in first, with no email box, and **Delete my data** also removes the account's watches and alerts. Existing databases gain `watches.user_id` on start.

### Changed

- **Uttar Pradesh only.** NeevCheck now covers UP-RERA and nothing else, instead of thin, search-only coverage of 23 states. The other states' adapters, `GET /api/states`, the `state` fields on every model, the state picker, state badges, the coverage page and the pre-RERA notes are gone. A number of another state's RERA, or a project in a city outside Uttar Pradesh, is answered once, calmly: "NeevCheck covers Uttar Pradesh RERA projects for now. Check this project on its own state's RERA website." (`outside_up` on search results.) The search box takes "UP-RERA number, project or builder", and all copy, meta tags and the Hindi translation say UP-RERA. `docs/states.md` and `docs/find-any-project.md` are deleted.
- **Group companies and lender notices always run.** `V2_SOURCES` is removed: the group and SARFAESI sources and the per-day source cache are part of every check. Sentinel re-checks skip the cache, since they exist to see what changed.
- **Website.** The footer reads "NeevCheck · Public records, read live" with a "Not a credit rating" note; hackathon and team names are gone from every page, meta tag and share picture. The sticky header has a solid background.

### Fixed

- **Score.** A project past its completion date and not completed (`past_end_date`) cost nothing; it now costs like a revised date (40 / 70 by months overdue, the larger of the two when both are present). Complaints against the promoter across all its UP-RERA projects now cost 1 point each (max 40) under R13 "Builder complaint record". A band needs the UP-RERA record and at least 4 of the 6 pillars; otherwise the score is provisional and shows no band. Every stored check is scored again at startup, so old reports and recent checks follow the method.
- **Check flow.** UP-RERA reports what it has read as soon as the main page is parsed. A source that times out or fails after reporting keeps its findings and checks and ends as `partial` (new run status) instead of `blocked`. A check no longer stops because UP-RERA was only partly read; it fails only with no project record and no builder.
- **War Room.** A lane with findings shows "Partly read", never "Not read", and the big view lists its findings. A lane that did not run says why, and "N lanes read" matches what ran.
- **Confirm.** The project's name is shown, never the number twice, and the Registered column is filled in from the project's own page.

### Also changed

- **Self-hosted fonts.** Geist, Geist Mono and Noto Sans Devanagari are served from `frontend/src/fonts` (SIL Open Font License texts included) instead of Google Fonts, so a build never needs the network for type.
- **One score.** NeevScore 300–900 is the only score the interface shows: the home scale and report card, the live check result, the report, My reports, Compare, Sentinel alerts, the shared preview image and the WhatsApp text. The first 0–100 score is kept as one line in each report's method section, and in the API for older clients.
- **One contract.** The API's shape is exported from the backend to `contracts/openapi.json`, and the frontend's types are generated from it. `make contract` does both; CI fails when either is out of date.

### Added

- **Find a project.** The resolver searches the open web beside UP-RERA and votes on the `UPRERAPRJ` numbers it finds (+3 a page of up-rera.in, +2 the builder's site, +1 any other domain), then confirms each kept number on up-rera.in. New: `GET /api/promoters/search` (a builder's registered projects and company pages), `locality` on `GET /api/projects/search`, and `POST /api/extract` (UP-RERA numbers in a PDF brochure or agreement, or in the text of a QR code; read in memory, never stored, personal details removed). Public orders are searched last, only to find a builder or a number. The app has a "More ways to find it" panel, status badges, and a factual not-found card in English and Hindi that never calls a project illegal or unregistered. New dependencies: `pypdf` (backend) and `jsqr` (frontend).
- **README redesign** with an animated banner, architecture and workflow, fresh media from a live check, and the team.
- `display_score` (value, band, hard stop, confidence, provisional) on every answer that shows a score: the report, the check and its events, My reports, recent checks, Compare, Sentinel alerts and promoter projects. Checks stored before NeevScore existed are re-scored from their findings when read.
- `GET /api/meta`: the score scale, band edges, pillar weights and reason codes, so no client hard-codes them.
- Compare now ranks by NeevScore and lists points lost per pillar instead of per area.

### Fixed

- **Search on the live site.** Any project registered after 2018 without a stable UP-RERA details page (for example `UPRERAPRJ396176`) made search fail with "We could not search UP-RERA just now", because the API tried to read a page that does not exist. Search also ran inside a Vercel function, where a sleeping Render server could outlast it. Search now runs in the browser with a 120-second timeout, wakes the server first, retries once after a proxy error, and names the real reason when it fails.
- **Finding projects.** Name searches are limited to up-rera.in and every candidate is completed from its own page (name, promoter, district, registration date). Spellings like `uprera prj 8334` work.
- **Home page.** The animated skyline behind the hero was hidden by a stray CSS rule; it is back, and with reduced motion it stays still instead of disappearing. The search bar is frosted glass, as designed.
- **Interrupted checks.** A check cut off by a restart is marked failed on startup instead of staying "running" forever.

### Added

- **My reports**: the checks you start are kept in your browser (no account) and listed at `/reports`, with Open, Compare, Re-check and Remove.
- **Recently checked**: the home page card shows the latest real finished check, with a strip of recent ones; before there are any, an empty card says where your report will appear.
- **Compare**: two or three finished checks side by side at `/compare`, with "best on the records" chosen only between checks that read at least half their key records.
- **Report extras**: the builder's other UP-RERA projects, five questions to ask the builder, Share on WhatsApp, and "Records read on" with a prompt to re-check after a week.
- **Resume**: reopening a live check picks up where it stands.
- API: `GET /api/checks?ids=`, `GET /api/checks/recent`, `GET /api/checks/compare?ids=`, `GET /api/promoters/projects`.
