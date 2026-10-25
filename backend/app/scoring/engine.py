"""NeevScore engine: a pure function from findings to a score.

    score = round(100 - sum(weight x penalty)), penalties capped per area

The same findings always give the same score, and every point lost is a
Driver that points back at the finding behind it.
"""

import math
from collections.abc import Iterable

from app.models import Area, AreaScore, CheckKey, Driver, Finding, Score
from app.scoring import weights as w


def score(findings: list[Finding], checks_read: Iterable[CheckKey]) -> Score:
    has_completion_certificate = any(f.kind == "completion_certificate" for f in findings)
    penalties = {f.id: _penalty(f, has_completion_certificate) for f in findings}
    drivers, area_totals = _apply_area_caps(findings, penalties)

    value = _round_half_up(100 - sum(-driver.points for driver in drivers))
    hard_stop_reason = next((r for f in findings if (r := _hard_stop_reason(f))), None)
    if hard_stop_reason:
        value = min(value, w.HARD_STOP_CAP)

    read = set(checks_read)
    return Score(
        value=value,
        band=next(band for floor, band in w.BANDS if value >= floor),
        confidence=round(len(read & set(w.KEY_CHECKS)) / len(w.KEY_CHECKS), 2),
        hard_stop=hard_stop_reason is not None,
        hard_stop_reason=hard_stop_reason,
        drivers=sorted(drivers, key=lambda driver: driver.points),
        areas=[
            AreaScore(area=a, label=w.AREA_LABELS[a], weight=weight, penalty=area_totals[a])
            for a, weight in w.AREA_WEIGHTS.items()
        ],
        checks_unread=[key for key in w.KEY_CHECKS if key not in read],
    )


def _penalty(finding: Finding, has_completion_certificate: bool) -> int:
    match finding.kind:
        case "completion_extended":
            count = finding.count or 0
            return w.EXTENSION_FIRST + w.EXTENSION_EACH_MORE * (count - 1) if count > 0 else 0
        case "past_end_date":
            # A completion certificate on record means the delay is not counted, but
            # the certificate itself stays a finding to verify.
            if has_completion_certificate:
                return 0
            months = finding.months or 0
            return next((penalty for limit, penalty in w.DELAY_STEPS if months > limit), 0)
        case "insolvency_scope":
            return w.INSOLVENCY_OTHER_PROJECT if finding.scope == "other_project" else 100
        case "registration_revoked":
            return 100
        case "land_dues":
            return w.LAND_DUES
        case "news_story":
            return w.NEWS_PER_STORY
        case "promoter_complaints":
            return _step(finding.count, w.PROMOTER_COMPLAINT_STEPS)
        case "project_complaints":
            return _step(finding.count, w.PROJECT_COMPLAINT_STEPS)
        case _:
            return 0


def _step(count: int | None, steps: list[tuple[int, int]]) -> int:
    return next((penalty for least, penalty in steps if (count or 0) >= least), 0)


def _hard_stop_reason(finding: Finding) -> str | None:
    if finding.kind == "registration_revoked":
        return "UP-RERA registration lapsed or revoked"
    if finding.kind == "insolvency_scope" and finding.scope == "company":
        return "Insolvency covers the whole company"
    if finding.kind == "insolvency_scope" and finding.scope == "this_project":
        return "Insolvency covers this project"
    return None


def _apply_area_caps(
    findings: list[Finding], penalties: dict[str, int]
) -> tuple[list[Driver], dict[Area, int]]:
    """Spend each area's cap on its largest penalties first, so drivers add up exactly."""
    used: dict[Area, int] = dict.fromkeys(w.AREA_WEIGHTS, 0)
    drivers: list[Driver] = []
    for finding in sorted(findings, key=lambda f: penalties[f.id], reverse=True):
        area = w.KIND_AREAS.get(finding.kind)
        if area is None or penalties[finding.id] == 0:
            continue
        applied = min(penalties[finding.id], w.AREA_CAPS[area] - used[area])
        if applied <= 0:
            continue
        used[area] += applied
        drivers.append(
            Driver(
                finding_id=finding.id,
                title=finding.title,
                area=area,
                penalty=applied,
                points=-round(w.AREA_WEIGHTS[area] * applied, 2),
            )
        )
    return drivers, used


def _round_half_up(value: float) -> int:
    return math.floor(value + 0.5)
