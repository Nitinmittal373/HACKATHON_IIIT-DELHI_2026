import asyncio
from dataclasses import replace
from datetime import UTC, date, datetime

import pytest

from app.models import Project
from app.parsers.uprera_page import ParseError, is_certificate, parse_uprera_page
from app.scoring.engine import score
from app.sources.base import (
    ChecksRead,
    FoundFinding,
    Progress,
    ProjectDetails,
    SourceContext,
    SourceError,
)
from app.sources.uprera import (
    DETAILS_SELECTORS,
    SUMMARY_SELECTORS,
    UpreraSource,
    complaint_findings,
    extension_findings,
    findings_from_record,
    months_between,
    selectors_for,
)
from tests.conftest import make_web, summary_url_8334
from tests.fakes import FakeWebClient, load_page

URL_8334 = "https://www.up-rera.in/Frm_View_Project_Details.aspx?id=8334"
TODAY = date(2026, 10, 25)
NOW = datetime(2026, 10, 25, 9, 30, tzinfo=UTC)
SUMMARY_8334 = summary_url_8334()


def test_details_page_8334() -> None:
    record = parse_uprera_page(load_page("uprera_8334.html"))

    assert record.rera_id == "UPRERAPRJ8334"
    assert record.name == "SUPERTECH ECO VILLAGE-I PHASE I-C"
    assert record.promoter == "SUPERTECH LIMITED"
    assert record.promoter_id == "UPRERAPRM1754"
    assert record.registered_on == date(2017, 8, 9)
    assert record.project_type == "Ongoing"
    assert record.district == "Gautam Buddha Nagar"
    assert record.start_date == date(2012, 12, 30)
    assert record.end_date == date(2017, 12, 30)
    assert record.permits[0].number == "PLG/(BP)2311/5397"
    assert record.permits[0].valid_upto == date(2021, 7, 28)
    assert len(record.documents) == 15
    assert record.latest_end_date == date(2017, 12, 30)


def test_a_completion_certificate_proforma_is_not_a_certificate() -> None:
    record = parse_uprera_page(load_page("uprera_8334.html"))
    proforma = next(d for d in record.documents if "Completion" in d.name)
    assert proforma.name == "Proforma of Completion Certificate(Occupancy)"
    assert proforma.uploaded
    assert record.completion_certificate is None


@pytest.mark.parametrize(
    ("name", "counts"),
    [
        ("Completion Certificate", True),
        ("Occupancy Certificate", True),
        ("Proforma of Completion Certificate(Occupancy)", False),
        ("Commencement Certificate", False),
    ],
)
def test_is_certificate(name: str, counts: bool) -> None:
    assert is_certificate(name) is counts


def test_details_page_6742_takes_the_latest_end_date() -> None:
    record = parse_uprera_page(load_page("uprera_6742.html"))
    assert record.rera_id == "UPRERAPRJ6742"
    assert record.promoter == "Gaursons Promoters Private Limited"
    # The basic details say 26 Mar 2023; the permit table says 27 Sep 2022.
    assert record.latest_end_date == date(2023, 3, 26)
    assert record.completion_certificate is None


def test_summary_page_for_a_new_format_number() -> None:
    record = parse_uprera_page(load_page("uprera_summary_188811.html"))
    assert record.rera_id == "UPRERAPRJ188811/08/2024"
    assert record.name == "GAUR NYC RESIDENCES"
    assert record.promoter == "GAURSONS HI-TECH INFRASTRUCTURE PRIVATE LIMITED"
    assert record.district == "Ghaziabad"
    assert record.registered_on == date(2024, 8, 26)
    assert record.end_date == date(2029, 8, 6)
    assert record.project_complaints == 2
    assert record.promoter_complaints == 648


def test_unexpected_page_is_a_parse_error() -> None:
    with pytest.raises(ParseError):
        parse_uprera_page("<html><body>Service unavailable</body></html>")


