# Data sources

NeevCheck reads only public records. Each source has a reliability level that decides how much weight its findings can carry.

| Source | Site | What we read | Reliability |
| --- | --- | --- | --- |
| UP-RERA | [up-rera.in](https://www.up-rera.in) | Registration, promoter, completion date, extensions granted, completion certificate, documents, complaint counts | Primary |
| Company registry | [mca.gov.in](https://www.mca.gov.in), [Economic Times](https://economictimes.indiatimes.com), [zaubacorp.com](https://www.zaubacorp.com) | Company name, CIN, status | Primary on MCA; the mirrors are secondary |
| Insolvency | NCLT / NCLAT orders, [ibbi.gov.in](https://ibbi.gov.in), news reports of the case | Whether a case was admitted, when, and which projects it covers | Primary on official sites; news reports are secondary |
| Land authorities | Noida, Greater Noida (GNIDA), YEIDA | Published dues and defaulter lists | Primary |
| Consumer cases | [e-Jagriti](https://e-jagriti.gov.in) | Cases against the promoter | Primary, behind a CAPTCHA |
| Courts and news | Supreme Court orders, court reporting, news sites | The NBCC order and delay coverage | Orders are primary; reports and news are secondary |

## How we read them

- **UP-RERA** pages are read with **TinyFish Fetch** and parsed by deterministic Python code, so the same page always gives the same fields. Only the sections we use are requested, so the bank details and phone numbers on the page are never stored.
- For the other sources a **TinyFish browser agent** opens a deep page on the site, searches for the project or promoter and returns the exact fields we ask for as structured JSON. Where **Fetch** can read the page (a company details table, a PDF list, a court order) Python reads it instead, which is free and gives the same answer every time.
- A page is used for a company only if it carries the promoter's **exact legal name**: "Supertech Limited" is not "Supertech Realtors Limited". A project is matched word for word, so Eco Village-I is never matched to Eco Village-II.
- A **news report alone never causes a hard stop**. If it says an insolvency covers the whole company or this project, the finding is shown for review with 0 points until a court order is read.
- Every finding is saved with the **source URL**, the **time it was read** and its **reliability**.
- If a site shows a **CAPTCHA**, the agent stops and is never retried. The source is marked *Unable to verify* and the report tells the buyer how to check it themselves. e-Jagriti and zaubacorp both do this today.
- A list that is not published or cannot be read (the land authorities' dues lists, on the day of the recorded check) leaves its check **unread**: absence of a record never adds points.
- We respect each site's rate limits and run at most `AGENT_CONCURRENCY` agents at once.

## What we never do

- Bypass a CAPTCHA, login or paywall
- Collect personal data beyond what a public register publishes
- Show a claim without its source
