"""Goa: Goa RERA."""

from app.states.base import StateSpec
from app.states.search_adapter import SearchStateAdapter

ADAPTER = SearchStateAdapter(
    StateSpec(
        code="GA",
        name="Goa",
        rera_name="Goa RERA",
        domains=("rera.goa.gov.in",),
        id_patterns=(r"PRGO\d{8}",),
        coverage="partial",
        examples=("PRGO08242238", "PRGO05242234"),
        complaint_url="https://rera.goa.gov.in/",
        search_url="https://rera.goa.gov.in/",
        query_name="Goa RERA",
        note=("Fetch reads the project page, which needs a link that Search finds first."),
    )
)
