<div align="center">

<img src="docs/assets/banner.svg" width="100%" alt="NeevCheck: Know your builder before you book. An animated construction skyline with rising towers, a swinging crane and lit windows.">

<br>

[![Live demo](https://img.shields.io/badge/live%20demo-neevcheck--up.vercel.app-F26B1D?style=flat-square)](https://neevcheck-up.vercel.app)
[![HackIIITD 2026](https://img.shields.io/badge/HackIIITD-2026%20finalist-111111?style=flat-square)](#team)
[![TinyFish](https://img.shields.io/badge/agents-TinyFish-F26B1D?style=flat-square)](https://tinyfish.ai)
[![Next.js](https://img.shields.io/badge/Next.js-15-000000?style=flat-square&logo=nextdotjs)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square)](LICENSE)

**A risk check for under-construction homes in Uttar Pradesh.** Give NeevCheck a project, a builder, a brochure or a QR code. TinyFish browser agents read the public records, and the app turns them into one **NeevScore (300–900)** with a source link for every point.

[**Live demo**](https://neevcheck-up.vercel.app) · [Find a project](#find-a-project) · [How it works](#how-it-works) · [NeevScore](#neevscore-300900) · [Architecture](#architecture) · [Run it](#getting-started) · [Team](#team)

<br>

<img src="docs/assets/hero.gif" width="860" alt="NeevCheck home page: a search bar, the More ways to find it panel, a report card and an animated construction skyline">

</div>

---

## Live demo

**Web app: <https://neevcheck-up.vercel.app>** · API: <https://neevcheck-api.onrender.com> ([health](https://neevcheck-api.onrender.com/api/health), [docs](https://neevcheck-api.onrender.com/docs)).

Every check is live: nothing is mocked, and there is no demo mode. The API runs on Render's free plan and sleeps when idle, so the first search can take up to a minute while it wakes. To run it yourself, see [Getting started](#getting-started); to deploy it, see [`docs/deployment.md`](docs/deployment.md).

## The problem

Buying an under-construction flat is often a family's biggest cheque. The facts that decide whether it will be delivered are public, but they are scattered across government portals that few buyers know about, let alone read.

| | |
| --- | --- |
| **51,000** | homes Supertech booked for delivery in 2010–12, many still waiting ([Supreme Court, Feb 2026](https://www.livelaw.in/top-stories/supreme-court-upholds-nclat-order-directing-nbcc-to-complete-stalled-supertech-housing-projects-522030)) |
| **49,748** | homes in 16 stalled Supertech projects handed to NBCC to finish ([NCLAT order, Dec 2024](https://psuwatch.com/newsupdates/nbcc-appointed-as-consultant-to-complete-supertechs-16-housing-projects)) |
| **UP-RERA** | the one register NeevCheck reads in full: promoter, dates, extensions and complaint counts for every project |

A broker's brochure says *"possession on time"*. The records may say the completion date was extended three times. NeevCheck reads the records so the buyer doesn't have to.

## How it works

<div align="center">
<img src="docs/assets/workflow.svg" width="100%" alt="Workflow: find the project by name, number, builder, locality, document or QR code; confirm it; the War Room reads six lanes of sources; NeevScore 300 to 900; the report; weekly Sentinel re-checks">
</div>

1. **Find it.** By name, RERA number, builder, locality, a brochure PDF or a QR code. Many projects have no website and no number to hand; [there is a path for them](#find-a-project).
2. **Confirm it.** Candidates are listed with how sure we are of each number. Nothing runs until the buyer says *"yes, this is the one"*.
3. **War Room.** Six lanes, read two at a time: UP-RERA, the company registry, group companies, insolvency and court cases, land authorities, news and lenders. Each lane streams its progress and says honestly when it stopped.
4. **NeevScore.** A deterministic formula turns the findings into a 300–900 score. Same records, same score.
5. **Report.** Score, reasons, evidence ledger, timeline and a buyer action plan, in English or हिंदी.
6. **Sentinel.** A weekly re-check alerts the buyer only when a record actually changes.

<div align="center">
<img src="docs/assets/war-room.gif" width="820" alt="The War Room during a live check of UPRERAPRJ8334: six lanes read and their findings fill in">
<br><sub><b>War Room</b>: a real check of <code>UPRERAPRJ8334</code>, sped up. Six lanes, each with its own status.</sub>
</div>

## Find a project

A buyer may know only a name, a builder's brand, a neighbourhood, a brochure or a hoarding's QR code. NeevCheck takes all six. The search runs UP-RERA and the open web side by side, and never calls a listing site a source: listing sites only help find the number.

NeevCheck covers **Uttar Pradesh RERA projects** (numbers like `UPRERAPRJ8334`). A number of another state's RERA, or a project in a city outside Uttar Pradesh, gets one calm line: *"NeevCheck covers Uttar Pradesh RERA projects for now. Check this project on its own state's RERA website."* Nothing is searched for it.

| You have | What NeevCheck does |
| --- | --- |
| **A name** | Searches up-rera.in, and the open web with no domain limit (four Search wordings, cached for a day). `UPRERAPRJ` numbers are found in the results, then **voted on** |
| **A UP-RERA number** | Opens its own up-rera.in page. If the page gives nothing, the same vote confirms the number exists |
| **A builder** | `GET /api/promoters/search`: the builder's registered projects from up-rera.in and the open web, plus company-registry pages with CIN, each company kept apart |
| **A city or locality** | `?locality=Sector 150 Noida` is added to the open-web search. A city outside Uttar Pradesh is answered with the calm line above when nothing is found |
| **A brochure or agreement** | Upload a PDF (5 MB). It is read in memory, the UP-RERA numbers and the words around them come back with phone numbers, e-mail, PAN and Aadhaar removed, and the file is never stored |
| **A QR code** | Scan it with the camera or choose a photo. The browser decodes it; only the text inside is sent |

<div align="center">
<img src="docs/assets/screens/more-ways.png" width="760" alt="The More ways to find it panel: Builder, City or locality, Upload brochure and Scan QR tabs">
<br><sub><b>More ways to find it</b>: builder, locality, brochure upload and QR scan. Keyboard accessible, English and हिंदी.</sub>
</div>

**The vote.** A number printed by a page of up-rera.in earns 3 points, by the builder's own site 2, and by any other distinct domain 1. A number is kept at 3 points or when two domains print it, and only if one of them prints it next to the project's name. A number beside a *different* project's name does not count (a listing of many projects gives each number only its own words), Several numbers for one name (phases, towers) are separate candidates.

**What the buyer is told.** Every candidate carries a status and the sites that printed its number:

| Status | Meaning |
| --- | --- |
| `confirmed` | A page on up-rera.in prints this number |
| `listings_only` | Builder and listing sites print it; no UP-RERA page was read. A check will try UP-RERA and say what it could not verify |
| `from_document` | Taken from the buyer's own PDF or QR code |
| `from_order` | Found in a public order that names the project, with a link to the order |

**When nothing is found.** NeevCheck says only: *"We couldn't find a RERA registration for this project in public records."* It never calls a project illegal or unregistered, because a public search can miss a project. It then tells the buyer what to do: ask the builder for the number in writing, that a project of more than 500 square metres of land or more than eight apartments must be registered before it is advertised or sold (RERA Act, Section 3), not to pay until the number can be verified, and where to tell UP-RERA (its form for projects without a registration). A test bans accusing words in that card, in English and Hindi.

## What NeevCheck does

| | Feature | What the buyer gets |
| :-: | --- | --- |
| 🔎 | **Find a project** | Name, UP-RERA number, builder, locality, brochure or QR code, on UP-RERA and the open web |
| 🏟️ | **War Room** | Six lanes, each with its own live ticker and findings count; click a lane to enlarge its live browser view |
| 📊 | **NeevScore (300–900)** | One explained number, like a credit score: six weighted pillars, a confidence meter and reason codes R01–R14 |
| 🗂️ | **Evidence ledger** | Every finding carries its source link, the minute it was read, the words on the page and its reliability. *No source, no claim.* |
| 🧬 | **Builder DNA and family tree** | Sister projects, insolvency scope, directors (name and DIN only) and related companies, with a list view for phones |
| ⚖️ | **Compare** | Two or three projects side by side; it names the best only when the evidence allows |
| ✅ | **Buyer action plan and questions** | Four things to check before paying more, and five questions for the builder, ready to copy |
| ✉️ | **Complaint draft** | An editable complaint built from facts only, with numbered annexures, in English or Hindi. *Draft for you to review. Not legal advice.* |
| 🔔 | **Neev Sentinel** | Weekly re-checks and TinyFish Monitors on the project's page; an alert only when a record changes |
| 🗃️ | **My reports** | Every check is kept in your browser, with no account |
| 🌐 | **English and हिंदी** | Plain-language reports for every family member |

<div align="center">
<img src="docs/assets/screens/report-v2.png" width="760" alt="A NeevCheck report: NeevScore, band, evidence read, reason codes and six pillar bars">
<br><sub><b>Report</b>: the score, the reasons behind it and the proof for each.</sub>
</div>

<div align="center">
<img src="docs/assets/screens/compare.png" width="760" alt="Compare page with two projects side by side, row by row">
<br><sub><b>Compare</b>: row by row from the records. A thin check is never ranked.</sub>
</div>

## NeevScore (300–900)

NeevScore is a number from **300 to 900**: higher is safer. The backend owns the scale (`GET /api/meta` serves it; the frontend keeps no copy). It follows the shape of a credit report:

```text
NeevScore = 900 − 6 × Σ (pillar weight × pillar penalty)        clipped to 300–900
```

Points come off only for records we find. **Absence of a record never adds points.** A source we cannot read becomes reason code **R12 Data unavailable**: it costs nothing and lowers **confidence**, the share of the six record types that were read.

| Pillar | Weight | Examples |
| --- | --: | --- |
| Regulatory compliance (RERA) | 30% | registration status, extensions, missed quarterly updates |
| Legal and insolvency | 25% | insolvency of the promoter or this project, complaints, cases |
| Delivery track record | 20% | other projects of the same group delayed or lapsed |
| Financial and corporate health | 15% | struck-off or disqualified directors, charges, auction notices |
| Land authority and approvals | 5% | dues lists, missing completion or occupancy certificates |
| Sentiment and news | 5% | delay or protest coverage (secondary) |

| Band | Range |
| --- | --- |
| Low risk | 750–900 |
| Watch | 600–749 |
| Elevated risk | 450–599 |
| High risk | 300–449, and any hard stop (for example this project in insolvency per an official page) caps the score here |
| Not enough evidence yet | shown instead of a band, with a dash, unless the UP-RERA record (P1) and at least four of the six pillars were read. A hard stop always shows |

**A real example.** A live check of `UPRERAPRJ8334` (Supertech Eco Village-I Phase I-C), first read on 25 Oct 2026, with every source on, gave **495 · Elevated** with 5 of 6 record types read:

```text
900  starting score
-150 15 complaints on UP-RERA about this project            (R05, primary)
-126 completion date 105 months overdue                     (R03, primary)
-120 5 of 5 group projects past their completion date       (R13, primary)
  -9 three recent news stories on delays                    (R11, secondary)
 ───
 495  Elevated · confidence 83% (5 of 6 record types) · no hard stop
```

The 2,803 complaints against the promoter across all its projects are also a finding (R13, "Builder complaint record", capped); here the group's delays already use up that pillar. Every line links to the page it was read from; the check is recorded in [`backend/tests/fixtures/check_8334.json`](backend/tests/fixtures/check_8334.json) and replayed by the tests. The weights are transparent expert priors, to be calibrated on labelled stalled-project lists. Full method: [`docs/scoring.md`](docs/scoring.md).

## Scope

NeevCheck is built for **Uttar Pradesh**. UP-RERA is the one register it reads in full, because it is the one whose project pages a program can open and parse: the details page, the project summary with its complaint counts, and the extensions granted. The company registry, insolvency orders, group companies, lender notices, news and the Noida, Greater Noida and Yamuna Expressway dues lists are read for the promoter. A field a source does not show stays unread: it lowers confidence and never adds penalty points.

## How NeevCheck uses TinyFish

Every source tries the cheapest way to read a page first and escalates only when it has to.

| TinyFish | Cost | Used for |
| --- | --- | --- |
| **Search** | free | Finding the project on the open web and on up-rera.in; company pages; lender notices; news; public orders |
| **Fetch** | free | Opening UP-RERA project pages, company-registry pages and PDFs, lender and land-authority documents |
| **Agent** | paid, last step | Pages that need clicks: insolvency and court cases, e-Jagriti, the registry only when Fetch cannot read it. **A report uses at most three agent runs** |
| **Monitors** | per daily check | Watching a project's page and builder news; a change re-checks and alerts |

When an agent meets a CAPTCHA, a login or a paywall it stops. The lane says *Unable to verify*, the report lowers confidence, and nothing is bypassed. Results are cached per source, entity and day, so a second project of the same builder reads its company records from the cache. The escalation ladder is in [`docs/architecture.md`](docs/architecture.md#the-escalation-ladder).

## Architecture

<div align="center">
<img src="docs/assets/architecture.svg" width="100%" alt="Architecture: the browser on Vercel talks to FastAPI on Render; the resolver, check orchestrator, NeevScore engine, Postgres and Sentinel run there; TinyFish Search, Fetch and Agent read six lanes of public sources">
</div>

<details>
<summary><b>Diagram source</b> (Mermaid)</summary>

```mermaid
flowchart LR
    U([Homebuyer]) -->|find, confirm| FE[Next.js app<br/>More ways · War Room · Report]
    FE -->|REST + Server-Sent Events| API[FastAPI backend]
    API --> RES[Resolver<br/>open-web vote · document · QR]
    API --> ORCH[Check orchestrator]
    RES --> TF
    ORCH -->|six lanes| TF[[TinyFish<br/>Search · Fetch · Agent]]
    TF --> R1[(UP-RERA)]
    TF --> R2[(MCA registry)]
    TF --> R3[(IBBI · NCLT)]
    TF --> R4[(Land authorities)]
    TF --> R5[(Orders · courts)]
    TF --> R6[(News · lenders)]
    ORCH --> SC[NeevScore engine]
    SC --> DB[(SQLite / Postgres)]
    DB --> API
    CRON[Sentinel scheduler] -->|weekly re-check| ORCH
```

```mermaid
sequenceDiagram
    autonumber
    participant B as Browser
    participant A as FastAPI
    participant T as TinyFish
    B->>A: GET /api/projects/search?q=Mahagun Mywoods
    A->>T: Search (up-rera.in + open web)
    A-->>B: candidates with status and sources
    B->>A: POST /api/checks {rera_id, details_url}
    A-->>B: 202 {check_id}
    B->>A: GET /api/checks/{id}/events (SSE)
    A->>T: Search, Fetch, Agent per lane
    A-->>B: source.progress / finding.added
    A-->>B: check.completed {display_score}
    B->>A: GET /api/checks/{id}/report
```

</details>

More detail in [`docs/architecture.md`](docs/architecture.md).

## Tech stack

| Layer | Choice | Why |
| --- | --- | --- |
| Browser agents | **TinyFish** Search, Fetch, Agent and Monitors | Reads real government portals like a person, with a live view we can show buyers |
| Frontend | **Next.js 15**, React 19, TypeScript (strict) | Server rendering for a fast first load, file-based routes |
| Styling | Plain CSS with design tokens, CSS animations | Easy to read; no runtime animation library |
| Fonts | Geist, Geist Mono, Noto Sans Devanagari (self-hosted) | Clean UI type with proper Hindi support, and builds that never fetch fonts |
| Backend | **Python 3.12, FastAPI**, Pydantic v2 | Typed API, async streaming with Server-Sent Events |
| Documents | pypdf (PDF text), jsQR (QR codes, in the browser) | Small, pinned, offline; no OCR service |
| Storage | SQLite (local), Postgres (production) via SQLAlchemy 2 | Zero setup locally, one switch to deploy |
| Quality | pytest, Ruff, ESLint, tsc, Playwright with axe | Every change linted, typed, tested and checked for accessibility |
| CI and security | GitHub Actions, gitleaks, Dependabot | Tests on every push, secret scan over full history |
| Hosting | Vercel (web), Render (API) | Free tiers that fit a hackathon demo |

## Trust and ethics

- **Public records only.** NeevCheck reads official portals and published reports. No private data is collected; an uploaded brochure is read in memory and never stored.
- **No CAPTCHA, login or paywall is ever bypassed.** The source is marked *Unable to verify*.
- **No source, no claim.** Every finding links to where it came from and when it was read. Listing sites, orders and uploads only help find a project's number and builder; they are never scored findings.
- **Absence adds nothing.** A record we could not find never adds points; an unreadable source only lowers confidence.
- **Never invented.** There is no demo mode: every check is live, and tests replay recorded fixtures only.
- **Decision support, not advice.** NeevCheck is not a credit rating or legal advice. Verify important facts on the official portal.
- **Your keys stay yours.** API keys live in a local `.env`, never in the browser, logs or commits. See [`SECURITY.md`](SECURITY.md).

## Where NeevCheck fits

| Tool | What it is known for | The gap NeevCheck owns |
| --- | --- | --- |
| Landeed, Terra | Land records and title checks | The land, not the builder's RERA delivery record, group companies or insolvency |
| Probe42, Tofler, Zauba | Company risk data and registry mirrors | Raw company data with no project score; NeevCheck reads them as one source among several |
| Property portals | Listings and builder marketing | No incentive to show risk |
| PropEquity, PropAlert | Market and project tracking and delay analytics | Aggregate views, not a sourced per-project proof for one buyer |
| CRISIL and other raters | Ratings of builders for lenders and investors | Paid and not aimed at buyers; NeevCheck is explicitly *not* a credit rating |
| A lawyer's verification | A one-off title and approvals opinion | Slow and rarely repeated; NeevCheck is a free first pass and a list of questions to take to the lawyer |

NeevCheck's gap: **a free, sourced, per-project risk check for a home buyer in Uttar Pradesh, with proof for every point, a way in for projects that have no website, and a complaint draft when the records show a problem.** Descriptions of other tools are brief summaries of what they are known for, not reviews.

## Getting started

> Every check is live, so you need a [TinyFish API key](https://agent.tinyfish.ai/api-keys). To put NeevCheck online, follow [`docs/deployment.md`](docs/deployment.md).

```bash
git clone https://github.com/Nitinmittal373/HACKATHON_IIIT-DELHI_2026.git neevcheck
cd neevcheck
cp .env.example .env            # then set TINYFISH_API_KEY in .env

# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload    # http://localhost:8000/docs
ruff check . && pytest -q        # tests replay recorded responses, no key needed

# frontend (new terminal)
cd frontend
npm install
npm run dev                      # http://localhost:3000
npm run lint && npm run typecheck && npm run test:unit && npm run build
npm run e2e                      # browser tests; need `npx playwright install chromium` once

# after changing a backend model (from the repo root)
make contract                    # exports contracts/openapi.json and regenerates the frontend types
```

The key never leaves your machine: `.env` is git-ignored and the app never logs it. A `TINYFISH_API_KEY` set in your shell takes precedence over `.env`.

Try it from the terminal once the backend is running:

```bash
curl "localhost:8000/api/projects/search?q=Mahagun%20Mywoods"
curl "localhost:8000/api/projects/search?q=Eureka%20Park&locality=Sector%20150%20Noida"
curl "localhost:8000/api/promoters/search?q=Mahagun%20India"
curl -X POST localhost:8000/api/extract -H "Content-Type: application/pdf" --data-binary @brochure.pdf
curl -X POST localhost:8000/api/checks -H "Content-Type: application/json" -d '{"rera_id": "UPRERAPRJ8334"}'
curl -N localhost:8000/api/checks/<id>/events               # live event stream
curl localhost:8000/api/checks/<id>/report
```

The full API is described in [`docs/architecture.md`](docs/architecture.md#api).

## Project structure

```text
.
├── backend/                 FastAPI service
│   ├── app/
│   │   ├── api/             routes: search, promoters, extract, checks, events (SSE), reports, sentinel
│   │   ├── sources/         one module per public source, plus the shared agent runner
│   │   ├── states/          the resolver, the open-web vote, UP-RERA confirmation,
│   │   │                    builder and order search, the city table
│   │   ├── extract.py       numbers in a PDF or QR text, with personal details removed
│   │   ├── scoring/         NeevScore engine (v2/) and the classic 0–100 score
│   │   ├── sentinel/        watches, change detection, alerts, email
│   │   ├── orchestrator.py  runs a check and streams its events
│   │   └── tinyfish.py      the only module that calls TinyFish
│   ├── scripts/             API contract export; recorders for test fixtures; famous-project table
│   └── tests/               pytest, with recorded TinyFish responses in fixtures/
├── frontend/                Next.js app
│   ├── e2e/                 Playwright tests against a recorded API
│   ├── scripts/             capture.ts, capture-live.ts: the README media
│   └── src/
│       ├── app/             routes: home, check, report, reports, compare, alerts
│       ├── components/      find/ (More ways), confirm/, cam/ (War Room), report/ …
│       ├── lib/             API client and types generated from the contract, English and Hindi copy
│       └── styles/          tokens, globals, app screens and print
├── contracts/               openapi.json, exported from the backend (the API contract)
├── docs/                    architecture, scoring, data sources, deployment, assets
├── render.yaml              Render Blueprint for the API
└── .github/                 CI, issue forms, pull request template
```

## Roadmap

- [x] **Phase 0 · Foundation** — repo structure, CI, security policy, contribution guide, final design approved
- [x] **Phase 1 · Backend core** — API, data models, NeevScore engine, live UP-RERA source, event stream, shared agent runner
- [x] **Phase 2 · TinyFish agents** — source agents, live view streaming, CAPTCHA handling
- [x] **Phase 3 · Frontend foundation** — design tokens, layout, animated skyline, home page
- [x] **Phase 4 · Check flow** — search, confirm, Agent Cam, report
- [x] **Phase 5 · Sentinel and sharing** — weekly re-checks, alerts, PDF, Hindi
- [x] **v2 · Credit-style score** — NeevScore 300–900 with reason codes, War Room, family tree, evidence ledger, complaint draft, Monitor watch
- [x] **One contract, one score** — the API contract is exported from the backend and generates the frontend types
- [x] **Uttar Pradesh only** — one register read in full; other states answered with a calm line instead of thin, search-only coverage
- [x] **Find a project** — open-web search with source voting, UP-RERA confirmation, builder and locality search, brochure and QR, public orders, and factual guidance when nothing is found
- [x] **Score and flow fixes** — an overdue date costs points, the builder's complaint record counts, a band needs the RERA record and four of six pillars, and a lane that timed out keeps what it read
- [ ] **Phase 6 · Launch** — deployment, calibration of the score weights, v1.0

## Team

Built by **Team RYZEN** from KIET Group of Institutions for the HackIIITD 2026 finale at IIIT Delhi.

| Member | Role | Focus |
| --- | --- | --- |
| <a href="https://github.com/Nitinmittal373"><img src="https://github.com/Nitinmittal373.png?size=96" width="48" alt="" align="left" hspace="8"></a>**Nitin Mittal** (team leader)<br>[github.com/Nitinmittal373](https://github.com/Nitinmittal373) | Backend | Backend services and integrations |
| <a href="https://github.com/rishibhaskar777"><img src="https://github.com/rishibhaskar777.png?size=96" width="48" alt="" align="left" hspace="8"></a>**Rishi Bhaskar**<br>[github.com/rishibhaskar777](https://github.com/rishibhaskar777) | Full-stack | Frontend and backend |
| **Siddharth Varshney** | UI/UX | Interface and experience design |
| **Shreyansh Gupta** | Architecture and idea | System architecture, design and the original idea |

Want to help? Read [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

[MIT](LICENSE) © 2026 Rishi Bhaskar and Nitin Mittal

<div align="center"><sub>Built on public records, read by TinyFish agents.</sub></div>
