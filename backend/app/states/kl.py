"""Kerala: K-RERA."""

from app.states.base import StateSpec
from app.states.search_adapter import SearchStateAdapter

ADAPTER = SearchStateAdapter(
    StateSpec(
        code="KL",
        name="Kerala",
        rera_name="K-RERA",
        domains=("rera.kerala.gov.in",),
        id_patterns=(r"K-RERA/PRJ/(?:[A-Z]{3}/)?\d+/\d{4}",),
        coverage="search_only",
        examples=("K-RERA/PRJ/039/2020", "K-RERA/PRJ/KKD/096/2025"),
        complaint_url="https://rera.kerala.gov.in/",
        search_url="https://rera.kerala.gov.in/explore-projects",
        query_name="Kerala RERA",
        note=("Search returns registration and extension certificates."),
    )
)
