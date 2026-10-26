"""Put two or three finished checks side by side, one row per question a buyer asks.

Pure: reports in, comparison out. A value the check could not read is None, never zero, so
an unread source can never look like a clean record.
"""

from typing import Literal

from app.api_model import ApiModel
from app.models import (
    Area,
    Band,
    CheckKey,
    DisplayScore,
    Finding,
    PillarId,
    Project,
    Report,
)
from app.scoring.v2 import weights as v2
from app.scoring.weights import KEY_CHECKS

InsolvencyStatus = Literal[
    "none_found", "admitted", "other_project", "this_project", "company", "unverified"
]
BestReason = Literal["best_score", "tie", "not_enough_evidence"]
TOP_FINDINGS = 3
# Findings worth showing when fewer than three cost points.
NOTABLE = ("red_flag", "fail", "review")


class AreaPoints(ApiModel):
    area: Area
    label: str
    lost: float
    # The most this area can take off the score: its weight times a full penalty.
    max: float


class PillarPoints(ApiModel):
    id: PillarId
    name: str
    # Points this pillar took off the 300-900 score, and the most it could take.
    lost: float
    max: float


class FindingLine(ApiModel):
    title: str
    source_url: str
    points: float


class ComparedProject(ApiModel):
    check_id: str
    project: Project
    # The score to show and rank by; `score`, `band` and `areas` are the classic 0-100 view.
    display_score: DisplayScore
    pillars: list[PillarPoints]
    score: int
    band: Band
    confidence: float
    hard_stop: bool
    areas: list[AreaPoints]
    delay_months: int | None
    project_complaints: int | None
    promoter_complaints: int | None
    insolvency: InsolvencyStatus | None
    company_status: str | None
    unread: list[CheckKey]
    top_findings: list[FindingLine]


class Comparison(ApiModel):
    projects: list[ComparedProject]
    # The check with the best score among those read well enough to rank, if there is one.
    best: str | None
    reason: BestReason


def compare(reports: list[Report]) -> Comparison:
    projects = [compared(report) for report in reports]
    best, reason = best_on_records(projects)
    return Comparison(projects=projects, best=best, reason=reason)


def best_on_records(projects: list[ComparedProject]) -> tuple[str | None, BestReason]:
    """Rank only checks that read at least half the pillars; a thin check proves little."""
    ranked = [p for p in projects if p.display_score.confidence >= v2.MIN_CONFIDENCE_FOR_BAND]
    if len(ranked) < 2:
        return None, "not_enough_evidence"
    top = max(p.display_score.value for p in ranked)
    leaders = [p for p in ranked if p.display_score.value == top]
    if len(leaders) > 1:
        return None, "tie"
    return leaders[0].check_id, "best_score"


def compared(report: Report) -> ComparedProject:
    read = set(KEY_CHECKS) - set(report.score.checks_unread)
    by_kind = {finding.kind: finding for finding in report.findings}
    return ComparedProject(
        check_id=report.check.id,
        project=report.project,
        display_score=report.display_score,
        pillars=[
            PillarPoints(
                id=pillar.id,
                name=pillar.name,
                lost=abs(pillar.points),
                max=round(v2.POINTS_PER_PENALTY * pillar.weight * 100, 2),
            )
            for pillar in report.score_v2.pillars
        ],
        score=report.score.value,
        band=report.score.band,
        confidence=report.score.confidence,
        hard_stop=report.score.hard_stop,
        areas=[
            AreaPoints(
                area=area.area,
                label=area.label,
                lost=round(area.weight * area.penalty, 2),
                max=round(area.weight * 100, 2),
            )
            for area in report.score.areas
        ],
        delay_months=delay_months(by_kind, read),
        project_complaints=_count(by_kind.get("project_complaints")),
        promoter_complaints=_count(by_kind.get("promoter_complaints")),
        insolvency=insolvency(by_kind, read),
        company_status=company_status(by_kind, read),
        unread=report.score.checks_unread,
        top_findings=top_findings(report),
    )


def delay_months(by_kind: dict[str, Finding], read: set[CheckKey]) -> int | None:
    """Months past the completion date on record; 0 when the date has not passed."""
    if "completion_date" not in read:
        return None
    late = by_kind.get("past_end_date")
    return late.months if late and late.months is not None else 0


def insolvency(by_kind: dict[str, Finding], read: set[CheckKey]) -> InsolvencyStatus | None:
    if "insolvency" not in read and "insolvency_scope" not in by_kind:
        return None
    if (scope := by_kind.get("insolvency_scope")) and scope.scope:
        return scope.scope
    if "insolvency_scope_unverified" in by_kind:
        return "unverified"
    if "insolvency_admitted" in by_kind:
        return "admitted"
    return "none_found"


def company_status(by_kind: dict[str, Finding], read: set[CheckKey]) -> str | None:
    """The registry's own words ("Active", "Strike Off"), without the CIN."""
    if "company_status" not in read:
        return None
    # A registry status that means insolvency is recorded as an insolvency finding instead.
    finding = by_kind.get("company_status") or by_kind.get("insolvency_scope")
    if finding is None or finding.source != "registry":
        return None
    status = finding.title.removeprefix("Company status:").split("(CIN")[0]
    return status.strip(" .") or None


def top_findings(report: Report) -> list[FindingLine]:
    """The findings that cost the most points, then other red flags and items to review."""
    by_id = {finding.id: finding for finding in report.findings}
    # Drivers are sorted biggest loss first, in points of the 300-900 score.
    lines = [
        FindingLine(
            title=by_id[d.finding_id].title,
            source_url=by_id[d.finding_id].source_url,
            points=d.points,
        )
        for d in report.score_v2.drivers
        if d.finding_id in by_id
    ]
    driven = {d.finding_id for d in report.score_v2.drivers}
    for verdict in NOTABLE:
        lines += [
            FindingLine(title=f.title, source_url=f.source_url, points=0)
            for f in report.findings
            if f.verdict == verdict and f.id not in driven
        ]
    return lines[:TOP_FINDINGS]


def _count(finding: Finding | None) -> int | None:
    return finding.count if finding else None
