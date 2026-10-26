"""Uttarakhand: UKRERA."""

from app.states.base import StateSpec
from app.states.search_adapter import SearchStateAdapter

ADAPTER = SearchStateAdapter(
    StateSpec(
        code="UK",
        name="Uttarakhand",
        rera_name="UKRERA",
        domains=("rera.uk.gov.in",),
        id_patterns=(r"UKREP\d{10,14}",),
        coverage="search_only",
        examples=("UKREP06240000564",),
        complaint_url="https://rera.uk.gov.in/",
        search_url="https://rera.uk.gov.in/",
        query_name="Uttarakhand RERA UKRERA",
        note=("No portal page could be read; the number comes from a registration certificate."),
    )
)
