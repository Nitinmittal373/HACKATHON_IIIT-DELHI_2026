"""West Bengal: WBRERA."""

from app.states.base import StateSpec
from app.states.search_adapter import SearchStateAdapter

ADAPTER = SearchStateAdapter(
    StateSpec(
        code="WB",
        name="West Bengal",
        rera_name="WBRERA",
        domains=("rera.wb.gov.in",),
        id_patterns=(r"WBRERA/P/[A-Z]{3}/\d{4}/\d+",),
        coverage="search_only",
        examples=("WBRERA/P/KOL/2024/002005", "WBRERA/P/NOR/2024/002226"),
        complaint_url="https://rera.wb.gov.in/",
        search_url="https://rera.wb.gov.in/",
        query_name="WBRERA West Bengal",
        note=(
            "Search returns project pages with completion and extension dates; Fetch "
            "cannot reach the portal."
        ),
    )
)
