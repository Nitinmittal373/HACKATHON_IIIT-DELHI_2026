# Security Policy

## Reporting a vulnerability

Please do not open a public issue for security problems.
Email the maintainers through their GitHub profiles
([@rishibhaskar777](https://github.com/rishibhaskar777), [@Nitinmittal373](https://github.com/Nitinmittal373))
with the steps to reproduce. We reply within 72 hours.

## How NeevCheck handles sensitive data

| Area | What we do |
| --- | --- |
| API keys | The TinyFish key lives only in the backend's environment (a git-ignored `.env` locally, a secret on the host). It is never sent to the browser: the frontend only knows `NEXT_PUBLIC_API_URL`, and the built bundle is checked for the key. Logs and errors never print it. CI never needs it. |
| Secret scanning | Every push and pull request runs gitleaks over the full history. |
| Webhooks | `POST /api/sentinel/run` needs `WEBHOOK_SECRET` in the `X-Webhook-Secret` header and compares it in constant time. With no secret configured it refuses every call. |
| Rate limits and cost | New checks are limited per IP address per minute, and `SITE_CHECKS_PER_DAY` / `SITE_CHECKS_PER_MONTH` cap all live checks, Sentinel's included. Searches have a per-address limit and a site-wide `SITE_SEARCHES_PER_DAY`. A finished check of the same project from the last `REUSE_REPORT_DAYS` is reused instead of starting a paid run. TinyFish Monitors, which bill outside these budgets, are off unless `SENTINEL_MONITORS=true`. |
| CORS | The API answers browsers only from the origins in `FRONTEND_ORIGINS`. |
| Input | Every request body and query is validated with Pydantic: RERA numbers by pattern, links must be https on up-rera.in, at most 3 watches per account. |
| CAPTCHAs | The agent never bypasses a CAPTCHA, login or paywall. A run stops at the first progress note that mentions a CAPTCHA, whatever the agent reports, and the source is marked "Unable to verify". |
| Live view | The agent's live browser view is shown only for https addresses, in an iframe with `sandbox="allow-scripts allow-same-origin"`, no referrer and a CSP `frame-src https:`. |
| Personal data | We store the projects checked and, for Sentinel, the account, the verified Google email and the language of a watch. Only the signed-in account can create, list or stop its watches (another account's watch answers 404), and alerts go only to that email. An email is used only to send that watch's alerts, never for anything else, and only when alert email is configured (an HTTPS email API key or SMTP); the key stays in the environment and is never logged. Every alert email ends with a link that stops that watch: its token is 32 random bytes, only a hash is stored, and opening the link changes nothing until the Stop alerts button is pressed. Questions or deletion requests: neevcheck.help@gmail.com. Director names appear only as published in public registers. |
| Headers | The API sends `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` and a `default-src 'none'` CSP. The web app sends a Content-Security-Policy (self, the API and https frames only; no inline objects, no framing of the site), `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` and `Permissions-Policy`. |

## Supported versions

Only the latest version on `main` receives fixes.
