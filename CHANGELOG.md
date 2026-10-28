# Changelog

## Unreleased

### Added (credit protection)

- **Sign in to start a live check.** `REQUIRE_SIGNIN_FOR_CHECKS` (default on) makes `POST /api/checks` need the sign-in token for a new live check; each account gets `CHECKS_PER_ACCOUNT_PER_DAY` (2) in Indian time, then `429` `account_limit` with the reset time. Opening, sharing and reusing saved reports stays open. The picker says *Sign in to run a live check* when signed out and *You have N live checks left today* when signed in (`GET /api/limits`).
- **Reuse recent reports.** A report finished within `REUSE_REPORT_DAYS` (7) is returned to anyone at no cost and saved to the account. *Re-check now* works once per project every `RECHECK_MIN_DAYS` (7); the report shows *Next re-check possible on …* (`Check.next_recheck_at`).
- **Saved searches and a search limit.** Search answers are kept in the database for `SEARCH_CACHE_DAYS` (7). `SEARCHES_PER_IP_PER_DAY` (15 signed out) and `SEARCHES_PER_IP_PER_DAY_SIGNED_IN` (40) count only searches that really run, in memory, for one Indian day.
- **A budget for the site.** `SITE_CHECKS_PER_DAY` (5) and `SITE_CHECKS_PER_MONTH` (60) replace `MAX_CHECKS_PER_DAY`. Used up, new checks get a calm message and searching and saved reports keep working.
- **Usage per check.** Every check stores its Search, Fetch and Agent call counts. `GET /api/admin/usage` (`ADMIN_TOKEN`, header `X-Admin-Token`) returns today's and the month's totals and the average per check.
- **Invite-only switch.** `INVITE_ONLY` and `ALLOWED_EMAILS` limit live checks to listed e-mails.
- **A gallery of saved reports.** `FEATURED_RERA_IDS` and `GET /api/featured` feed *Recently checked famous projects* on the Check page, from saved checks only and never naming who ran one.
- **Partly read pillars.** The UP-RERA complaint counts are the key check `rera_complaints` and read the builder (P2) and legal (P3) pillars, shown as *Partly read (UP-RERA complaints)*. A check with the registration, both complaint counts and the company status read now gets a band.
- **Real pages.** Check a project (`/check`), How it works (`/how-it-works`) and For RWAs (`/rwa`) have their own addresses, titles and descriptions in English and Hindi, with a sitemap. The header marks the current page, and old `/#search`, `/#how-it-works` and `/#sentinel` links go to them.

### Changed (credit protection)

- **Lanes that cannot succeed are not run.** Consumer cases (e-Jagriti always shows a CAPTCHA) no longer run an agent: the lane reads *Not checked automatically: the site needs a CAPTCHA* with a link. The group lane runs only for an exact company name. The insolvency lane reads its page with Fetch first and uses an agent only when the page speaks of an admission.
- **A stop when credit runs out.** After a call fails for lack of credit or a rate limit, the rest of that check's lanes are skipped without a retry and the War Room says *Paused: live-check credits are low*.
- **Honest badges.** A fact read from news or another secondary source is badged *From a secondary source*, in grey, never *Confirmed*.
- **The Google photo.** The content security policy now allows `lh3.googleusercontent.com`; the avatar falls back to the person's initials if the photo fails.
- **A calmer look.** The blurred glow and dotted grid are gone, panels are plain white with one thin border, there is no gradient text or glass, inner pages are left-aligned at a reading width, and the home page is the hero and the search only. The copy is plainer, in both languages.
- **Search limits in the privacy page.** It says searches are counted per address for one day, in memory.
- **README.** Rewritten for the current product, with a configuration table and screenshots made from saved fixtures.

### Added (sign-in)

- **Sign in with Google (optional).** Auth.js with the Google provider, a `/login` page in English and Hindi, a Sign in button next to My reports (the Google avatar with My reports and Sign out once signed in) and a small link under the landing page's search box. Reports are saved per account: the site mints a ten-minute HS256 token with `AUTH_BRIDGE_SECRET`, and the API adds `GET`, `POST` and `DELETE /api/me/reports` (rate limited, stored in Postgres or SQLite as `user_reports`). The checks made in this browser while signed out are offered to the account after sign-in (see Changed, accounts), and Alerts starts with the account's e-mail. Search, checks, reports and sharing never need an account. New dependency: `next-auth` 4.24.15.

- **Privacy page and Delete my data.** `/privacy` in English and Hindi, linked from the footer and the login page, says what is kept when you sign in, that checks need no account, how alert emails are used, and how to delete your data. The account menu has a **Delete my data** option backed by `DELETE /api/me` (same bridge token, rate limited), which removes the account's saved reports.

- **Stop-alerts link in every alert email.** Each email ends with "Stop alerts for this project:" and a link to `/alerts/stop?token=...` (EN and HI), built from `SITE_URL` or `NEXT_PUBLIC_SITE_URL`. Tokens are 32 random bytes, stored hashed. The page only shows a **Stop alerts** button; the button sends `POST /api/sentinel/unsubscribe`, which is rate limited and answers the same for any token. Alert cards also have a **Stop watching** button. The privacy page now says every alert email has a link to stop it. The contact address is neevcheck.help@gmail.com.

- **Alerts belong to the signed-in account.** Watching a project, reading alerts and stopping a watch from the app now need the bridge token. The alert email is the account's Google-verified email (one typed in the request is ignored), watches are stored against the account id, `GET /api/sentinel/alerts` no longer looks up a typed email, and another account's watch answers 404 like a missing one. The email link keeps working without sign-in. Watches made before accounts stay working for email and the link, are hidden from the app, and link to the account that signs in with the same verified email. The Alerts page and Watch this project ask the visitor to sign in first, with no email box, and **Delete my data** also removes the account's watches and alerts. Existing databases gain `watches.user_id` on start.

### Changed (accounts)

- **Accounts are fully separate.** Checks started while signed in are saved to the account by `POST /api/checks` itself (the browser sends the bridge token), and My reports, Alerts and recent checks come only from the server for that account, never mixed with browser data. The browser tags each saved report `anon` (made while signed out) or with the account id. After sign-in, the `anon` reports are offered ("Add the 2 reports from this browser to your account?", Add / Not now) and move only on Add; another account's reports are never moved. Sign out and **Delete my data** clear the account's cached token, lists, tagged reports and compare picks from the browser, then reload.
- **No public feed of other people's checks.** `GET /api/checks/recent` and the "Recently checked on NeevCheck" strip are removed. Signed in, the home page shows **Your recent checks** (new `GET /api/me/recent`, the last six of the account). Signed out, it shows **Checked in this browser** (the `anon` reports). The hero card and the score marker follow the same rule. `GET /api/checks?ids=` now returns the card facts too. A report still opens by its link, so sharing is unchanged. The privacy page says who sees what.
- **After sign-in** the visitor goes to the home page. Signing in from **Watch this project** returns to that report and reopens the dialog. Only same-site paths are accepted as `next`.

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
