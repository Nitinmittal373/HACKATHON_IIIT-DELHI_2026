# NeevCheck frontend

Next.js 15 (App Router), React 19, TypeScript strict, plain CSS.

```bash
npm install
npm run dev          # http://localhost:3000
npm run lint && npm run typecheck && npm run build
```

- `src/styles/tokens.css` holds the colours, radii and shadows; `globals.css` the reset and shared keyframes.
- Every component has its own CSS Module. Animations are CSS keyframes only.
- `scripts/capture.ts` records the README pictures (home animation, report, War Room animation, login page) from a production build that talks to `e2e/mock-api.ts`, so it never calls TinyFish. The steps are in the header of the script; each GIF must stay under 1 MB.
- `src/lib/api-schema.d.ts` is generated from `contracts/openapi.json` (`npm run gen:api`, or `make contract` from the repository root); never edit it. `src/lib/types.ts` only names its types.
- `npm run test:unit` runs plain Node tests next to the code (the score scale, and a guard that fails if the classic 0–100 score or a copy of the scale reaches the interface).
- `e2e/` holds the browser tests. `npm run e2e` builds the app and runs it against `e2e/mock-api.ts`, which replays the recorded check of UPRERAPRJ8334 (`e2e/fixtures/`, rewritten by `python -m scripts.export_e2e_fixtures` in `backend/`). Search and the report are fetched by the Next server, where a browser tool cannot intercept requests, so a small mock API stands in for the backend. No test touches the network.
