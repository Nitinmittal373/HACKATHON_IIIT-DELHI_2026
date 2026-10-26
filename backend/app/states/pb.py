"""Punjab: RERA Punjab."""

from app.states.base import StateSpec
from app.states.search_adapter import SearchStateAdapter

ADAPTER = SearchStateAdapter(
    StateSpec(
        code="PB",
        name="Punjab",
        rera_name="RERA Punjab",
        domains=("rera.punjab.gov.in",),
        id_patterns=(r"PBRERA-[A-Z0-9]+-PR\d+",),
        coverage="search_only",
        examples=("PBRERA-SAS79-PR0083",),
        complaint_url="https://rera.punjab.gov.in/",
        search_url="https://rera.punjab.gov.in/reraindex/publicview/projectinfo",
        query_name="Punjab RERA",
        note=("Fetch fails (HTTP 522); Search returns quarterly update pages."),
    )
)
