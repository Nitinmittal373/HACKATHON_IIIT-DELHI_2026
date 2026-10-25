from app.scoring.engine import score
from app.sources.base import ChecksRead, FoundFinding, Progress
from app.sources.registry import (
    RegistrySource,
    is_this_company,
    parse_company_table,
    pick_company_page,
    readable_pages,
    to_findings,
)
from app.tinyfish import AgentDone, SearchHit
from tests.fakes import FakeWebClient
from tests.sourcekit import ECO_VILLAGE_1, context, run_source

PROMOTER = "SUPERTECH LIMITED"
ZAUBA = "https://www.zaubacorp.com/SUPERTECH-LIMITED-U74899DL1995PLC074422"
ECONOMIC_TIMES = (
    "https://economictimes.indiatimes.com/company/supertech-limited/U74899DL1995PLC074422"
)
DETAILS_TABLE = """
## Supertech Limited Details

| | |
| --- | --- |
| | CIN | U74899DL1995PLC074422 | |
| | Date of Incorporation | 07 Dec, 1995 | |
| | Status | Active | |
"""


def hit(url: str, title: str, snippet: str = "") -> SearchHit:
    return SearchHit(title=title, url=url, snippet=snippet)


def test_the_exact_legal_name_is_needed_not_the_brand() -> None:
    hits = [
        hit(
            "https://www.zaubacorp.com/SUPERTECH-REALTORS-LIMITED-U1",
            "SUPERTECH REALTORS LIMITED",
        ),
        hit("https://www.zaubacorp.com/SUPERTECH-EV-LIMITED-L1", "SUPERTECH EV LIMITED"),
    ]
    assert pick_company_page(hits, PROMOTER) is None


def test_a_page_that_shows_no_captcha_is_preferred_to_zaubacorp() -> None:
    hits = [hit(ZAUBA, "supertech limited"), hit(ECONOMIC_TIMES, "Supertech Limited Information")]
    page = pick_company_page(hits, PROMOTER)
    assert page is not None and page.url == ECONOMIC_TIMES


def test_pages_outside_the_registry_hosts_are_ignored() -> None:
    hits = [
        hit("https://tracxn.com/d/legal-entities/india/supertech-limited/x", "SUPERTECH LIMITED")
    ]
    assert pick_company_page(hits, PROMOTER) is None


def test_the_details_table_gives_name_cin_and_status() -> None:
    assert parse_company_table(DETAILS_TABLE) == {
        "legal_name": "Supertech Limited",
        "cin": "U74899DL1995PLC074422",
        "status": "Active",
    }
    assert parse_company_table("Opening The Company Check…")["status"] is None


def test_an_active_company_is_ok_and_costs_nothing() -> None:
    result = parse_company_table(DETAILS_TABLE)
    [finding] = to_findings(result, PROMOTER, ECONOMIC_TIMES, context())

    assert finding.kind == "company_status"
    assert finding.verdict == "ok"
    assert finding.reliability == "secondary"
    assert finding.title == "Company status: Active (CIN U74899DL1995PLC074422)"
    assert score([finding], ["company_status"]).value == 100


def test_a_company_under_cirp_is_a_hard_stop() -> None:
    result = {"legal_name": "SUPERTECH LIMITED", "cin": "U1", "status": "Under CIRP"}
    [finding] = to_findings(result, PROMOTER, ECONOMIC_TIMES, context())

    assert (finding.kind, finding.scope, finding.verdict) == (
        "insolvency_scope",
        "company",
        "red_flag",
    )
    scored = score([finding], ["company_status"])
    assert scored.hard_stop
    assert scored.value <= 39


def test_another_company_with_a_similar_name_is_never_used() -> None:
    result = {"legal_name": "SUPERTECH REALTORS LIMITED", "cin": "U2", "status": "Under CIRP"}
    assert not is_this_company(result, PROMOTER)
    assert to_findings(result, PROMOTER, ECONOMIC_TIMES, context()) == []
    assert RegistrySource().checks_read(result, context()) == ()


def test_a_page_without_a_status_leaves_the_check_unread() -> None:
    result = {"legal_name": "SUPERTECH LIMITED", "cin": None, "status": None}
    assert RegistrySource().checks_read(result, context()) == ()
    assert ECO_VILLAGE_1.promoter == PROMOTER


def test_a_zaubacorp_page_is_read_through_its_captcha_free_mirror() -> None:
    assert readable_pages(ZAUBA, PROMOTER) == [ECONOMIC_TIMES, ZAUBA]
    assert readable_pages(ECONOMIC_TIMES, PROMOTER) == [ECONOMIC_TIMES]


def test_the_registry_is_read_with_fetch_and_no_agent_when_the_table_is_readable() -> None:
    web = FakeWebClient(
        searches={
            "SUPERTECH LIMITED company CIN status zaubacorp": [
                SearchHit(title="supertech limited", url=ZAUBA, snippet="CIN U74899DL1995PLC074422")
            ]
        },
        texts={ECONOMIC_TIMES: DETAILS_TABLE},
    )
    events = run_source(RegistrySource(), context(web=web))

    [finding] = [e.finding for e in events if isinstance(e, FoundFinding)]
    assert finding.source_url == ECONOMIC_TIMES
    assert events[-1] == ChecksRead(("company_status",))
    assert [call for call in web.calls if call[0] == "agent"] == []


def test_a_mirror_page_for_another_company_is_not_used() -> None:
    other = DETAILS_TABLE.replace("Supertech Limited", "Supertech Realtors Limited")
    web = FakeWebClient(
        searches={
            "SUPERTECH LIMITED company CIN status zaubacorp": [
                SearchHit(title="supertech limited", url=ZAUBA, snippet="")
            ]
        },
        texts={ECONOMIC_TIMES: other},
        agent_runs={
            ZAUBA: [AgentDone("COMPLETED", {"legal_name": None, "cin": None, "status": None})]
        },
    )
    events = run_source(RegistrySource(), context(web=web))

    assert not any(isinstance(e, FoundFinding | ChecksRead) for e in events)
    assert [call for call in web.calls if call[0] == "agent"] == [("agent", ZAUBA)]
    assert Progress("Opening www.zaubacorp.com") in events
