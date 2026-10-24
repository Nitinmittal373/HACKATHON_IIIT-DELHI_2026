# Working on NeevCheck

## Branches
- `main` always runs. Never push broken code to it.
- One branch per task: `feat/war-room-live-browser`, `fix/mca-name-match`, `docs/methodology`.
- Open a pull request into `main`; CI must be green; one teammate reviews.

## Commits
Short, present tense, what changed and why:
`feat(scoring): treat insolvency of another project as review, not hard stop`
Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`.

## Before you commit
1. `git status`: `.env`, `.venv/`, `node_modules/`, `backend/data/` must not appear.
2. Backend: `python -m pytest -q`
3. Frontend: `npm run typecheck && npm run lint`

## Who owns what
| Area | Folder | Owner |
|---|---|---|
| Agents and sources | `backend/app/sources.py`, `tf.py` | [name] |
| Scoring, API, data | `backend/app/scoring.py`, `main.py`, `store.py` | [name] |
| Frontend | `frontend/` | [name] |
| Research, QA, demo | `docs/`, test projects, pitch | [name] |

## Rules that protect the product
- No source, no claim. Every finding is `Evidence` with a URL and retrieval time.
- Change a scoring rule only together with `docs/METHODOLOGY.md` and a test.
- Never present sample or mock data as a real check.
