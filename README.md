# NeevCheck

**Know your builder before you pay the booking amount.**

NeevCheck checks under-construction housing projects in Uttar Pradesh. Web agents read UP-RERA, company
records, IBBI/NCLT insolvency records, land-authority notices and the news, then produce an explainable
**NeevScore (300–900)** where every claim has a source, a status and a retrieval date. Watch mode keeps
checking after you book.

Built by Team RYZEN (KIET Group of Institutions) for HackIIITD 2026 · Powered by the TinyFish API.

## Features

- **War Room**: five lanes run live; watch each agent's real browser.
- **Project dossier**: data tiles, delivery timeline, insights, what was checked (including what was not found), next steps.
- **Reproducible score**: the calculation is shown on every report ([methodology](docs/METHODOLOGY.md)).
- **Evidence ledger**: Verified · Partially verified · Requires review, with source links and original retrieval dates.
- **Builder family tree**, **Ask NeevCheck** (answers only from cited evidence), **complaint draft**, **PDF**, **compare**.
- **Watch mode** with TinyFish Monitor and alerts. Light and dark themes, English and Hindi.

## Repository layout

```
backend/            FastAPI service (Python)
  app/              config, models, sources (lanes), matching, scoring, insights, store, tf (TinyFish), main
  tests/            pytest: scoring rules, matching, full API flow with TinyFish mocked
  scripts/          seed_sample.py, mock_server.py
frontend/           Next.js 15 app (TypeScript, Tailwind CSS, Radix UI, Motion, React Flow)
  src/app/          landing, methodology, and the app: dashboard, check, reports, compare, watch
  src/components/   UI primitives and feature components
  src/lib/          API client, types, i18n, utilities
docs/               METHODOLOGY.md, ARCHITECTURE.md
.github/workflows/  CI: backend tests, frontend typecheck, lint and build
```

## Setup (Windows PowerShell)

Requirements: Python 3.11+, Node.js 20+, a TinyFish API key.

```powershell
git clone https://github.com/Nitinmittal373/HACKATHON_IIIT-DELHI_2026.git
cd HACKATHON_IIIT-DELHI_2026
copy .env.example .env                 # paste your TinyFish key into .env
```

Backend (terminal 1):

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q                    # all tests should pass
uvicorn app.main:app --reload --port 8000
```

Frontend (terminal 2):

```powershell
cd frontend
copy .env.example .env.local
npm install
npm run dev                            # http://localhost:3000
```

No credits to spare? Run `python -m scripts.mock_server` instead of uvicorn. It serves sample data
through the same API, so the whole app works offline. Sample data must never be presented as a real check.

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/investigations` | Start a check `{"query": "..."}` → `{"id"}` |
| GET | `/api/investigations/{id}` | Status |
| GET | `/api/investigations/{id}/events` | Live events (SSE) |
| GET | `/api/reports` | Saved reports |
| GET | `/api/reports/{id}` | Full report |
| POST | `/api/reports/{id}/ask` | Answer from cited evidence |
| POST | `/api/reports/{id}/complaint-draft` | UP-RERA complaint draft |
| GET | `/api/projects/{id}/evidence` | Evidence ledger |
| POST | `/api/projects/{id}/watch` | Start TinyFish Monitors |
| GET | `/api/watches`, `/api/alerts` | Watch list and alerts |
| POST | `/api/webhooks/tinyfish` | Monitor webhook (needs `token`) |
| GET | `/api/health` | Key loaded, demo mode, watch readiness |

## Security

- Keys live only in `.env` (git-ignored). Never paste keys in code, chats, screenshots or commits.
- Before every commit, run `git status` and confirm `.env`, `.venv/`, `node_modules/` and `backend/data/` are not listed.
- See [ARCHITECTURE.md](docs/ARCHITECTURE.md#security) for the full list.

## Responsible use

NeevScore is a risk indicator based on public records, not a credit rating or legal advice. Findings are
stated as cited facts with retrieval dates; allegations and news are marked "requires review". Government
CAPTCHAs are never solved automatically.

## Team

Team RYZEN · KIET Group of Institutions

- Rishi Bhaskar ([@rishibhaskar777](https://github.com/rishibhaskar777))
- Nitin Mittal ([@Nitinmittal373](https://github.com/Nitinmittal373))
