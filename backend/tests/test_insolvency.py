from typing import Any

import pytest

from app.models import Project
from app.scoring.engine import score
from app.sources.insolvency import (
    InsolvencySource,
    decide_scope,
    pick_case_page,
    to_findings,
)
from app.tinyfish import SearchHit
from tests.sourcekit import ECO_VILLAGE_1, context

NEWS = "https://www.fortuneindia.com/enterprise/nclt-declares-supertech-insolvent/107553"
ORDER = "https://nclat.nic.in/display-board/view_order_pdf?fid=1"
ECO_VILLAGE_2 = ECO_VILLAGE_1.model_copy(update={"name": "SUPERTECH ECO VILLAGE-II PHASE II-A"})


def answer(**fields: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "admitted": True,
        "admitted_on": "2022-03-25",
        "covers_whole_company": False,
        "projects_named": [],
        "scope_quote": "The order covers the project named below.",
        "order_url": None,
    }
    return base | fields


def kinds(findings: list[Any]) -> list[tuple[str, Any]]:
    return [(f.kind, f.scope) for f in findings]


def test_eco_village_one_is_not_covered_by_a_process_limited_to_eco_village_two() -> None:
    result = answer(projects_named=["Eco Village-II"])
    assert decide_scope(result, ECO_VILLAGE_1) == "other_project"
    assert decide_scope(result, ECO_VILLAGE_2) == "this_project"


def test_roman_and_arabic_numerals_name_the_same_project() -> None:
    assert decide_scope(answer(projects_named=["Eco Village 1, Greater Noida"]), ECO_VILLAGE_1) == (
        "this_project"
    )


def test_another_project_costs_sixty_and_needs_review() -> None:
    findings = to_findings(
        answer(projects_named=["Eco Village-II"]), ECO_VILLAGE_1, NEWS, context()
    )

    assert kinds(findings) == [("insolvency_admitted", None), ("insolvency_scope", "other_project")]
    assert [f.verdict for f in findings] == ["review", "review"]
    result = score(findings, ["insolvency"])
    assert (result.value, result.hard_stop) == (91, False)
    assert [d.points for d in result.drivers] == [-9.0]  # one case, counted once


def test_this_project_in_an_official_order_is_a_hard_stop() -> None:
    findings = to_findings(
        answer(projects_named=["Eco Village-I"]), ECO_VILLAGE_1, ORDER, context()
    )

    assert findings[-1].reliability == "primary"
    result = score(findings, ["insolvency"])
    assert result.hard_stop and result.value <= 39


def test_the_whole_company_in_an_official_order_is_a_hard_stop() -> None:
    findings = to_findings(answer(covers_whole_company=True), ECO_VILLAGE_1, ORDER, context())
    assert kinds(findings)[-1] == ("insolvency_scope", "company")
    assert score(findings, ["insolvency"]).hard_stop


def test_a_news_report_alone_never_causes_a_hard_stop() -> None:
    findings = to_findings(answer(covers_whole_company=True), ECO_VILLAGE_1, NEWS, context())

    assert kinds(findings)[-1] == ("insolvency_scope_unverified", "company")
    assert "No court order was read" in findings[-1].title
    result = score(findings, ["insolvency"])
    assert (result.value, result.hard_stop) == (100, False)


def test_an_admission_without_a_scope_is_shown_for_review_with_no_points() -> None:
    findings = to_findings(answer(), ECO_VILLAGE_1, NEWS, context())

    assert kinds(findings) == [("insolvency_admitted", None)]
    assert (
        findings[0].title
        == "Insolvency application against SUPERTECH LIMITED was admitted on 25 Mar 2022"
    )
    assert score(findings, ["insolvency"]).value == 100


def test_a_page_that_does_not_report_an_admission_gives_no_finding_and_no_read_check() -> None:
    result = answer(admitted=False)
    assert to_findings(result, ECO_VILLAGE_1, NEWS, context()) == []
    assert InsolvencySource().checks_read(result, context()) == ()
    assert InsolvencySource().checks_read(answer(), context()) == ("insolvency",)


def test_only_an_official_order_address_replaces_the_page_as_proof() -> None:
    [admitted, *_] = to_findings(
        answer(projects_named=["Eco Village-II"], order_url=ORDER), ECO_VILLAGE_1, NEWS, context()
    )
    assert admitted.source_url == ORDER

    [admitted, *_] = to_findings(
        answer(order_url="https://example.com/made-up-order.pdf"), ECO_VILLAGE_1, NEWS, context()
    )
    assert admitted.source_url == NEWS


@pytest.mark.parametrize(
    "project", [Project(rera_id="UPRERAPRJ1", details_url="https://up-rera.in/x")]
)
def test_a_project_without_a_name_cannot_be_matched(project: Project) -> None:
    assert decide_scope(answer(projects_named=["Eco Village-II"]), project) is None


def hit(url: str, title: str, snippet: str = "") -> SearchHit:
    return SearchHit(title=title, url=url, snippet=snippet)


def test_the_agent_is_sent_to_a_readable_page_about_the_promoter() -> None:
    hits = [
        hit("https://www.scribd.com/document/1/x", "NCLT Order on Supertech Limited Insolvency"),
        hit(ORDER, "Insolvency of Supertech Ltd NCLT order"),
        hit("https://www.supertechlimited.com/", "Supertech Limited CIRP update"),
        hit(NEWS, "NCLT declares Supertech insolvent", "Supertech Ltd insolvency admitted"),
        hit("https://example.com/other", "Supertech Realtors Limited insolvency NCLT"),
    ]
    page = pick_case_page(hits, "SUPERTECH LIMITED")
    assert page is not None and page.url == NEWS  # deep page first; no PDF, upload or other company
