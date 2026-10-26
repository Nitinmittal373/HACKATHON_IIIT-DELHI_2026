"""Registration numbers in a buyer's own PDF or QR text: limits, privacy and confirmation."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.extract import MAX_BYTES, ExtractError, numbers_in_document, pdf_text
from app.main import create_app
from app.tinyfish import SearchHit
from tests.conftest import make_settings
from tests.fakes import FakeWebClient, search_key
from tests.pdfs import BROCHURE, make_pdf

MH = "P51900008345"
KA = "PRM/KA/RERA/1251/446/PR/170915/000176"
PORTAL = "maharera.maharashtra.gov.in"


def client(tmp_path: Path, web: FakeWebClient | None = None, **overrides: object) -> TestClient:
    settings = make_settings(tmp_path, **overrides)
    return TestClient(create_app(settings, web=web or FakeWebClient()))


def post_pdf(http: TestClient, data: bytes):
    return http.post("/api/extract", content=data, headers={"content-type": "application/pdf"})


def test_a_brochure_pdf_gives_its_numbers_and_the_words_around_them(tmp_path: Path) -> None:
    with client(tmp_path) as http:
        response = post_pdf(http, make_pdf(BROCHURE))
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "your document"
    assert [(n["state"], n["rera_id"]) for n in body["numbers"]] == [("MH", MH), ("KA", KA)]
    assert "MahaRERA Reg. No." in body["numbers"][0]["line"]
    assert all(c["status"] == "from_document" for c in body["candidates"])
    assert all(c["sources"] == ["your document"] for c in body["candidates"])


def test_personal_details_never_come_back(tmp_path: Path) -> None:
    with client(tmp_path) as http:
        body = post_pdf(http, make_pdf(BROCHURE)).text
    for private in ("9876543210", "test.person@example.test", "ABCDE1234F", "1234 5678 9012"):
        assert private not in body


def test_a_number_the_portal_prints_is_confirmed(tmp_path: Path) -> None:
    hit = SearchHit(
        title="Projects search result",
        url=f"https://{PORTAL}/projects-search-result?certificate_no={MH}",
        snippet=f"{MH}. SUNRISE HEIGHTS. SUNRISE BUILDERS LIMITED. THANE.",
    )
    web = FakeWebClient(searches={search_key(f"{MH} MahaRERA project", PORTAL): [hit]})
    with client(tmp_path, web) as http:
        body = post_pdf(http, make_pdf(BROCHURE)).json()
    mh = next(c for c in body["candidates"] if c["rera_id"] == MH)
    assert mh["status"] == "confirmed"
    assert mh["sources"] == [PORTAL, "your document"]
    assert mh["promoter"] == "SUNRISE BUILDERS LIMITED"


def test_a_pdf_without_a_number_says_what_to_do(tmp_path: Path) -> None:
    with client(tmp_path) as http:
        body = post_pdf(http, make_pdf(["Sunrise Heights", "Call us today"])).json()
    assert body["numbers"] == [] and body["candidates"] == []
    assert "Ask the builder for the number in writing" in body["message"]


def test_a_file_over_five_megabytes_is_refused(tmp_path: Path) -> None:
    with client(tmp_path) as http:
        response = post_pdf(http, b"%PDF-1.4\n" + b"0" * (MAX_BYTES + 1))
    assert response.status_code == 413
    assert "5 MB" in response.json()["detail"]


@pytest.mark.parametrize("kind", ["image/png", "image/jpeg", "text/plain", "application/zip"])
def test_other_file_types_are_refused(tmp_path: Path, kind: str) -> None:
    with client(tmp_path) as http:
        response = http.post("/api/extract", content=b"data", headers={"content-type": kind})
    assert response.status_code == 415


def test_a_file_that_is_not_a_pdf_is_refused(tmp_path: Path) -> None:
    with client(tmp_path) as http:
        response = post_pdf(http, b"MZ not a pdf at all")
    assert response.status_code == 422


def test_a_damaged_pdf_is_refused_with_a_reason(tmp_path: Path) -> None:
    with client(tmp_path) as http:
        response = post_pdf(http, b"%PDF-1.4\n1 0 obj << /Broken >> endobj")
    assert response.status_code == 422
    assert response.json()["detail"] == "This PDF could not be read"


def test_qr_text_is_read_like_a_document(tmp_path: Path) -> None:
    text = f"https://maharerait.example.test/view?certificate_no={MH}&x=1"
    with client(tmp_path) as http:
        response = http.post("/api/extract", json={"text": text})
    body = response.json()
    assert body["source"] == "your QR code"
    assert [n["rera_id"] for n in body["numbers"]] == [MH]


def test_json_without_text_is_refused(tmp_path: Path) -> None:
    with client(tmp_path) as http:
        response = http.post("/api/extract", json={"nope": 1})
    assert response.status_code == 422


def test_files_are_rate_limited_per_address(tmp_path: Path) -> None:
    with client(tmp_path) as http:
        answers = [http.post("/api/extract", json={"text": "x"}).status_code for _ in range(12)]
    assert answers.count(429) == 2
    assert answers[0] == 200


def test_nothing_is_written_to_disk(tmp_path: Path) -> None:
    before = {p for p in tmp_path.rglob("*")}
    with client(tmp_path) as http:
        post_pdf(http, make_pdf(BROCHURE))
    created = {p.name for p in set(tmp_path.rglob("*")) - before}
    assert not any(name.endswith((".pdf", ".tmp")) for name in created)


def test_pdf_text_enforces_the_limit_itself() -> None:
    with pytest.raises(ExtractError):
        pdf_text(b"%PDF" + b"0" * MAX_BYTES)


def test_numbers_in_a_url_are_found_after_decoding() -> None:
    found = numbers_in_document("https://x.test/?no=PRM%2FKA%2FRERA%2F1251%2F446%2FPR%2F170915%2F000176")
    assert [n.rera_id for n in found] == [KA]
