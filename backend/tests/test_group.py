"""The group-companies source, replayed from what the real sites answered (group_8334.json)."""

import asyncio
from datetime import date, datetime
from pathlib import Path

import pytest

from app.models import Finding, Project
from app.sources.base import FoundFinding, SourceContext, SourceError
from app.sources.group import GroupSource, is_delayed, status_findings
from app.sources.mca import is_this_company, parse_profile
from app.sources.registry import parse_company_table
from tests.fakes import FakeWebClient, load_recording

RECORDING = load_recording("group_8334.json")
CAPTURED = datetime.fromisoformat(RECORDING["captured_at"])
PROJECT = Project.model_validate(RECORDING["project"])
TOFLER = next(u for u in RECORDING["texts"] if "tofler.in/supertech-limited" in u)


def run(project: Project = PROJECT, web: FakeWebClient | None = None) -> list[Finding]:
    web = web or FakeWebClient().replay(RECORDING)
    ctx = SourceContext(project=project, web=web, today=CAPTURED.date(), now=CAPTURED)

    async def collect() -> list[Finding]:
        return [e.finding async for e in GroupSource().run(ctx) if isinstance(e, FoundFinding)]

    return asyncio.run(collect())


def test_the_profile_lists_directors_by_name_and_din_only() -> None:
    profile = parse_profile(RECORDING["texts"][TOFLER])

    assert profile.legal_name == "SUPERTECH LIMITED"
    assert len(profile.directors) == 6
    assert all(len(d.din) == 8 and d.din.isdigit() for d in profile.directors)
    assert "Ram Kishor Arora" in {d.name for d in profile.directors}  # "Shareholder" removed
    assert len(profile.related_companies) == 8
    assert "SUPERTECH REALTORS PRIVATE LIMITED" in profile.related_companies


def test_a_profile_of_another_company_is_not_accepted() -> None:
    profile = parse_profile(RECORDING["texts"][TOFLER])

    assert is_this_company(profile, "Supertech Limited")
    assert not is_this_company(profile, "Supertech Realtors Private Limited")


def test_group_findings_each_carry_a_source_and_a_read_time() -> None:
    findings = run()

    kinds = {f.kind for f in findings}
    assert {"directors", "group_delay_share"} <= kinds
    assert all(f.source_url.startswith("https://") and f.read_at == CAPTURED for f in findings)
    assert all(f.source == "group" for f in findings)


def test_the_directors_finding_holds_names_and_dins_and_nothing_else() -> None:
    (directors,) = [f for f in run() if f.kind == "directors"]

    assert directors.snippet and "DIN" in directors.snippet
    assert "@" not in directors.snippet and "Hamkund" not in directors.snippet


def test_the_delay_share_counts_the_projects_that_were_read() -> None:
    (share,) = [f for f in run() if f.kind == "group_delay_share"]

    delayed = [f for f in run() if f.kind == "group_project_delayed"]
    assert share.count == len(delayed)
    assert share.total is not None and share.count <= share.total <= 20


def test_a_promoter_with_no_profile_leaves_the_source_unread() -> None:
    with pytest.raises(SourceError, match="exact name"):
        run(web=FakeWebClient())


def test_no_promoter_name_leaves_the_source_unread() -> None:
    with pytest.raises(SourceError, match="not known"):
        run(PROJECT.model_copy(update={"promoter": None}))


def test_insolvent_and_struck_off_related_companies_are_findings() -> None:
    ctx = SourceContext(
        project=PROJECT, web=FakeWebClient(), today=date(2026, 10, 26), now=CAPTURED
    )
    entries = [
        ("A LIMITED", "Under CIRP", "https://economictimes.indiatimes.com/a"),
        ("B LIMITED", "Strike Off", "https://economictimes.indiatimes.com/b"),
        ("C LIMITED", "Active", "https://economictimes.indiatimes.com/c"),
        None,
    ]

    kinds = [f.kind for f in status_findings(entries, ctx)]

    assert kinds == ["group_company_insolvent", "director_struck_off"]


def test_a_completed_project_is_never_delayed() -> None:
    from dataclasses import replace

    from app.parsers.uprera_page import parse_uprera_page
    from tests.fakes import load_page

    record = parse_uprera_page(load_page("uprera_summary_2634.html"))

    assert record.is_completed
    assert not is_delayed(record, date(2026, 10, 26))
    assert not is_delayed(
        replace(record, end_date=None, revised_end_date=None, permits=(), extensions=()),
        date(2026, 10, 26),
    )


def test_the_company_table_parser_still_reads_the_registry_page() -> None:
    text = next(t for u, t in RECORDING["texts"].items() if "economictimes" in u)

    assert parse_company_table(text)["status"]


def test_with_v2_sources_the_group_pillar_is_scored(tmp_path: Path) -> None:
    from fastapi.testclient import TestClient

    from app.main import create_app
    from tests.conftest import make_settings, make_web, read_events
    from tests.test_recorded_check import CAPTURED_AT
    from tests.test_recorded_check import RECORDING as CHECK

    web = make_web().replay(CHECK).replay(RECORDING)
    app = create_app(
        make_settings(tmp_path, v2_sources=True), web=web, clock=lambda: CAPTURED_AT, cache_dir=None
    )
    with TestClient(app) as client:
        check_id = client.post("/api/checks", json={"rera_id": "UPRERAPRJ8334"}).json()["id"]
        read_events(client, check_id)
        report = client.get(f"/api/checks/{check_id}/report").json()

    v2 = report["score_v2"]
    assert "P2" not in v2["pillars_unread"]
    assert "R13" in [c["code"] for c in v2["reason_codes"]]
    assert report["score"]["value"] == 68  # the classic score does not read group findings
