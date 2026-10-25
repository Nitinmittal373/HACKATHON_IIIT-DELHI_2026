# Changelog

## Unreleased

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
