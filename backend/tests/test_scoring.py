from datetime import date
from itertools import count

import pytest

from app.models import CheckKey, Finding, InsolvencyScope
from app.scoring.engine import score
from app.scoring.weights import KEY_CHECKS

_ids = count(1)
URL = "https://www.up-rera.in/Frm_View_Project_Details.aspx?id=8334"


def finding(
    kind: str,
    *,
    count: int | None = None,
    months: int | None = None,
    scope: InsolvencyScope | None = None,
) -> Finding:
    return Finding(
        id=f"f{next(_ids)}",
        source="uprera",
        kind=kind,
        title=kind.replace("_", " "),
        verdict="review",
        reliability="primary",
        source_url=URL,
        read_on=date(2026, 10, 25),
        count=count,
        months=months,
        scope=scope,
    )


ALL_CHECKS: list[CheckKey] = list(KEY_CHECKS)


def test_worked_example_from_the_docs_gives_76() -> None:
    findings = [
        finding("completion_extended", count=3),
        finding("insolvency_admitted"),
        finding("insolvency_scope", scope="other_project"),
        finding("news_story"),
        finding("court_order"),
    ]
    read: list[CheckKey] = [
        "registration",
        "extensions",
        "company_status",
        "insolvency",
        "land_dues",
    ]

    result = score(findings, read)

    assert result.value == 76
    assert result.band == "Moderate"
    assert result.confidence == 0.71
    assert not result.hard_stop
    assert [d.points for d in result.drivers] == [-14.0, -9.0, -1.0]
    assert result.checks_unread == ["completion_date", "consumer_cases"]


def test_insolvency_of_the_company_is_a_hard_stop_capped_at_39() -> None:
    result = score([finding("insolvency_scope", scope="company")], ALL_CHECKS)
    assert result.value == 39
    assert result.band == "Critical"
    assert result.hard_stop
    assert result.hard_stop_reason == "Insolvency covers the whole company"


def test_insolvency_of_this_project_is_a_hard_stop() -> None:
    assert score([finding("insolvency_scope", scope="this_project")], ALL_CHECKS).hard_stop


def test_no_findings_score_100_with_no_confidence() -> None:
    result = score([], [])
    assert result.value == 100
    assert result.band == "Low"
    assert result.confidence == 0.0
    assert result.checks_unread == list(KEY_CHECKS)


@pytest.mark.parametrize(
    ("count", "value"), [(19, 100), (20, 97), (100, 94), (499, 94), (500, 91), (2803, 91)]
)
def test_promoter_complaints_count_in_builder_history(count: int, value: int) -> None:
    assert score([finding("promoter_complaints", count=count)], ALL_CHECKS).value == value


@pytest.mark.parametrize(("count", "points"), [(0, []), (1, [-2.25]), (9, [-2.25]), (15, [-6.0])])
def test_project_complaints_count_in_legal(count: int, points: list[float]) -> None:
    result = score([finding("project_complaints", count=count)], ALL_CHECKS)
    assert [d.points for d in result.drivers] == points


def test_penalties_in_one_area_are_capped_at_100() -> None:
    findings = [finding("completion_extended", count=3), finding("past_end_date", months=40)]
    result = score(findings, ALL_CHECKS)
    # 70 + 70 in execution is capped at 100, so 20% x 100 = 20 points.
    assert result.value == 80
    assert sum(d.penalty for d in result.drivers) == 100


def test_news_is_capped_below_a_full_area() -> None:
    result = score([finding("news_story") for _ in range(9)], ALL_CHECKS)
    assert result.value == 94


def test_delay_steps() -> None:
    def delay_score(months: int) -> int:
        return score([finding("past_end_date", months=months)], ALL_CHECKS).value

    assert delay_score(12) == 100
    assert delay_score(13) == 92
    assert delay_score(25) == 86


def test_completion_certificate_skips_the_delay_penalty() -> None:
    findings = [finding("past_end_date", months=105), finding("completion_certificate")]
    result = score(findings, ALL_CHECKS)
    assert result.value == 100
    assert result.drivers == []


def test_absence_and_context_never_add_points() -> None:
    findings = [finding("land_clear"), finding("registration"), finding("court_order")]
    assert score(findings, ALL_CHECKS).value == 100


def test_unread_sources_lower_confidence_not_the_score() -> None:
    findings = [finding("completion_extended", count=1)]
    full = score(findings, ALL_CHECKS)
    partial = score(findings, ["registration"])
    assert full.value == partial.value == 94
    assert partial.confidence < full.confidence
