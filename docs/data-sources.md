# Data sources

NeevCheck reads only public records. Each source has a reliability level that decides how much weight its findings can carry.

| Source | Site | What we read | Reliability |
| --- | --- | --- | --- |
| UP-RERA | [up-rera.in](https://www.up-rera.in) | Registration, promoter, completion date, extensions, filings | Primary |
| Company registry | [mca.gov.in](https://www.mca.gov.in) | Company status, CIN | Primary (mirrors are secondary) |
| Insolvency | [ibbi.gov.in](https://ibbi.gov.in), NCLT / NCLAT orders | Admitted cases and their scope | Primary |
| Land authorities | Noida, Greater Noida, YEIDA | Published dues and defaulter lists | Primary |
| Consumer cases | [e-Jagriti](https://e-jagriti.gov.in) | Cases against the promoter | Primary, often behind a CAPTCHA |
| Courts and news | Court reporting and news sites | Orders, rulings, delay coverage | Secondary |

## How we read them

- A **TinyFish browser agent** opens the site, searches for the project or promoter and returns the exact fields we ask for.
- Every finding is saved with the **source URL**, the **time it was read** and its **reliability**.
- If a site shows a **CAPTCHA**, the agent stops. The source is marked *Unable to verify* and the report tells the buyer how to check it themselves.
- We respect each site's rate limits and run at most `AGENT_CONCURRENCY` agents at once.

## What we never do

- Bypass a CAPTCHA, login or paywall
- Collect personal data beyond what a public register publishes
- Show a claim without its source
