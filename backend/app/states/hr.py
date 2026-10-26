"""Haryana: HRERA (Gurugram and Panchkula)."""

from app.states.base import StateSpec
from app.states.search_adapter import SearchStateAdapter

ADAPTER = SearchStateAdapter(
    StateSpec(
        code="HR",
        name="Haryana",
        rera_name="HRERA (Gurugram and Panchkula)",
        domains=("haryanarera.gov.in",),
        id_patterns=(
            r"HE?RERA-[A-Z]{3}-[A-Z]{2,4}-\d+-\d{4}",
            r"RC/REP/HARERA/GGM/\d+(?:/\d+)*",
        ),
        coverage="search_only",
        examples=("HRERA-PKL-JJR-867-2026", "RC/REP/HARERA/GGM/1061/793/2026/33"),
        complaint_url="https://haryanarera.gov.in/",
        search_url="https://haryanarera.gov.in/assistancecontrol/project_search_public/2",
        query_name="HRERA Haryana",
        positional_in="view_certificate",
        positional=(
            r"Date[.|\s]+(?:M/s\.? )?"
            r"(?P<promoter>[A-Z][\w &'.\-]{2,70}?(?:Ltd|Limited|LLP))"
        ),
        note=(
            "Fetch and an India-proxy agent both fail on this portal; Search returns "
            "approval date, status and promoter."
        ),
    )
)
