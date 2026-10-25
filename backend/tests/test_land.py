from app.models import Project
from app.scoring.engine import score
from app.sources.base import ChecksRead, FoundFinding, Progress
from app.sources.land import LandSource, promoter_listed
from app.tinyfish import SearchHit
from tests.fakes import FakeWebClient
from tests.sourcekit import ECO_VILLAGE_1, context, run_source

GNIDA_LIST = "https://www.greaternoidaauthority.in/files/attachments/dues-defaulter-list.pdf"
NOIDA_LIST = "https://www.noidaauthorityonline.in/site/writereaddata/defaulter-dues.pdf"
YEIDA_LIST = "https://www.yamunaexpresswayauthority.com/Upload/PressNewsFiles/dues-list"

LIST_WITH_PROMOTER = """Group housing dues as on 31 March 2026
1 Gaursons India Limited 120,45,00,000
2 M/s Supertech Ltd. 355,12,00,000
"""
LIST_WITHOUT_PROMOTER = """Group housing dues as on 31 March 2026
1 Gaursons India Limited 120,45,00,000
2 Supertech Realtors Limited 12,00,000
"""
QUERIES = {
    "Noida Authority": NOIDA_LIST,
    "Greater Noida Industrial Development Authority": GNIDA_LIST,
    "Yamuna Expressway Industrial Development Authority": YEIDA_LIST,
}


def web_with(lists: dict[str, str]) -> FakeWebClient:
    """Each authority's search finds its dues list; it is readable only if given in `lists`."""
    searches = {
        f"{name} builders dues defaulter list group housing": [
            SearchHit(title="Builders defaulter list", url=url, snippet="Dues of group housing")
        ]
        for name, url in QUERIES.items()
    }
    return FakeWebClient(searches=searches, texts=lists)


def test_a_line_with_the_exact_name_and_an_amount_counts() -> None:
    assert promoter_listed("SUPERTECH LIMITED", LIST_WITH_PROMOTER)


def test_a_similar_name_does_not_count() -> None:
    assert not promoter_listed("SUPERTECH LIMITED", LIST_WITHOUT_PROMOTER)


def test_a_name_without_an_amount_is_not_a_dues_entry() -> None:
    assert not promoter_listed("SUPERTECH LIMITED", "Allotment to Supertech Limited, Sector 1")


def test_a_listed_promoter_costs_fifty_in_the_financial_area() -> None:
    web = web_with({NOIDA_LIST: LIST_WITH_PROMOTER})
    events = run_source(LandSource(), context(web=web))

    [finding] = [e.finding for e in events if isinstance(e, FoundFinding)]
    assert finding.kind == "land_dues"
    assert finding.source_url == NOIDA_LIST
    assert finding.reliability == "primary"
    result = score([finding], ["land_dues"])
    assert [d.points for d in result.drivers] == [-7.5]
    assert events[-1] == ChecksRead(("land_dues",))


def test_not_found_in_every_list_is_read_but_adds_no_points() -> None:
    texts = {url: LIST_WITHOUT_PROMOTER for url in QUERIES.values()}
    events = run_source(LandSource(), context(web=web_with(texts)))

    findings = [e.finding for e in events if isinstance(e, FoundFinding)]
    assert [f.verdict for f in findings] == ["not_found"] * 3
    assert score(findings, ["land_dues"]).value == 100
    assert events[-1] == ChecksRead(("land_dues",))


def test_one_unreadable_list_leaves_the_check_unread() -> None:
    texts = {NOIDA_LIST: LIST_WITHOUT_PROMOTER, GNIDA_LIST: LIST_WITHOUT_PROMOTER}
    events = run_source(LandSource(), context(web=web_with(texts)))

    assert not any(isinstance(e, ChecksRead) for e in events)
    assert any(isinstance(e, Progress) and "could not be read" in e.text for e in events)


def test_nothing_readable_gives_no_findings_at_all() -> None:
    events = run_source(LandSource(), context(web=web_with({})))
    assert not any(isinstance(e, FoundFinding | ChecksRead) for e in events)


def test_a_district_without_a_connected_list_is_left_unread() -> None:
    elsewhere = Project(
        rera_id="UPRERAPRJ1",
        name="X",
        promoter=ECO_VILLAGE_1.promoter,
        district="Lucknow",
        details_url="https://up-rera.in/x",
    )
    events = run_source(LandSource(), context(elsewhere, web_with({})))
    assert [type(e) for e in events] == [Progress]
