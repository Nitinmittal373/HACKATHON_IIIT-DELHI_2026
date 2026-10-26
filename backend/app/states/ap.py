"""Andhra Pradesh: AP RERA."""

from app.states.base import StateSpec
from app.states.search_adapter import SearchStateAdapter

ADAPTER = SearchStateAdapter(
    StateSpec(
        code="AP",
        name="Andhra Pradesh",
        rera_name="AP RERA",
        domains=("rera.ap.gov.in",),
        id_patterns=(r"\d{1,5} OF \d{4}",),
        coverage="search_only",
        examples=("410 OF 2017", "246 OF 2018"),
        complaint_url="https://rera.ap.gov.in/",
        search_url="https://rera.ap.gov.in/RERA/Views/Home.aspx",
        query_name="Andhra Pradesh RERA",
        note=("Numbers look like '410 OF 2017'; Fetch cannot reach the portal."),
        detect_confidence=0.7,
    )
)
