"""Rajasthan: RAJ-RERA."""

from app.states.base import StateSpec
from app.states.search_adapter import SearchStateAdapter

ADAPTER = SearchStateAdapter(
    StateSpec(
        code="RJ",
        name="Rajasthan",
        rera_name="RAJ-RERA",
        domains=("rera.rajasthan.gov.in",),
        id_patterns=(r"RAJ/P/\d{4}/\d+",),
        coverage="search_only",
        examples=("RAJ/P/2020/1380", "RAJ/P/2024/3129"),
        complaint_url="https://rera.rajasthan.gov.in/",
        search_url="https://rera.rajasthan.gov.in/ProjectList",
        query_name="Rajasthan RERA",
        note=(
            "The portal needs JavaScript, so Fetch returns nothing; Search returns "
            "promoter project lists."
        ),
    )
)