def test_findings_and_score_for_8334_from_the_recorded_pages() -> None:
    record = parse_uprera_page(load_page("uprera_8334.html"))
    summary = parse_uprera_page(load_page("uprera_summary_8334.html"))
    findings = findings_from_record(record, URL_8334, TODAY, NOW)
    findings += complaint_findings(summary, SUMMARY_8334, TODAY, NOW)
    by_kind = {f.kind: f for f in findings}

    assert set(by_kind) == {
        "registration",
        "past_end_date",
        "promoter_complaints",
        "project_complaints",
    }
    delay = by_kind["past_end_date"]
    assert delay.title == (
        "Completion date on record (30 Dec 2017) passed 105 months ago; "
        "project still listed as Ongoing"
    )
    assert (delay.verdict, delay.reliability, delay.months) == ("fail", "primary", 105)
    assert by_kind["promoter_complaints"].count == 2803
    assert by_kind["project_complaints"].count == 15
    assert by_kind["project_complaints"].source_url == SUMMARY_8334
    assert by_kind["registration"].source_url == URL_8334

    result = score(findings, ["registration", "completion_date"])
    # -14 delay, -9 builder history (2,803 >= 500), -6 legal (15 >= 10).
    assert [d.points for d in result.drivers] == [-14.0, -9.0, -6.0]
    assert result.value == 71
    assert result.confidence == 0.29
    assert result.band == "insufficient_evidence"
    assert result.provisional


def test_findings_and_score_for_6742_count_the_delay() -> None:
    record = parse_uprera_page(load_page("uprera_6742.html"))
    findings = findings_from_record(record, "https://www.up-rera.in/x", TODAY, NOW)
    delay = next(f for f in findings if f.kind == "past_end_date")

    assert delay.months == 42
    assert delay.verdict == "fail"
    result = score(findings, ["registration", "completion_date"])
    assert result.value == 86
    assert [d.points for d in result.drivers] == [-14.0]


def test_a_project_not_yet_due_shows_its_date_and_no_delay() -> None:
    record = parse_uprera_page(load_page("uprera_summary_188811.html"))
    findings = findings_from_record(record, "https://up-rera.in/x", TODAY, NOW)
    assert {f.kind for f in findings} == {"registration", "completion_date"}


def test_complaints_on_a_new_format_summary_page() -> None:
    record = parse_uprera_page(load_page("uprera_summary_188811.html"))
    findings = complaint_findings(record, "https://up-rera.in/x", TODAY, NOW)
    assert [(f.kind, f.count, f.area) for f in findings] == [
        ("promoter_complaints", 648, "builder_history"),
        ("project_complaints", 2, "legal"),
    ]


@pytest.mark.parametrize(
    ("start", "end", "months"),
    [
        (date(2017, 12, 30), date(2026, 10, 25), 105),
        (date(2023, 3, 26), date(2023, 4, 26), 1),
        (date(2023, 3, 26), date(2023, 4, 25), 0),
        (date(2029, 8, 6), date(2026, 10, 25), -34),
    ],
)
def test_months_between(start: date, end: date, months: int) -> None:
    assert months_between(start, end) == months


def test_selectors_follow_the_page_layout() -> None:
    assert selectors_for(URL_8334) == DETAILS_SELECTORS
    assert selectors_for("https://up-rera.in/Projectsummary?a=1") == SUMMARY_SELECTORS


def run_source(web: FakeWebClient, project: Project) -> list[object]:
    async def collect() -> list[object]:
        ctx = SourceContext(project=project, web=web, today=TODAY, now=NOW)
        return [event async for event in UpreraSource().run(ctx)]

    return asyncio.run(collect())


def test_source_reads_the_details_and_summary_pages() -> None:
    events = run_source(make_web(), Project(rera_id="UPRERAPRJ8334", details_url=URL_8334))

    details = next(e for e in events if isinstance(e, ProjectDetails))
    assert details.project.promoter == "SUPERTECH LIMITED"
    kinds = [e.finding.kind for e in events if isinstance(e, FoundFinding)]
    assert kinds == ["registration", "past_end_date", "promoter_complaints", "project_complaints"]
    assert events[-1] == ChecksRead(("registration", "completion_date", "extensions"))


