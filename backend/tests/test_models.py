import pytest
from pydantic import ValidationError

from app.models import CheckCreate, is_uprera_url, normalize_rera_id


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("UPRERAPRJ8334", "UPRERAPRJ8334"),
        ("  upreraprj8334 ", "UPRERAPRJ8334"),
        ("UPRERAPRJ 8334", "UPRERAPRJ8334"),
        ("UPRERAPRJ188811/08/2024", "UPRERAPRJ188811/08/2024"),
        ("UPRERAPRJ12345678", None),
        ("UPRERAPRJ8334/8/2024", None),
        ("Gaur City", None),
        ("", None),
    ],
)
def test_normalize_rera_id(text: str, expected: str | None) -> None:
    assert normalize_rera_id(text) == expected


def test_check_create_normalizes_the_number() -> None:
    assert CheckCreate(rera_id=" upreraprj8334").rera_id == "UPRERAPRJ8334"


@pytest.mark.parametrize(
    "body",
    [
        {"rera_id": "8334"},
        {"rera_id": "UPRERAPRJ8334", "extra": "field"},
        {"rera_id": "UPRERAPRJ188811/08/2024"},
        {"rera_id": "UPRERAPRJ8334", "details_url": "https://evil.example/up-rera.in"},
        {"rera_id": "UPRERAPRJ8334", "details_url": "http://www.up-rera.in/x"},
    ],
)
def test_check_create_rejects_bad_input(body: dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        CheckCreate.model_validate(body)


def test_uprera_url_check_uses_the_real_host() -> None:
    assert is_uprera_url("https://up-rera.in/Projectsummary?x=1")
    assert not is_uprera_url("https://up-rera.in.evil.example/")
    assert not is_uprera_url("https://uprera.azurewebsites.net/x")
