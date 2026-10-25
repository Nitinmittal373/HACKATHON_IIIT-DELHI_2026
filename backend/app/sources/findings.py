"""One place that builds a Finding, so every source fills the honesty fields the same way."""

import uuid
from datetime import date, datetime

from app.models import Area, Finding, Reliability, SourceName, Verdict


def build_finding(
    *,
    source: SourceName,
    reliability: Reliability,
    kind: str,
    area: Area,
    title: str,
    verdict: Verdict,
    url: str,
    today: date,
    now: datetime,
    **facts: object,
) -> Finding:
    """A finding always carries where it came from (`url`) and when it was read."""
    return Finding.model_validate(
        {
            "id": uuid.uuid4().hex,
            "source": source,
            "kind": kind,
            "title": title,
            "area": area,
            "verdict": verdict,
            "reliability": reliability,
            "source_url": url,
            "read_on": today,
            "read_at": now,
            **facts,
        }
    )
