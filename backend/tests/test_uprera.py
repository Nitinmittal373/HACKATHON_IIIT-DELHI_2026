import asyncio
from datetime import UTC, date, datetime

import pytest

from app.models import Project
from app.parsers.uprera_page import ParseError, parse_uprera_page
from app.scoring.engine import score
from app.sources.base import ChecksRead, FoundFinding, ProjectDetails, SourceContext, SourceError
from app.sources.uprera import (
    DETAILS_SELECTORS,
    SUMMARY_SELECTORS,
    UpreraSource,
    findings_from_record,
    months_between,
    selectors_for,
)
from tests.fakes import FakeWebClient, load_page

URL_8334 = "https://www.up-rera.in/Frm_View_Project_Details.aspx?id=8334"
TODAY = date(2026, 10, 25)
NOW = datetime(2026, 10, 25, 9, 30, tzinfo=UTC)


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


def test_8334_has_a_completion_certificate_proforma() -> None:
    certificate = parse_uprera_page(load_page("uprera_8334.html")).completion_certificate
    assert certificate is not None
    assert certificate.file_name == "PRJ14-8334Completion certificate_EV1_Ph-1C.pdf"
    assert certificate.uploaded_on == date(2019, 4, 17)


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


def test_findings_and_score_for_8334_from_the_recorded_page() -> None:
    record = parse_uprera_page(load_page("uprera_8334.html"))
    findings = findings_from_record(record, URL_8334, TODAY, NOW)
    by_kind = {f.kind: f for f in findings}

    assert by_kind["registration"].title == "Registered on UP-RERA on 09 Aug 2017"
    assert by_kind["past_end_date"].months == 105
    assert by_kind["completion_certificate"].title == (
        "Promoter uploaded a completion certificate proforma. Verify possession status"
    )
    assert by_kind["completion_certificate"].verdict == "review"
    assert all(f.source_url == URL_8334 and f.read_on == TODAY for f in findings)

    result = score(findings, ["registration", "completion_date"])
    # The certificate on record means the delay is not counted; other sources are unread.
    assert result.value == 100
    assert result.confidence == 0.29
    assert "consumer_cases" in result.checks_unread


def test_findings_and_score_for_6742_count_the_delay() -> None:
    record = parse_uprera_page(load_page("uprera_6742.html"))
    findings = findings_from_record(record, "https://www.up-rera.in/x", TODAY, NOW)
    delay = next(f for f in findings if f.kind == "past_end_date")

    assert delay.months == 42
    assert delay.verdict == "red_flag"
    result = score(findings, ["registration", "completion_date"])
    assert result.value == 86
    assert [d.points for d in result.drivers] == [-14.0]


def test_a_project_not_yet_due_has_no_delay_or_certificate_finding() -> None:
    record = parse_uprera_page(load_page("uprera_summary_188811.html"))
    kinds = {f.kind for f in findings_from_record(record, "https://up-rera.in/x", TODAY, NOW)}
    assert kinds == {"registration", "completion_date", "rera_complaints"}


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


def test_source_yields_project_details_findings_and_checks_read() -> None:
    web = FakeWebClient(pages={URL_8334: load_page("uprera_8334.html")})
    events = run_source(web, Project(rera_id="UPRERAPRJ8334", details_url=URL_8334))

    details = next(e for e in events if isinstance(e, ProjectDetails))
    assert details.project.promoter == "SUPERTECH LIMITED"
    assert sum(isinstance(e, FoundFinding) for e in events) == 4
    assert events[-1] == ChecksRead(("registration", "completion_date"))


def test_source_refuses_a_page_for_another_project() -> None:
    url = "https://www.up-rera.in/Frm_View_Project_Details.aspx?id=6742"
    web = FakeWebClient(pages={url: load_page("uprera_8334.html")})
    with pytest.raises(SourceError, match="shows UPRERAPRJ8334"):
        run_source(web, Project(rera_id="UPRERAPRJ6742", details_url=url))