def test_source_carries_on_when_the_summary_page_is_not_found() -> None:
    web = FakeWebClient(pages={URL_8334: load_page("uprera_8334.html")})
    events = run_source(web, Project(rera_id="UPRERAPRJ8334", details_url=URL_8334))

    kinds = [e.finding.kind for e in events if isinstance(e, FoundFinding)]
    assert kinds == ["registration", "past_end_date"]
    assert any(isinstance(e, Progress) and "complaints were not read" in e.text for e in events)
    assert events[-1] == ChecksRead(("registration", "completion_date"))


def test_source_refuses_a_page_for_another_project() -> None:
    url = "https://www.up-rera.in/Frm_View_Project_Details.aspx?id=6742"
    web = FakeWebClient(pages={url: load_page("uprera_8334.html")})
    with pytest.raises(SourceError, match="shows UPRERAPRJ8334"):
        run_source(web, Project(rera_id="UPRERAPRJ6742", details_url=url))


def test_a_new_project_past_its_date_counts_the_delay() -> None:
    record = parse_uprera_page(load_page("uprera_summary_188811.html"))
    assert record.project_type == "New"
    late = replace(record, end_date=date(2023, 4, 26))

    delay = next(
        f
        for f in findings_from_record(late, "https://up-rera.in/x", TODAY, NOW)
        if f.kind == "past_end_date"
    )

    assert delay.months == 41
    assert delay.verdict == "fail"
    assert delay.title.endswith("project still listed as New")
    assert score([delay], ["registration", "completion_date"]).drivers[0].points == -14.0


def test_a_completed_project_past_its_date_has_no_delay() -> None:
    record = parse_uprera_page(load_page("uprera_summary_188811.html"))
    done = replace(record, end_date=date(2023, 4, 26), project_type="Completed")
    kinds = {f.kind for f in findings_from_record(done, "https://up-rera.in/x", TODAY, NOW)}
    assert kinds == {"registration", "completion_date"}


@pytest.mark.parametrize(
    ("project_type", "uploaded_on", "completed"),
    [
        ("Ongoing", None, False),
        ("New", None, False),
        (None, None, False),
        ("Completed", None, True),
        # UP-RERA keeps "Ongoing" after completion; the certificate block is the signal.
        ("Ongoing", date(2023, 7, 26), True),
    ],
)
def test_is_completed(project_type: str | None, uploaded_on: date | None, completed: bool) -> None:
    record = replace(
        parse_uprera_page(load_page("uprera_summary_8334.html")),
        project_type=project_type,
        completion_uploaded_on=uploaded_on,
    )
    assert record.is_completed is completed


def test_a_completed_project_from_the_register_has_its_certificate_date() -> None:
    record = parse_uprera_page(load_page("uprera_summary_2634.html"))

    assert record.rera_id == "UPRERAPRJ2634"
    assert record.project_type == "Ongoing"
    assert record.completion_uploaded_on == date(2023, 7, 26)
    assert record.is_completed
    kinds = [f.kind for f in findings_from_record(record, "https://up-rera.in/x", TODAY, NOW)]
    assert "past_end_date" not in kinds
    assert "completion_certificate" in kinds


def test_extensions_are_read_and_covid_ones_are_set_apart() -> None:
    record = parse_uprera_page(load_page("uprera_summary_2634.html"))

    assert [(e.extended_from, e.extended_to, e.is_covid) for e in record.extensions] == [
        (date(2019, 12, 31), date(2020, 12, 30), False),
        (date(2020, 12, 30), date(2021, 6, 29), True),
    ]
    # Delay is measured from the latest approved date, so the COVID extension counts there.
    assert record.latest_end_date == date(2021, 6, 29)


def test_one_extension_costs_the_first_step_and_covid_is_not_counted() -> None:
    record = parse_uprera_page(load_page("uprera_summary_2634.html"))

    [finding] = extension_findings(record, "https://up-rera.in/x", TODAY, NOW)

    assert finding.kind == "completion_extended"
    assert finding.count == 1
    assert finding.title == "Completion date extended once by UP-RERA, most recently to 30 Dec 2020"
    assert score([finding], ["extensions"]).drivers[0].points == -6.0


def test_a_project_with_no_extension_table_has_no_extension_finding() -> None:
    record = parse_uprera_page(load_page("uprera_summary_8334.html"))
    assert extension_findings(record, "https://up-rera.in/x", TODAY, NOW) == []
