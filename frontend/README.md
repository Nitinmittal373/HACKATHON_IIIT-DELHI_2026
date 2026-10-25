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
