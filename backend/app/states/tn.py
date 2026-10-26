"""Tamil Nadu: TNRERA."""

from app.states.base import StateSpec
from app.states.search_adapter import SearchStateAdapter

ADAPTER = SearchStateAdapter(
    StateSpec(
        code="TN",
        name="Tamil Nadu",
        rera_name="TNRERA",
        domains=("rera.tn.gov.in",),
        id_patterns=(
            r"TN/\d+/[A-Za-z]+/\d+/\d{4}",
            r"TNRERA/\d+/[A-Za-z]+/\d+/\d{4}",
        ),
        coverage="search_only",
        examples=("TN/01/Layout/0001/2017", "TNRERA/7/LO/3733/2026"),
        complaint_url="https://rera.tn.gov.in/complaint/login",
        search_url="https://rera.tn.gov.in/registered-building/tn",
        query_name="TNRERA Tamil Nadu",
        note=(
            "Search returns project pages with status and completion date; Fetch cannot "
            "reach the portal."
        ),
    )
)
