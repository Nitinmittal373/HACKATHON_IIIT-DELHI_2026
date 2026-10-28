from datetime import date
from itertools import count
from pathlib import Path

import pytest

from app.models import Finding, InsolvencyScope, Reliability
from app.scoring.v2 import band_for, clip, partly_read, pillars_read, score_v2
from app.scoring.v2.models import PillarId
from tests.test_recorded_check import check

_ids = count(1)
URL = "https://www.up-rera.in/Frm_View_Project_Details.aspx?id=8334"
ALL: list[PillarId] = ["P1", "P2", "P3", "P4", "P5", "P6"]


def finding(
    kind: str,
    *,
    count: int | None = None,
    months: int | None = None,
    total: int | None = None,
    scope: InsolvencyScope | None = None,
    reliability: Reliability = "primary",
    occurred_on: date | None = None,
) -> Finding:
    return Finding(
        id=f"f{next(_ids)}",
        source="uprera",
        kind=kind,
        title=kind.replace("_", " "),
        verdict="review",
        reliability=reliability,
        source_url=URL,
        read_on=date(2026, 10, 25),
        count=count,
        months=months,
        total=total,
        scope=scope,
        occurred_on=occurred_on,
    )


def penalty_of(kind: str, pillar: str, **facts: object) -> int:
    result = score_v2([finding(kind, **facts)], ALL)  # type: ignore[arg-type]
    return next(p.penalty for p in result.pillars if p.id == pillar)


def test_nothing_found_scores_900_and_never_adds_points() -> None:
    result = score_v2([], ALL)

    assert (result.value, result.band) == (900, "Low")
    assert result.reason_codes == []


@pytest.mark.parametrize(
    ("kind", "pillar", "facts", "expected"),
    [
        ("completion_extended", "P1", {"count": 1}, 30),
        ("completion_extended", "P1", {"count": 3}, 70),
        ("delay_vs_promised", "P1", {"months": 12}, 0),
        ("delay_vs_promised", "P1", {"months": 13}, 40),
        ("delay_vs_promised", "P1", {"months": 25}, 70),
        ("qpr_missed", "P1", {"count": 2}, 30),
        ("qpr_missed", "P1", {"count": 4}, 60),
        ("rera_penalty_order", "P1", {"count": 2}, 40),
        ("group_delay_share", "P2", {"count": 1, "total": 4}, 25),
        ("group_project_lapsed", "P2", {}, 40),
        ("group_company_insolvent", "P3", {}, 50),
        ("project_complaints", "P3", {"count": 3}, 30),
        ("project_complaints", "P3", {"count": 30}, 100),
        ("consumer_cases", "P3", {"count": 3}, 15),
        ("consumer_cases", "P3", {"count": 20}, 40),
        ("company_struck_off", "P4", {}, 40),
        ("director_disqualified", "P4", {}, 40),
        ("charge_created", "P4", {}, 20),
        ("mca_late_filing", "P4", {}, 20),
        ("sarfaesi_notice", "P4", {}, 60),
        ("land_dues", "P5", {}, 70),
        ("land_package_default", "P5", {}, 50),
        ("oc_cc_past_due", "P5", {}, 30),
        ("news_story", "P6", {"occurred_on": date(2026, 6, 1)}, 10),
    ],
)
def test_each_rule(kind: str, pillar: str, facts: dict[str, object], expected: int) -> None:
    assert penalty_of(kind, pillar, **facts) == expected


def test_news_is_capped_at_60_and_a_pillar_at_100() -> None:
    news = [finding("news_story", occurred_on=date(2026, 8, 1)) for _ in range(9)]
    rera = [finding("completion_extended", count=5), finding("qpr_missed", count=4)]

    result = score_v2([*news, *rera], ALL)

    penalties = {p.id: p.penalty for p in result.pillars}
    assert penalties["P6"] == 60
    assert penalties["P1"] == 100


def test_only_news_from_the_last_12_months_counts() -> None:
    old = finding("news_story", occurred_on=date(2025, 10, 24))  # 366 days before the read
    undated = finding("news_story")
    edge = finding("news_story", occurred_on=date(2025, 10, 25))  # exactly 365 days

    assert score_v2([old, undated], ALL).value == 900
    assert score_v2([edge], ALL).pillars[5].penalty == 10


