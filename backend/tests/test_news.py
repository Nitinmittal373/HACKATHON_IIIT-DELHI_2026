from datetime import date

from app.scoring.engine import score
from app.sources.base import FoundFinding
from app.sources.news import NewsSource, news_query, published_on, story_findings
from app.tinyfish import SearchHit
from tests.fakes import FakeWebClient
from tests.sourcekit import ECO_VILLAGE_1, TODAY, context, run_source

SC_ORDER = (
    "https://api.sci.gov.in/supremecourt/2025/5007/5007_2025_1_18_68404_Order_05-Feb-2026.pdf"
)
ORDER_TEXT = """The corporate debtor, M/s. Supertech Limited, was to complete 16 projects:
(xiv) Eco Village-1, Greater Noida.
(ix) Eco Village-2, Greater Noida."""


def story(title: str, date_text: str | None = "4 weeks ago", snippet: str = "") -> SearchHit:
    return SearchHit(
        title=title, url=f"https://news.example/{abs(hash(title))}", snippet=snippet, date=date_text
    )


def test_the_search_uses_the_brand_and_project_words_without_the_phase() -> None:
    assert news_query(ECO_VILLAGE_1) == "supertech eco village delay OR NCLT OR NBCC"


def test_only_stories_about_delays_that_name_the_project_or_promoter_count() -> None:
    hits = [
        story("NBCC to resume work on 16 stalled Supertech projects in Jan"),
        story("Supertech Eco Village-I homebuyers still wait for possession"),
        story("Supertech launches a new offer for Diwali"),
        story("Gaursons delays handover in Greater Noida West"),
    ]
    findings = story_findings(hits, ECO_VILLAGE_1, context())

    assert [f.title.split(": ")[0] for f in findings] == [
        "News on delays, about the promoter",
        "News on delays, about this project",
    ]
    assert all(f.reliability == "secondary" and f.verdict == "review" for f in findings)


def test_one_story_carried_by_two_outlets_counts_once() -> None:
    hits = [
        story("Supertech delays: NBCC takes over - Times of India"),
        story("Supertech delays: NBCC takes over | Hindustan Times"),
    ]
    assert len(story_findings(hits, ECO_VILLAGE_1, context())) == 1


def test_at_most_three_stories_are_kept_and_each_costs_a_little() -> None:
    hits = [story(f"Supertech delay story number {n} on possession") for n in range(5)]
    findings = story_findings(hits, ECO_VILLAGE_1, context())

    assert len(findings) == 3
    result = score(findings, [])
    assert [d.points for d in result.drivers] == [-1.0, -1.0, -1.0]


def test_a_relative_date_is_stated_as_approximate() -> None:
    assert published_on("4 weeks ago", TODAY) == (
        date(2026, 9, 27),
        " (published about 4 weeks ago)",
    )
    assert published_on("Sep 2, 2026", TODAY) == (date(2026, 9, 2), "")
    assert published_on(None, TODAY) == (None, "")


def test_a_supreme_court_order_that_names_the_project_is_context_with_no_points() -> None:
    web = FakeWebClient(
        searches={
            "Supreme Court NBCC SUPERTECH LIMITED stalled projects order": [
                SearchHit(title="O R D E R", url=SC_ORDER, snippet="", date="Feb 5, 2026")
            ]
        },
        texts={SC_ORDER: ORDER_TEXT},
    )
    events = run_source(NewsSource(), context(web=web))

    [order] = [
        e.finding for e in events if isinstance(e, FoundFinding) and e.finding.kind == "court_order"
    ]
    assert order.verdict == "context"
    assert order.reliability == "primary"
    assert order.occurred_on == date(2026, 2, 5)
    assert score([order], []).value == 100


def test_an_order_that_names_only_another_phase_is_not_used() -> None:
    web = FakeWebClient(
        searches={
            "Supreme Court NBCC SUPERTECH LIMITED stalled projects order": [
                SearchHit(title="O R D E R", url=SC_ORDER, snippet="")
            ]
        },
        texts={SC_ORDER: "M/s. Supertech Limited. (ix) Eco Village-2, Greater Noida."},
    )
    events = run_source(NewsSource(), context(web=web))
    assert not any(isinstance(e, FoundFinding) for e in events)
