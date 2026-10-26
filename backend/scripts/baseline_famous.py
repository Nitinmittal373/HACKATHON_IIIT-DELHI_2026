"""Run the famous projects through the resolver and write a found / not found table.

    python -m scripts.baseline_famous [output.md]

Only free Search and Fetch are used. The searches are also saved as a fixture so the same
table can be replayed in tests.
"""

import asyncio
import json
import sys
from pathlib import Path

from app.config import load_settings
from app.states.resolver import resolve_any
from app.tinyfish import LiveWebClient, WebError
from scripts.famous_projects import FAMOUS
from scripts.recorder import RecordingWebClient, scrub

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "backend" / "tests" / "fixtures"


async def main(output: Path) -> None:
    settings = load_settings()
    key = settings.tinyfish_api_key.get_secret_value()
    web = RecordingWebClient(
        LiveWebClient(settings.tinyfish_api_key, fetch_timeout=45, agent_timeout=60)
    )
    rows = []
    try:
        for famous in FAMOUS:
            try:
                found = await resolve_any(famous.query, web)
            except WebError as error:
                rows.append((famous.query, "error", str(error)))
                continue
            right = [p for p in found.candidates if famous.matches(p)]
            if right:
                top = right[0]
                rows.append((famous.query, "found", f"{top.rera_id} {top.name or ''}".strip()))
            else:
                rows.append(
                    (famous.query, "not found", f"{len(found.candidates)} other candidates")
                )
    finally:
        await web.aclose()
    lines = ["| Project | Result | Detail |", "|---|---|---|"]
    lines += [f"| {q} | {result} | {detail} |" for q, result, detail in rows]
    total = sum(result == "found" for _, result, _ in rows)
    lines.append(f"\n{total} of {len(rows)} found.")
    save(output, lines, web.recording(), key)
    print("\n".join(lines))


def save(output: Path, lines: list[str], recording: dict, key: str) -> None:
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    text = scrub(json.dumps(recording, indent=2, ensure_ascii=False))
    if key in text:
        sys.exit("Refusing to write the fixture: it contains the API key")
    (FIXTURES / "baseline_famous.json").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(
        main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs" / "baseline-famous.md")
    )
