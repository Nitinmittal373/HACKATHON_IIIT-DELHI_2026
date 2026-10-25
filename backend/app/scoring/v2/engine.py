"""NeevScore v2: a pure function from findings to a 300-900 score with reason codes.

    score = clip(900 - 6 x sum(weight x pillar penalty), 300, 900)

Each pillar's penalty is capped at 100 (news at 60). The cap is spent on the largest
penalties first, so the drivers and reason codes add up to the score exactly. Like v1, the
same findings always give the same score and a missing record never adds points.
"""

import math
from collections.abc import Iterable, Sequence

from app.models import Finding
from app.scoring.v2 import weights as w
from app.scoring.v2.models import BandV2, DriverV2, Pillar, PillarId, ReasonCode, ScoreV2
from app.scoring.v2.reasons import DATA_UNAVAILABLE, label_for
from app.scoring.v2.rules import RULES, hard_stop_reason


def score_v2(
    findings: list[Finding],
    pillars_read: Iterable[PillarId],
    unavailable: Sequence[str] = (),
) -> ScoreV2:
    """`unavailable` names the records that could not be read (a CAPTCHA, a source down)."""
    drivers, penalties = _apply_pillar_caps(findings)
    lost = sum(w.PILLAR_WEIGHTS[p] * penalty for p, penalty in penalties.items())
    value = clip(900 - w.POINTS_PER_PENALTY * lost)

    stop = next((r for f in findings if (r := hard_stop_reason(f))), None)
    if stop:
        value = min(value, w.HARD_STOP_CAP)

    read = set(pillars_read)
    unread = [p for p in w.PILLAR_WEIGHTS if p not in read]
    confidence = round(len(read) / len(w.PILLAR_WEIGHTS), 2)
    provisional = confidence < w.MIN_CONFIDENCE_FOR_BAND and stop is None
    band: BandV2 = "insufficient_evidence" if provisional else band_for(value)
    return ScoreV2(
        value=value,
        band=band,
        band_label=w.BAND_LABELS[band],
        provisional=provisional,
        hard_stop=stop is not None,
        hard_stop_reason=stop,
        confidence=confidence,
        pillars=[
            Pillar(
                id=p,
                name=w.PILLAR_NAMES[p],
                weight=weight,
                penalty=penalties[p],
                points=-_points(weight, penalties[p]),
            )
            for p, weight in w.PILLAR_WEIGHTS.items()
        ],
        reason_codes=_reason_codes(findings, drivers, unread, unavailable),
        drivers=sorted(drivers, key=lambda d: d.points),
        pillars_unread=unread,
    )


def clip(raw: float) -> int:
    return min(w.SCALE_TOP, max(w.SCALE_FLOOR, math.floor(raw + 0.5)))


def band_for(value: int) -> BandV2:
    return next(band for floor, band in w.BANDS if value >= floor)


def _points(weight: float, penalty: int) -> float:
    return round(w.POINTS_PER_PENALTY * weight * penalty, 2)


def _apply_pillar_caps(findings: list[Finding]) -> tuple[list[DriverV2], dict[PillarId, int]]:
    used: dict[PillarId, int] = dict.fromkeys(w.PILLAR_WEIGHTS, 0)
    scored = [(f, RULES[f.kind]) for f in findings if f.kind in RULES]
    costs = {f.id: rule.penalty(f) for f, rule in scored}
    drivers: list[DriverV2] = []
    for finding, rule in sorted(scored, key=lambda pair: costs[pair[0].id], reverse=True):
        applied = min(costs[finding.id], w.PILLAR_CAPS[rule.pillar] - used[rule.pillar])
        if applied <= 0:
            continue
        used[rule.pillar] += applied
        drivers.append(
            DriverV2(
                finding_id=finding.id,
                pillar=rule.pillar,
                code=rule.code,
                penalty=applied,
                points=-_points(w.PILLAR_WEIGHTS[rule.pillar], applied),
            )
        )
    return drivers, used


def _reason_codes(
    findings: list[Finding],
    drivers: list[DriverV2],
    unread: list[PillarId],
    unavailable: Sequence[str],
) -> list[ReasonCode]:
    by_id = {f.id: f for f in findings}
    grouped: dict[str, list[DriverV2]] = {}
    for driver in drivers:
        grouped.setdefault(driver.code, []).append(driver)
    codes = [
        ReasonCode(
            code=code,
            label=label_for(code, [by_id[d.finding_id] for d in group]),
            finding_ids=[d.finding_id for d in group],
            points=round(sum(d.points for d in group), 2),
        )
        for code, group in grouped.items()
    ]
    codes.sort(key=lambda c: (c.points, c.code))
    missing = [*unavailable, *(w.PILLAR_NAMES[p] for p in unread)]
    if missing:
        label = "Data unavailable: " + "; ".join(dict.fromkeys(missing))
        codes.append(ReasonCode(code=DATA_UNAVAILABLE, label=label, finding_ids=[], points=0.0))
    return codes
