"""Telangana: TG-RERA."""

from app.states.base import StateSpec
from app.states.search_adapter import SearchStateAdapter

ADAPTER = SearchStateAdapter(
    StateSpec(
        code="TG",
        name="Telangana",
        rera_name="TG-RERA",
        domains=("rerait.telangana.gov.in", "rera.telangana.gov.in"),
        id_patterns=(r"P0\d{10}",),
        coverage="search_only",
        examples=(),
        complaint_url="https://rera.telangana.gov.in/complaint/",
        search_url="https://rerait.telangana.gov.in/SearchList/Search",
        query_name="Telangana RERA TGRERA",
        note=(
            "The project search sits behind a CAPTCHA, which is never bypassed. The "
            "number format is not yet confirmed from a real record."
        ),
        detect_confidence=0.6,
        unverified_format=True,
    )
)
