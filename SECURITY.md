# Security Policy

## Reporting a vulnerability

Please do not open a public issue for security problems.
Email the maintainers through their GitHub profiles
([@rishibhaskar777](https://github.com/rishibhaskar777), [@Nitinmittal373](https://github.com/Nitinmittal373))
with the steps to reproduce. We reply within 72 hours.

## How NeevCheck handles sensitive data

| Area | What we do |
| --- | --- |
| API keys | The TinyFish key lives only in a local `.env` file, which is git-ignored. CI never needs it. |
| Webhooks | Sentinel webhooks require a shared secret and compare it in constant time. |
| Rate limits | New checks are limited per IP address to stop abuse of paid browser agents. |
| CAPTCHAs | The agent never bypasses a CAPTCHA. The source is marked "Unable to verify". |
| Personal data | We store only the projects a user checks. Director names appear only as published in public registers. |
| Headers | The API sends `X-Content-Type-Options`, `Referrer-Policy` and `X-Frame-Options`. |

## Supported versions

Only the latest version on `main` receives fixes.
