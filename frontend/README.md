# NeevCheck frontend

Next.js 15 (App Router), React 19, TypeScript strict, plain CSS.

```bash
npm install
npm run dev          # http://localhost:3000
npm run lint && npm run typecheck && npm run build
```

- `src/styles/tokens.css` holds the colours, radii and shadows; `globals.css` the reset and shared keyframes.
- Every component has its own CSS Module. Animations are CSS keyframes only.
- `scripts/capture.ts` records the screenshots and the hero GIF used in the README (needs `npx playwright install chromium` and a running `npm run build && npm start`).
- `e2e/` holds the browser tests. `npm run e2e` builds the app and runs it against `e2e/mock-api.ts`, which replays the recorded check of UPRERAPRJ8334 (`e2e/fixtures/`, rewritten by `python -m scripts.export_e2e_fixtures` in `backend/`). Search and the report are fetched by the Next server, where a browser tool cannot intercept requests, so a small mock API stands in for the backend. No test touches the network.
