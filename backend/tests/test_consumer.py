from app.sources.consumer import ConsumerSource, to_findings
from tests.sourcekit import ECO_VILLAGE_1, context

URL = "https://e-jagriti.gov.in/advance-case-search"
PROMOTER = "SUPERTECH LIMITED"


def row(party: str) -> dict[str, str]:
    return {"case_number": "CC/1/2024", "forum": "District Commission", "opposite_party": party}


def test_only_cases_naming_the_exact_legal_name_are_counted() -> None:
    result = {
        "total_cases": 3,
        "cases": [
            row("Supertech Ltd."),
            row("SUPERTECH LIMITED & Others"),
            row("Supertech Realtors"),
        ],
    }
    [finding] = to_findings(result, PROMOTER, URL, context())

    assert finding.count == 2
    assert finding.verdict == "review"
    assert finding.title == (
        "2 consumer cases against SUPERTECH LIMITED on the first page of e-Jagriti results"
    )


def test_no_matching_case_is_reported_as_not_found_without_points() -> None:
    [finding] = to_findings({"total_cases": 0, "cases": []}, PROMOTER, URL, context())
    assert (finding.verdict, finding.count) == ("not_found", 0)


def test_an_all_empty_answer_gives_nothing() -> None:
    assert to_findings({"total_cases": None, "cases": []}, PROMOTER, URL, context()) == []


def test_the_search_starts_on_the_case_search_page_with_the_promoter_name() -> None:
    import asyncio

    task = asyncio.run(ConsumerSource().task(context()))
    assert task is not None
    assert task.url == URL
    assert ECO_VILLAGE_1.promoter in task.goal


def test_a_single_case_is_not_pluralised() -> None:
    [finding] = to_findings(
        {"total_cases": 1, "cases": [row("SUPERTECH LIMITED")]}, PROMOTER, URL, context()
    )
    assert finding.title.startswith("1 consumer case against SUPERTECH LIMITED")
