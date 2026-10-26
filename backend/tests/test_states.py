"""State adapters: number formats, parsing of recorded Search results, and honest gaps.

Recordings come from scripts/capture_states.py (free Search and Fetch, 26 Oct 2026).
"""

import asyncio
import json
from datetime import UTC, date, datetime

import pytest

from app.models import Project
from app.states.lists import bihar_row, jharkhand_row
from app.states.registry import ADAPTERS, BY_CODE, detect_state, state_of
from app.states.resolver import resolve_any
from app.states.text import labelled_date, labelled_text, parse_date
from tests.fakes import FIXTURES, FakeWebClient

NOW = datetime(2026, 10, 26, 12, 0, tzinfo=UTC)

REAL_NUMBERS = [
    ("UPRERAPRJ8334", "UP"),
    ("UPRERAPRJ188811/08/2024", "UP"),
    ("P99000055716", "MH"),
    ("P51800000937", "MH"),
    ("HRERA-PKL-JJR-867-2026", "HR"),
    ("RC/REP/HARERA/GGM/1061/793/2026/33", "HR"),
    ("PRM/KA/RERA/1251/309/PR/190517/002554", "KA"),
    ("DLRERA2023P0008", "DL"),
    ("PR/GJ/SURAT/SURAT CITY/SUDA/RAA00299/290917", "GJ"),
    ("TN/01/Layout/0001/2017", "TN"),
    ("TNRERA/7/LO/3733/2026", "TN"),
    ("RAJ/P/2020/1380", "RJ"),
    ("WBRERA/P/KOL/2024/002005", "WB"),
    ("PBRERA-SAS79-PR0083", "PB"),
    ("K-RERA/PRJ/039/2020", "KL"),
    ("410 OF 2017", "AP"),
    ("UKREP06240000564", "UK"),
    ("BRERAP187328070625271029E00", "BR"),
    ("BRERAP00923-1/607/R-783/2019", "BR"),
    ("RP/09/2019/00287", "OD"),
    ("PRGO08242238", "GA"),
    ("PCGRERA220618000295", "CG"),
    ("RERAHPSOP09170006", "HP"),
    ("JHARERA/PROJECT/215/2024", "JH"),
    ("RERAA KM 68 OF 2022-2023", "AS"),
    ("RERA-JK-JMU-6-2026", "JK"),
]


def recording(name: str) -> FakeWebClient:
    return FakeWebClient().replay(json.loads((FIXTURES / name).read_text(encoding="utf-8")))


@pytest.mark.parametrize(("number", "state"), REAL_NUMBERS)
def test_detect_names_the_state_of_a_real_number(number: str, state: str) -> None:
    found = detect_state(number)
    assert found is not None and found[0].code == state
    assert state_of(number) == state


def test_detect_is_forgiving_about_case_and_dashes() -> None:
    assert detect_state(" k‐rera/prj/039/2020 ")[0].code == "KL"  # type: ignore[index]
    assert detect_state("upreraprj-8334")[0].code == "UP"  # type: ignore[index]


@pytest.mark.parametrize("text", ["Gaur City", "Lodha Palava", "8334", "P5180000093"])
def test_a_name_or_a_short_number_is_no_state(text: str) -> None:
    assert detect_state(text) is None


def test_every_listed_example_belongs_to_its_own_state() -> None:
    for adapter in ADAPTERS:
        for example in adapter.examples:
            assert detect_state(example)[0].code == adapter.code, example  # type: ignore[index]


def test_formats_not_yet_verified_have_no_examples() -> None:
    for code in ("TG", "MP"):
        assert BY_CODE[code].examples == ()
        assert BY_CODE[code].detect("P02400001234" if code == "TG" else "P-IND-19-1234") < 0.9


def test_only_up_is_full_and_goa_bihar_jharkhand_are_partial() -> None:
    levels = {a.code: a.coverage for a in ADAPTERS}
    assert levels["UP"] == "full"
    assert {c for c, level in levels.items() if level == "partial"} == {"GA", "BR", "JH"}
    assert levels["MH"] == levels["KA"] == levels["HR"] == "search_only"


def read(code: str, rera_id: str, fixture: str):  # type: ignore[no-untyped-def]
    web = recording(fixture)
    adapter = BY_CODE[code]
    project = Project(
        rera_id=rera_id,
        state=code,
        details_url=adapter.details_url(Project(rera_id=rera_id, state=code, details_url="")),
    )
    return asyncio.run(adapter.read(project, web, NOW)), web


