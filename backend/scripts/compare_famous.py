"""Run the famous projects through the whole resolver and write a before / after table.

    python -m scripts.compare_famous [output.md]

"Before" is the portal-only resolver (docs/baseline-famous.md, recorded earlier); "after" is
resolve_any, live. A project counts when a candidate's name or promoter matches, or when public
pages say it is older than RERA and the note names it. Only free Search and Fetch are used.
"""

import asyncio
import re
import sys
from pathlib import Path

from app.config import load_settings
from app.states.openweb import CACHE
from app.states.resolver import resolve_any
from app.tinyfish import LiveWebClient, WebError
from scripts.famous_projects import FAMOUS, Famous

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "docs" / "baseline-famous.md"
# One project at a time, as a buyer would: a search of one project uses up to a dozen Searches and
# TinyFish allows 30 a minute.
PAUSE_SECONDS = 40


def before_results() -> dict[str, str]:
    """query -> 'found' / 'not found' from the committed baseline table."""
    rows = re.findall(r"^\| (.+?) \| (found|not found|error) \|", BASELINE.read_text("utf-8"), re.M)
    return dict(rows)


async def after(famous: Famous, web: LiveWebClient) -> tuple[str, str]:
    try:
        found = await resolve_any(famous.query, web)
    except WebError as error:
        return "error", str(error)
    right = [p for p in found.candidates if famous.matches(p)]
    if right:
        top = right[0]
        return "found", f"{top.rera_id} · {top.status} · {', '.join(top.sources[:3])}"
    for note in found.pre_rera:
        if re.search(famous.expect, f"{note.name} {note.statement}", re.IGNORECASE):
            return "pre-RERA", note.statement[:90]
    return "not found", f"{len(found.candidates)} other candidates"


async def main(output: Path) -> None:
    settings = load_settings()
    web = LiveWebClient(settings.tinyfish_api_key, fetch_timeout=45, agent_timeout=60)
    before = before_results()
    rows = []
    try:
        for famous in FAMOUS:
            CACHE.clear()
            await asyncio.sleep(PAUSE_SECONDS)
            result, detail = await after(famous, web)
            rows.append((famous.query, before.get(famous.query, "?"), result, detail))
    finally:
        await web.aclose()
    lines = ["| Project | Before | After | After: detail |", "|---|---|---|---|"]
    lines += [f"| {q} | {b} | {a} | {d} |" for q, b, a, d in rows]
    right = sum(a in ("found", "pre-RERA") for _, _, a, _ in rows)
    was = sum(b == "found" for _, b, _, _ in rows)
    lines.append(f"\nBefore: {was} of {len(rows)}. After: {right} of {len(rows)}.")
    write(output, lines)
    print("\n".join(lines))


def write(output: Path, lines: list[str]) -> None:
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(
        main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs" / "find-any-project.md")
    )
