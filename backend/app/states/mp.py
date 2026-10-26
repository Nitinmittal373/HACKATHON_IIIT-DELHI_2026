"""Madhya Pradesh: MPRERA."""

from app.states.base import StateSpec
from app.states.search_adapter import SearchStateAdapter

ADAPTER = SearchStateAdapter(
    StateSpec(
        code="MP",
        name="Madhya Pradesh",
        rera_name="MPRERA",
        domains=("rera.mp.gov.in",),
        id_patterns=(r"P-[A-Z]{3}-\d{2}-\d{4}",),
        coverage="search_only",
        examples=(),
        complaint_url="https://rera.mp.gov.in/",
        search_url="https://rera.mp.gov.in/",
        query_name="Madhya Pradesh RERA MPRERA",
        note=(
            "No portal page could be read; the number format is not yet confirmed from a "
            "real record."
        ),
        detect_confidence=0.6,
        unverified_format=True,
    )
)