def test_unknown_kinds_cost_nothing() -> None:
    assert score_v2([finding("court_order"), finding("completion_date")], ALL).value == 900


def test_formula_and_driver_points_add_up() -> None:
    result = score_v2([finding("completion_extended", count=2)], ALL)  # P1 penalty 50

    assert result.value == 900 - round(6 * 0.30 * 50)
    assert result.reason_codes[0].code == "R02"
    assert result.reason_codes[0].points == -90.0
    assert result.drivers[0].points == -90.0


def test_clip_keeps_the_scale() -> None:
    assert clip(1000) == 900
    assert clip(299) == 300
    assert clip(300) == 300
    assert clip(0) == 300


@pytest.mark.parametrize(
    ("value", "band"),
    [
        (300, "High"),
        (449, "High"),
        (450, "Elevated"),
        (599, "Elevated"),
        (600, "Watch"),
        (749, "Watch"),
        (750, "Low"),
        (900, "Low"),
    ],
)
def test_band_edges(value: int, band: str) -> None:
    assert band_for(value) == band


def test_the_score_never_falls_below_300() -> None:
    worst = [
        finding("registration_revoked"),
        finding("group_project_lapsed"),
        finding("sarfaesi_notice"),
        finding("land_dues"),
        finding("insolvency_scope", scope="company"),
    ]

    assert score_v2(worst, ALL).value >= 300


def test_revoked_registration_is_a_hard_stop_in_the_high_band() -> None:
    result = score_v2([finding("registration_revoked")], ALL)

    assert result.hard_stop
    assert result.band == "High"
    assert result.value <= 449
    assert result.hard_stop_reason == "UP-RERA registration lapsed or revoked"
    assert result.reason_codes[0].code == "R01"


def test_cirp_from_an_official_page_is_a_hard_stop() -> None:
    result = score_v2([finding("insolvency_scope", scope="company")], ALL)

    assert result.hard_stop
    assert result.band == "High"
    assert result.reason_codes[0].code == "R06"


def test_cirp_from_a_secondary_page_is_not_a_hard_stop() -> None:
    secondary = finding("insolvency_scope", scope="company", reliability="secondary")

    result = score_v2([secondary], ALL)

    assert not result.hard_stop
    assert result.pillars[2].penalty == 50


def test_a_hard_stop_is_banded_even_with_little_evidence() -> None:
    result = score_v2([finding("registration_revoked")], ["P1"])

    assert result.provisional is False
    assert result.band == "High"


def test_too_few_pillars_gives_no_band() -> None:
    result = score_v2([finding("completion_extended", count=1)], ["P1", "P3"])

    assert result.confidence == 0.33
    assert result.provisional
    assert result.band == "insufficient_evidence"
    assert result.band_label == "Not enough evidence yet"


def test_four_pillars_with_the_rera_record_are_enough_for_a_band() -> None:
    assert not score_v2([], ["P1", "P2", "P3", "P4"]).provisional


def test_three_of_six_pillars_have_no_band_however_clean() -> None:
    result = score_v2([], ["P1", "P2", "P3"])

    assert result.provisional and result.band == "insufficient_evidence"
    assert result.value == 900  # kept as the provisional value, never shown as a band


def test_without_the_rera_record_there_is_no_band_even_with_five_pillars() -> None:
    assert score_v2([], ["P2", "P3", "P4", "P5", "P6"]).band == "insufficient_evidence"


def test_a_hard_stop_shows_even_when_little_was_read() -> None:
    result = score_v2([finding("registration_revoked")], ["P1"])

    assert result.hard_stop and result.band == "High"


def test_an_overdue_project_costs_points_like_a_slipped_date() -> None:
    overdue = score_v2([finding("past_end_date", months=39)], ALL)
    slipped = score_v2([finding("delay_vs_promised", months=39)], ALL)

    assert overdue.value == slipped.value == 774
    assert [r.code for r in overdue.reason_codes] == ["R03"]


def test_when_both_delay_kinds_are_present_only_the_larger_counts() -> None:
    both = score_v2(
        [finding("past_end_date", months=39), finding("delay_vs_promised", months=14)], ALL
    )

    assert both.value == score_v2([finding("past_end_date", months=39)], ALL).value
    assert len(both.drivers) == 1