def test_maharashtra_snippet_gives_name_promoter_and_district() -> None:
    record, _ = read("MH", "P99000055716", "states_mh.json")
    assert record is not None
    assert (record.name, record.promoter_name, record.district) == (
        "SRI BALAJI RESIDENCY",
        "Bhupesh Vasudev Bari",
        "Palghar",
    )
    assert record.source_url.startswith("https://maharera.maharashtra.gov.in/")
    assert record.read_via == "search_snippet"
    assert "P99000055716" in record.raw_snippets[0]


def test_a_snippet_without_dates_leaves_them_unread() -> None:
    record, _ = read("MH", "P99000055716", "states_mh.json")
    assert record is not None
    assert record.registration_date is None and record.promised_completion is None
    assert record.latest_completion is None


def test_karnataka_approval_date_comes_from_the_certificate_snippet() -> None:
    record, _ = read("KA", "PRM/KA/RERA/1251/446/PR/170915/000176", "states_ka.json")
    assert record is not None
    assert record.registration_date == date(2017, 9, 15)
    assert "reraCertificate" in record.source_url


def test_haryana_certificate_gives_registration_and_completion() -> None:
    record, _ = read("HR", "RC/REP/HARERA/GGM/1059/791/2026/31", "states_hr.json")
    assert record is not None
    assert record.registration_date == date(2026, 5, 4)
    assert record.promised_completion == date(2033, 8, 31)


def test_goa_page_is_opened_and_read_in_full() -> None:
    record, web = read("GA", "PRGO08242238", "states_ga.json")
    assert record is not None
    assert record.name == "Whiterock Square"
    assert record.registration_date == date(2024, 8, 16)
    assert record.promised_completion == date(2027, 5, 31)
    assert record.status == "New Project Launch"
    assert record.read_via is None
    assert any(kind == "fetch_text" for kind, _ in web.calls)


def test_bihar_and_jharkhand_rows_are_parsed_from_the_recorded_lists() -> None:
    bihar = json.loads((FIXTURES / "states_br.json").read_text(encoding="utf-8"))["texts"]
    jharkhand = json.loads((FIXTURES / "states_jh.json").read_text(encoding="utf-8"))["texts"]
    row = bihar_row(next(iter(bihar.values())), "BRERAP00923-1/607/R-783/2019")
    assert row and "Project Name: A ONE HERITAGE" in row and "17 Oct 2019" in row
    row = jharkhand_row(next(iter(jharkhand.values())), "JHARERA/PROJECT/46/2018")
    assert row and "Project Name: Global Platinium" in row and "02/08/2018" in row
    assert bihar_row("nothing here", "BRERAP1") is None


def test_a_number_no_portal_page_shows_is_not_invented() -> None:
    adapter = BY_CODE["MH"]
    project = Project(rera_id="P51800099999", state="MH", details_url="")
    assert asyncio.run(adapter.read(project, FakeWebClient(), NOW)) is None


def test_name_search_groups_candidates_from_several_states() -> None:
    found = asyncio.run(
        resolve_any("Prestige Lakeside Habitat", recording("states_name_prestige.json"))
    )
    states = {p.state for p in found.candidates}
    assert "KA" in states
    top = found.candidates[0]
    assert top.rera_id == "PRM/KA/RERA/1251/446/PR/170915/000176"
    assert top.state_name == "Karnataka"


def test_a_number_searches_only_its_own_state() -> None:
    web = recording("states_mh.json")
    found = asyncio.run(resolve_any("P99000055716", web))
    assert found.detected_state == "MH" and found.searched_states == ["MH"]
    assert [p.rera_id for p in found.candidates] == ["P99000055716"]


def test_text_helpers_read_the_ways_portals_write_dates() -> None:
    assert parse_date("Fri Aug 16 11:52:18 IST 2024") == date(2024, 8, 16)
    assert parse_date("3rd March 2026") == date(2026, 3, 3)
    assert parse_date("24-May-2024") == date(2024, 5, 24)
    text = "PROJECT COMPLETION DATE: 30-12-2027; EXTENSION COMPLETION DATE: NA; X"
    assert labelled_date(text, ("PROJECT COMPLETION DATE",)) == date(2027, 12, 30)
    assert labelled_date(text, ("EXTENSION COMPLETION DATE",)) is None


def test_a_value_cut_off_by_the_search_engine_is_not_trusted() -> None:
    assert (
        labelled_text("Promoter Name: Gaursons Promoters Private ...", ("Promoter Name",)) is None
    )
    assert labelled_text("Promoter Name: Gaursons India Ltd; next", ("Promoter Name",)) == (
        "Gaursons India Ltd"
    )
