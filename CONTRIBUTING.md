# Contributing to NeevCheck

Thanks for helping families check a builder before they book a home.

## Maintainers

| Name | GitHub | Focus |
| --- | --- | --- |
| Rishi Bhaskar | [@rishibhaskar777](https://github.com/rishibhaskar777) | Product, frontend, design |
| Nitin Mittal | [@Nitinmittal373](https://github.com/Nitinmittal373) | Backend, TinyFish agents, data |

## Run it locally

See [Getting started](README.md#getting-started) in the README. Checks need a TinyFish API key in `.env`; the test suite does not.

## Workflow

1. Create a branch from `main`: `feat/agent-cam`, `fix/score-rounding`, `docs/readme`.
2. Keep each pull request to one change.
3. Make sure these pass before you open the pull request:

   ```bash
   # backend
   cd backend && ruff check . && pytest -q
   # frontend
   cd frontend && npm run lint && npm run typecheck && npm run build
   ```

4. Fill in the pull request template. One maintainer reviews and merges.

## Commit messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(backend): stream TinyFish live browser URLs to the check page

Why the change was needed, in one or two sentences.

- what changed, one line per meaningful change
- how it was tested
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`.

## Code style

- **Python:** small functions, type hints, `ruff` formatting rules in `backend/pyproject.toml`.
- **TypeScript:** function components, one component per file, plain CSS in `src/styles`.
- **Data rule:** no source, no claim. Every finding shown to a user must carry a source link and the time it was read.

## Never commit

- `.env` or any key, token or password
- local databases (`backend/data/*.db`) or cached agent runs
