"""SARFAESI notices: an official lender page is scored, a news report is only for review."""

import asyncio
from datetime import UTC, datetime

import pytest

from app.models import Finding, Project
from app.sources.base import FoundFinding, SourceContext, SourceError
from app.sources.sarfaesi import SarfaesiSource, is_official, notice_findings
from app.tinyfish import SearchHit, WebError
from tests.fakes import FakeWebClient, load_recording

RECORDING = load_recording("sarfaesi_8334.json")
NOW = datetime(2026, 10, 26, 4, 0, tzinfo=UTC)
PROJECT = Project(
    rera_id="UPRERAPRJ8334", promoter="SUPERTECH LIMITED", details_url="https://up-rera.in/x"
)


def ctx(web: FakeWebClient, project: Project = PROJECT) -> SourceContext:
    return SourceContext(project=project, web=web, today=NOW.date(), now=NOW)


def run(web: FakeWebClient) -> list[Finding]:
    async def collect() -> list[Finding]:
        events = SarfaesiSource().run(ctx(web))
        return [e.finding async for e in events if isinstance(e, FoundFinding)]

    return asyncio.run(collect())


def hit(url: str, title: str, snippet: str) -> SearchHit:
    return SearchHit(title=title, url=url, snippet=snippet, date="2026-09-01")


def test_the_recorded_search_finds_no_notice_and_adds_nothing() -> None:
    assert run(FakeWebClient().replay(RECORDING)) == []


def test_an_official_notice_naming_the_company_is_scored() -> None:
    hits = [hit("https://ibapi.in/sale/1", "E-auction notice", "SARFAESI sale: Supertech Limited")]

    (found,) = notice_findings(hits, "Supertech Limited", ctx(FakeWebClient()))

    assert (found.kind, found.reliability, found.verdict) == ("sarfaesi_notice", "primary", "fail")
    assert found.source_url == "https://ibapi.in/sale/1"


def test_a_news_report_is_for_review_and_costs_nothing() -> None:
    hits = [hit("https://example.com/news", "Bank auctions assets", "SARFAESI: Supertech Limited")]

    (found,) = notice_findings(hits, "Supertech Limited", ctx(FakeWebClient()))

    assert (found.kind, found.reliability, found.verdict) == (
        "sarfaesi_report",
        "secondary",
        "review",
    )


def test_another_company_with_a_similar_name_is_ignored() -> None:
    hits = [
        hit(
            "https://ibapi.in/sale/2",
            "Auction",
            "SARFAESI sale: Supertech Realtors Private Limited",
        )
    ]

    assert notice_findings(hits, "Supertech Limited", ctx(FakeWebClient())) == []


def test_a_page_without_auction_words_is_ignored() -> None:
    hits = [hit("https://ibapi.in/x", "About Supertech Limited", "Supertech Limited builds homes")]

    assert notice_findings(hits, "Supertech Limited", ctx(FakeWebClient())) == []


def test_official_hosts() -> None:
    assert is_official("https://www.ibapi.in/x")
    assert is_official("https://drt.gov.in/x")
    assert not is_official("https://timesofindia.com/x")


def test_no_promoter_leaves_the_source_unread() -> None:
    with pytest.raises(SourceError, match="not known"):
        run_without = ctx(FakeWebClient(), PROJECT.model_copy(update={"promoter": None}))
        asyncio.run(_drain(run_without))


def test_a_search_failure_leaves_the_source_unread() -> None:
    web = FakeWebClient(search_error=WebError("Search failed: TinyFish did not answer in time"))

    with pytest.raises(SourceError, match="did not answer"):
        asyncio.run(_drain(ctx(web)))


async def _drain(context: SourceContext) -> None:
    async for _ in SarfaesiSource().run(context):
        pass
