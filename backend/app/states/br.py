"""Bihar: RERA Bihar."""

from app.states.base import StateSpec
from app.states.search_adapter import SearchStateAdapter

ADAPTER = SearchStateAdapter(
    StateSpec(
        code="BR",
        name="Bihar",
        rera_name="RERA Bihar",
        domains=("rera.bihar.gov.in",),
        id_patterns=(r"BRERAP\d{10,}[A-Z0-9]*",),
        coverage="search_only",
        examples=("BRERAP187328070625271029E00",),
        complaint_url="https://rera.bihar.gov.in/",
        search_url="https://rera.bihar.gov.in/RegisteredPP.aspx",
        query_name="Bihar RERA",
        note=("Fetch reads the project list (number, promoter, address), which has no dates."),
    )
)
