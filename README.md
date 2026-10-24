# NeevCheck

**CIBIL for builders.** AI web agents read UP-RERA, company (MCA), insolvency (IBBI/NCLT), land-authority and news records in parallel, give every housing project an explainable **NeevScore (300–900)** with source-linked reason codes, and keep watching after you book.

Built at HackIIITD 2026 · Powered by the TinyFish API.

## How it works

```
Query (project / RERA no. / builder)
   │
   ├─ Phase 1 ─ RERA lane: TinyFish Search finds the UP-RERA page (free) → Agent reads it (streamed)
   │            News lane: TinyFish Search (news) for delays / protests (free)
   └─ Phase 2 ─ MCA lane: Search → Agent reads the public company profile
                IBBI lane: Search ibbi.gov.in / nclt.gov.in for insolvency (free)
                Authority lane: Search Noida / GNIDA / YEIDA dues reports (free)
   ▼
Evidence ledger (every claim = source URL + timestamp)  →  NeevScore (deterministic, backend/app/scoring.py)
   ▼
War Room UI (live agent steps)  ·  Complaint draft  ·  Watch mode (TinyFish Monitor → webhook)
```

- Agents are capped at `AGENT_CONCURRENCY` (2 on pay-as-you-go); Search/Fetch are free and run in parallel.
- Every agent/search result is cached per day in `backend/cache/`. `DEMO_MODE=true` replays cached runs (with their recorded steps) so the stage demo never waits on a slow government site.
- The score never comes from an LLM. "Not checked" lowers **confidence**; it is never treated as clean.

## Setup (Windows PowerShell)

```powershell
git clone https://github.com/Nitinmittal373/HACKATHON_IIIT-DELHI_2026.git
cd HACKATHON_IIIT-DELHI_2026
copy .env.example .env          # then paste your TinyFish key into .env
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q             # scoring tests should pass
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000 and search e.g. `Supertech Eco Village`.

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/investigate` `{"query": "..."}` | Start an investigation → `job_id` |
| GET | `/api/investigate/{id}/events` | Server-Sent Events for the War Room |
| GET | `/api/report/{id}` | Signals, evidence, NeevScore |
| GET | `/api/report/{id}/complaint` | UP-RERA complaint draft from cited evidence |
| POST | `/api/watch/{id}` | Create TinyFish Monitors (needs `PUBLIC_BASE_URL`) |
| POST | `/api/webhooks/tinyfish` | Monitor webhook receiver |
| GET | `/api/health` | Checks key loaded / demo mode |

## Security

- Keys live only in `.env` (git-ignored). Never paste keys in code, chats or commits.
- On Vercel / Render, set keys in the platform's environment variables.
- Scraped text is escaped before display.

## Responsible use

NeevScore is a risk indicator based on public records, not a credit rating or legal advice. Findings are stated as cited facts with check dates. Government CAPTCHAs are never auto-solved. Director data is limited to names and DINs already published in public registers.

## Models and APIs used

- TinyFish Search, Fetch, Web Agent (streamed), Monitor (Python SDK `tinyfish`)
