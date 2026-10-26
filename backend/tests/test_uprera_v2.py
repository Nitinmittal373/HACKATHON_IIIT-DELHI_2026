"""UP-RERA signals NeevScore v2 reads: delay against the promised date and a lapsed status."""

from dataclasses import replace
from datetime import UTC, date, datetime

from app.parsers.uprera_page import UpreraRecord, parse_uprera_page
from app.sources.uprera import delay_vs_promised_findings, registration_status_findings
from tests.fakes import load_page

NOW = datetime(2026, 10, 25, 4, 0, tzinfo=UTC)
TODAY = date(2026, 10, 25)
URL = "https://www.up-rera.in/Frm_View_Project_Details.aspx?id=8334"


def record(**changes: object) -> UpreraRecord:
    return replace(parse_uprera_page(load_page("uprera_8334.html")), **changes)


def test_delay_vs_promised_compares_the_first_and_latest_dates() -> None:
    changed = record(end_date=date(2020, 1, 15), revised_end_date=date(2022, 3, 20))

    (found,) = delay_vs_promised_findings([changed], URL, TODAY, NOW)

    assert (found.kind, found.months, found.verdict) == ("delay_vs_promised", 26, "fail")
    assert "15 Jan 2020" in found.title and "20 Mar 2022" in found.title
    assert found.snippet
    assert found.source_url == URL


def test_the_latest_date_is_taken_across_both_pages() -> None:
    details = record(end_date=date(2020, 1, 1), revised_end_date=None, permits=())
    summary = record(end_date=None, revised_end_date=date(2021, 1, 1), permits=())

    (found,) = delay_vs_promised_findings([details, summary], URL, TODAY, NOW)

    assert (found.months, found.verdict) == (12, "review")


def test_no_delay_finding_when_the_date_never_moved() -> None:
    steady = record(end_date=date(2030, 1, 1), revised_end_date=None, permits=())

    assert delay_vs_promised_findings([steady], URL, TODAY, NOW) == []


def test_a_lapsed_status_on_the_page_is_a_registration_finding() -> None:
    (found,) = registration_status_findings(record(project_type="Lapsed"), URL, TODAY, NOW)

    assert found.kind == "registration_revoked"
    assert "Lapsed" in found.title


def test_an_ongoing_project_has_no_registration_finding() -> None:
    assert registration_status_findings(record(), URL, TODAY, NOW) == []
