"""Run real live checks for a list of UP-RERA numbers so a demo never waits.

    python -m scripts.prewarm UPRERAPRJ8334 UPRERAPRJ2634
    python -m scripts.prewarm --file numbers.txt

Every check is live and is stored in the configured database; the reads the v2 sources cache
keep their real read time, so a report shown later says when its pages were really read. The
daily check cap and the 24-hour reuse still apply, so running this twice costs nothing extra.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import load_settings
from app.main import create_app
from app.models import is_new_format, normalize_rera_id
from app.resolve import resolve_number
from app.tinyfish import LiveWebClient


def numbers_from(args: argparse.Namespace) -> list[str]:
    raw = list(args.numbers)
    if args.file:
        raw += Path(args.file).read_text(encoding="utf-8").split()
    found = [normalize_rera_id(text) for text in raw]
    bad = [text for text, number in zip(raw, found, strict=True) if number is None]
    if bad:
        sys.exit(f"Not UP-RERA project numbers: {', '.join(bad)}")
    return list(dict.fromkeys(n for n in found if n))


def details_link(rera_id: str, settings_web: LiveWebClient) -> str | None:
    """New-format numbers have no stable page; search finds the one to send."""
    project = asyncio.run(resolve_number(rera_id, settings_web))
    return project.details_url if project else None


def wait_for_check(client: TestClient, check_id: str) -> str:
    with client.stream("GET", f"/api/checks/{check_id}/events") as response:
        for line in response.iter_lines():
            if line.startswith("data: "):
                event = json.loads(line.removeprefix("data: "))
                if event["type"] == "check.completed":
                    return event["data"]["status"]
    return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run live checks ahead of a demo")
    parser.add_argument("numbers", nargs="*", help="UP-RERA project numbers")
    parser.add_argument("--file", help="a text file of numbers, separated by spaces or lines")
    parser.add_argument("--fresh", action="store_true", help="skip the 24-hour reuse")
    args = parser.parse_args()
    numbers = numbers_from(args)
    if not numbers:
        sys.exit("Give at least one UP-RERA number or --file")

    settings = load_settings().model_copy(update={"v2_sources": True, "rate_limit_per_minute": 100})
    web = LiveWebClient(
        settings.tinyfish_api_key,
        fetch_timeout=settings.fetch_timeout_seconds,
        agent_timeout=settings.agent_timeout_seconds,
        send_max_steps=settings.agent_send_max_steps,
    )
    app = create_app(settings, web=web)
    with TestClient(app) as client:
        for number in numbers:
            body: dict[str, object] = {"rera_id": number, "fresh": args.fresh}
            if is_new_format(number):
                url = details_link(number, web)
                if url is None:
                    print(f"{number}: no UP-RERA page found, skipped")
                    continue
                body["details_url"] = url
            response = client.post("/api/checks", json=body)
            if response.status_code not in (200, 202):
                print(f"{number}: refused ({response.status_code}) {response.text[:200]}")
                continue
            check = response.json()
            status = "reused" if check.get("reused") else wait_for_check(client, check["id"])
            report = client.get(f"/api/checks/{check['id']}/report")
            if report.status_code != 200:
                print(f"{number}: {status}, no report")
                continue
            data = report.json()
            v2 = data.get("score_v2") or {}
            print(
                f"{number}: {status}  v1 {data['score']['value']}  "
                f"v2 {v2.get('value')} ({v2.get('band_label')})"
            )


if __name__ == "__main__":
    main()