def test_promoter_complaints_cost_a_capped_amount_under_r13() -> None:
    few = score_v2([finding("promoter_complaints", count=10)], ALL)
    many = score_v2([finding("promoter_complaints", count=2803)], ALL)

    assert few.value == 900 - 12 and many.value == 900 - 48
    assert [c.label for c in many.reason_codes] == ["Builder complaint record"]
    assert many.reason_codes[0].code == "R13"
    assert next(p for p in many.pillars if p.id == "P2").penalty == 40


def test_9966_overdue_with_many_complaints_is_not_low() -> None:
    # UPRERAPRJ9966 as read on UP-RERA: 39 months overdue and 52 complaints about the project.
    result = score_v2(
        [finding("past_end_date", months=39), finding("project_complaints", count=52)], ALL
    )

    assert result.band != "Low"


def test_8334_is_elevated_or_worse() -> None:
    # UPRERAPRJ8334 as read on UP-RERA: 105 months overdue, 2803 complaints against the
    # promoter and 15 about the project.
    result = score_v2(
        [
            finding("past_end_date", months=105),
            finding("promoter_complaints", count=2803),
            finding("project_complaints", count=15),
        ],
        ALL,
    )

    assert result.band in ("Elevated", "High")


def test_unread_data_is_r12_with_no_penalty() -> None:
    clean = score_v2([], ["P1", "P2", "P3", "P4"])
    result = score_v2([], ["P1", "P2", "P3", "P4"], ["Consumer cases (e-Jagriti) (CAPTCHA)"])

    assert clean.value == result.value == 900
    r12 = result.reason_codes[-1]
    assert r12.code == "R12"
    assert r12.points == 0
    assert "e-Jagriti" in r12.label
    assert "Land authority" in r12.label


def test_reason_codes_are_ordered_by_points_lost() -> None:
    findings = [
        finding("news_story", occurred_on=date(2026, 8, 1)),
        finding("completion_extended", count=3),
    ]

    codes = [c.code for c in score_v2(findings, ALL).reason_codes]

    assert codes == ["R02", "R11"]


def test_pillars_read_from_checks_and_sources() -> None:
    assert pillars_read(["registration", "company_status"], ["news", "group"]) == [
        "P1",
        "P2",
        "P4",
        "P6",
    ]
    assert pillars_read([], []) == []


def test_uprera_complaints_read_the_promoter_and_legal_pillars() -> None:
    assert pillars_read(["rera_complaints"], []) == ["P2", "P3"]
    assert partly_read(["rera_complaints"], []) == {
        "P2": "UP-RERA complaints",
        "P3": "UP-RERA complaints",
    }


def test_a_pillar_with_its_own_source_read_is_not_partly_read() -> None:
    assert partly_read(["rera_complaints", "insolvency"], ["group"]) == {}


def test_five_records_read_give_a_band() -> None:
    # Registration, completion date, both complaint counts and the company status.
    checks = ["registration", "completion_date", "rera_complaints", "company_status"]
    read = pillars_read(checks, [])
    result = score_v2([], read, partly_read=partly_read(["rera_complaints"], []))

    assert read == ["P1", "P2", "P3", "P4"]
    assert result.band == "Low" and not result.provisional
    assert result.pillars_unread == ["P5", "P6"]
    partly = {p.id: p.partly_read for p in result.pillars if p.partly_read}
    assert partly == {"P2": "UP-RERA complaints", "P3": "UP-RERA complaints"}


def test_recorded_8334_check_has_a_v2_score(tmp_path: Path) -> None:
    report = check(tmp_path)["report"]

    v2 = report["score_v2"]
    assert report["score"]["value"] == 68  # v1 is untouched
    assert (v2["value"], v2["band"], v2["confidence"]) == (567, "Elevated", 0.83)
    assert v2["pillars_unread"] == ["P5"]
    assert [p["id"] for p in v2["pillars"]] == ALL
    codes = [c["code"] for c in v2["reason_codes"]]
    assert codes == ["R05", "R03", "R13", "R11", "R12"]
    assert v2["reason_codes"][0]["label"] == "15 RERA complaints"
    assert all(c["finding_ids"] or c["code"] == "R12" for c in v2["reason_codes"])
    finding_ids = {f["id"] for f in report["findings"]}
    assert {i for c in v2["reason_codes"] for i in c["finding_ids"]} <= finding_ids
