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

## Used only to find a project, never scored

Finding the project is separate from checking it. To reach a project's number NeevCheck may read builder sites, listing sites, a brochure or QR code the buyer gives, and public orders, and every one of them is a way to a number, not a source of findings:

| Used to find | Where | What it gives | What it never does |
| --- | --- | --- | --- |
| The number | Builder and listing sites, through unrestricted Search | A registration number, voted on by who prints it | Add a finding or a point; a number is `confirmed` only when an up-rera.in page prints it |
| The number | The buyer's own PDF or the text of a QR code | A number and the words around it, with personal details removed | Keep the file; it is read in memory and dropped |
| The builder and sometimes the number | RERA orders, indiankanoon.org and NCLT orders that name the project | A builder's name and the order's link | Count as evidence; the order is shown to the buyer and linked, nothing more |
| Companies of a builder | Company-registry mirrors of MCA data | A name and a CIN | Merge companies of one group; each is its own legal entity |

When nothing is found by any of these, NeevCheck says only that it could not find a RERA registration in public records, or, for another state's number, that it covers Uttar Pradesh for now. It never calls a project illegal or unregistered, because a public search can miss a project.

## What we never do

- Bypass a CAPTCHA, login or paywall
- Collect personal data beyond what a public register publishes
- Show a claim without its source

## NeevScore v2 signals: what UP-RERA actually shows

Investigated with free Search and Fetch on 25 Oct 2026, project UPRERAPRJ8334.

| Signal | Access reality | Method | Status |
| --- | --- | --- | --- |
| Registration lapsed or revoked | Shown only through the project status text; read when it says lapsed or revoked | Fetch + parser | Read (`registration_revoked`) |
| Revised vs promised completion date | Original end date on the details/summary page; extensions on the summary page | Fetch + parser | Read (`delay_vs_promised`) |
| Extensions | "Extension Granted" table on the summary page | Fetch + parser | Read (already in v1) |
| Quarterly progress reports (QPR) filed or missed | UP-RERA publishes the QPR rules, deadlines and a "Default on QPR" tag for non-compliant projects, but no per-project QPR table was found in the pages Fetch returns | Fetch finds nothing; an agent run returned no answer | **Not read.** Stays unread and appears under R12 |
| Penalty orders against a project | Orders are published as PDFs and press releases, not as a per-project list we could confirm | none | **Not read.** Stays unread and appears under R12 |

Nothing is guessed: a signal that cannot be read adds no points and lowers confidence.

## Company registry mirrors and the builder's group

Investigated with free Search and Fetch on 26 Oct 2026 for SUPERTECH LIMITED.

| Signal | Access reality | Method | Status |
| --- | --- | --- | --- |
| Directors (name and DIN) | Tofler's public profile lists them; Zaubacorp and TheCompanyCheck return "could not be read" to Fetch | Search + Fetch, parsed in Python | Read. Only name and DIN are kept: no addresses, PAN or phones (DPDP minimisation) |
| Charges (recent creation) | Tofler lists lenders, amounts and charge dates | Search + Fetch | Read; a `charge_created` finding only when a charge is dated in the last 12 months |
| Related companies | Tofler's "related companies" table (name only, no CIN) | Search + Fetch | Read, at most 10 per check |
| Status of a related company | Economic Times company page (Zaubacorp address mapped to it), exact legal-name match | Search + Fetch | Read when a page is found; otherwise unread, never assumed clean |
| Other directorships of each director | Not in the text Tofler's profile returns | none | **Not read.** R07 comes from related companies only |
| Struck-off or disqualified director | No readable page found | none | **Not read** |
| Late MCA filings | The registry pages show the last AGM and balance sheet dates only | none | **Not read** |
| Group projects on UP-RERA | Search on up-rera.in by exact legal name, then each project page (at most 20 per check) | Search + Fetch + parser | Read; delayed means more than 12 months past the latest date on the details page, so extensions only on the summary page can make it an undercount |

The group source never runs a browser agent. A profile that does not name exactly the promoter's legal company is not used, so "Supertech Limited" never collects "Supertech Realtors Private Limited".

## Insolvency, land authorities and lender notices (v2)

| Signal | Access reality | Method | Status |
| --- | --- | --- | --- |
| Promoter in CIRP (NCLT / IBBI) | Public orders and announcements on nclt.gov.in, ibbi.gov.in, nclat.nic.in; strict legal-name and scope matching already in `insolvency.py` | Search + agent only if a page cannot be read | Read (unchanged). Only an official page is a hard stop |
| Sister company in CIRP or liquidation | Registry status of each related company (see the group source) | Search + Fetch | Read when a page is found |
| Noida / GNIDA / YEIDA defaulter lists | Published as PDFs; exact legal name matched with an amount on the same line (already in `land.py`) | Search + Fetch text | Read (unchanged) |
| OC / CC past due, failed 25% package deposit | No readable list found | none | **Not read** |
| SARFAESI auction notices | Lender and IBAPI notice pages are indexed by Search; none named SUPERTECH LIMITED on 26 Oct 2026 | Search only | Read. A lender or government page is scored; any other page is shown for review with no points |
| Pending consumer or civil cases | e-Jagriti shows a CAPTCHA; we never bypass one | none | Unread: the report links to the official site and lists it under R12 |

## Feasibility at a glance

| Signal | Access reality | TinyFish method | Status |
| --- | --- | --- | --- |
| Registration lapsed or revoked | Project status text on up-rera.in | Fetch | Read |
| Delay against the promised date, extensions | Details and summary pages | Fetch | Read |
| Quarterly progress reports missed | No per-project table in what Fetch returns | Fetch, agent tried | Not read (R12) |
| Penalty orders | PDFs and press releases, not a per-project list | none | Not read (R12) |
| Directors, charges, related companies | Tofler public profile; other mirrors refuse Fetch | Search + Fetch | Read; name and DIN only |
| Struck-off director, late filings, other directorships | No readable public page | none | Not read |
| Group companies' UP-RERA projects | up-rera.in search by exact legal name | Search + Fetch | Read, capped at 10 companies and 20 projects |
| Promoter in CIRP | NCLT / IBBI pages, strict name and scope matching | Search + agent when needed | Read |
| Land authority defaulter lists | Authority PDFs | Search + Fetch text | Read |
| OC / CC past due, failed 25% deposit | No readable list | none | Not read |
| SARFAESI auction notices | Lender and IBAPI pages | Search | Read; review only unless the page is a lender's or the government's |
| Pending consumer cases | e-Jagriti shows a CAPTCHA | none | Not read; the report links to the official site |
| Page changes after a watch starts | Public UP-RERA page and news search | Monitors (page and topic) | Triggers a re-check only; never a claim |
| Builder background dossier (BETA idea) | TinyFish Research would be needed | not built | Skipped: it must never feed the score |
