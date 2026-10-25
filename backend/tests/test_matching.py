import pytest

from app.matching import (
    blob,
    brand,
    dedupe_titles,
    legal_name_in,
    mentions_project,
    normalize,
    project_pattern,
)
from app.tinyfish import SearchHit


def hit(title: str, url: str = "https://example.com/a", snippet: str = "") -> SearchHit:
    return SearchHit(title=title, url=url, snippet=snippet)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Supertech Ltd.", "supertech limited"),
        ("M/s Gaursons Promoters Pvt. Ltd", "m s gaursons promoters private limited"),
        ("  SUPERTECH   LIMITED ", "supertech limited"),
        (None, ""),
    ],
)
def test_normalize(raw: str | None, expected: str) -> None:
    assert normalize(raw) == expected


def test_legal_name_needs_the_whole_name() -> None:
    supertech = "SUPERTECH LIMITED"
    assert legal_name_in(supertech, normalize("Supertech Ltd (CIN U74899DL1995PLC074422)"))
    assert not legal_name_in(supertech, normalize("Supertech Realtors Limited"))
    assert not legal_name_in(supertech, normalize("Supertech EV Limited"))
    assert not legal_name_in(None, normalize("anything"))


def test_a_registry_address_carries_the_legal_name() -> None:
    page = hit("supertech limited", "https://www.zaubacorp.com/SUPERTECH-LIMITED-U74899DL1995PLC074422")
    assert legal_name_in("SUPERTECH LIMITED", blob(page))


@pytest.mark.parametrize(
    ("promoter", "expected"),
    [
        ("Jaypee Infratech Private Limited", "jaypee"),
        ("M/s Mr Proview Realtech Pvt Ltd", "proview"),
        ("SUPERTECH LIMITED", "supertech"),
        ("The India Company Limited", ""),
    ],
)
def test_brand_skips_honorifics_and_generic_words(promoter: str, expected: str) -> None:
    assert brand(promoter) == expected


def test_eco_village_one_never_matches_eco_village_two() -> None:
    pattern = project_pattern("SUPERTECH ECO VILLAGE-I PHASE I-C", "SUPERTECH LIMITED")

    assert mentions_project(pattern, "Eco Village-I, Greater Noida")
    assert mentions_project(pattern, "Eco Village-1")
    assert mentions_project(pattern, "Supertech Eco Village I Phase I-C")
    assert not mentions_project(pattern, "Eco Village-II")
    assert not mentions_project(pattern, "Eco Village-2, Greater Noida")
    assert not mentions_project(pattern, "Eco Village 10")
    assert not mentions_project(pattern, "Eco Citi")


def test_project_pattern_drops_the_brand_and_the_phase() -> None:
    pattern = project_pattern("Supertech Eco Village-II Phase II-A", "Supertech Limited")
    assert pattern is not None
    assert pattern.pattern == r"\beco\W+village\W+2\b"
    assert project_pattern(None) is None


def test_two_outlets_with_one_story_count_once() -> None:
    hits = [
        hit("NBCC to resume work on 16 Supertech projects - Times of India"),
        hit("NBCC to resume work on 16 Supertech projects | Hindustan Times"),
        hit("Supertech homebuyers wait for flats"),
    ]
    assert [h.title for h in dedupe_titles(hits)] == [hits[0].title, hits[2].title]
