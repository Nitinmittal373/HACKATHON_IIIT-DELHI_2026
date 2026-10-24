# Architecture

```
Browser (Next.js 15 · TypeScript · Tailwind · Radix · Motion · React Flow)
   │  REST + Server-Sent Events
   ▼
FastAPI (Python)
   ├─ investigations  → 5 lanes, run in two phases (asyncio.gather)
   │     Phase 1: UP-RERA (Search → Web Agent, streamed) · News (Search)
   │     Phase 2: Company (Search → Web Agent) · IBBI/NCLT (Search) · Land authority (Search)
   ├─ matching.py     strict legal-name and project-token matching, news de-duplication
   ├─ scoring.py      deterministic NeevScore (docs/METHODOLOGY.md)
   ├─ insights.py     family tree, grounded Q&A, complaint draft (no language model)
   ├─ store.py        SQLite (swap to PostgreSQL by changing this file only)
   └─ watch           TinyFish Monitor → POST /api/webhooks/tinyfish (shared secret)
   ▼
TinyFish: Search · Fetch · Web Agent (stealth profile, India proxy, max 2 concurrent) · Monitor
```

## Request flow

1. `POST /api/investigations` returns an id and starts the lanes in the background.
2. The War Room opens `GET /api/investigations/{id}/events` (SSE) and shows each step and the agent's live browser.
3. When all lanes finish, the report is scored, saved and announced with a `report` event.
4. The dossier loads `GET /api/reports/{id}`.

## Reliability for the live demo

- Agent slots are limited with a semaphore (`AGENT_CONCURRENCY`, default 2).
- Every Search/Fetch/Agent result is cached per day in `backend/cache/`. `DEMO_MODE=true` replays saved runs,
  shows "replay" in the UI and keeps each claim's original retrieval date.
- `python -m scripts.mock_server` runs the whole app on sample data with no credits, for UI work and rehearsal.
- One failing source never stops the others; it is recorded as unavailable and lowers confidence.

## Security

- Secrets only in `.env` (git-ignored). The frontend never sees the TinyFish key.
- CORS limited to `FRONTEND_ORIGINS`; input length limits; per-IP rate limit on new investigations.
- Webhook protected by `WEBHOOK_SECRET` (constant-time compare).
- Security headers on API and frontend (CSP, nosniff, frame denial, referrer policy).
- Scraped text is rendered as text, never HTML; only `http(s)` links are rendered.
- Agents read public pages only; CAPTCHAs are never solved automatically.

## Scaling path

PostgreSQL for `store.py`, a job queue (Redis + worker) for lanes, one source adapter per state RERA portal
mapped to the same `Signals`/`Evidence` model.
