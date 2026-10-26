"""Delhi: Delhi RERA."""

from app.states.base import StateSpec
from app.states.search_adapter import SearchStateAdapter

ADAPTER = SearchStateAdapter(
    StateSpec(
        code="DL",
        name="Delhi",
        rera_name="Delhi RERA",
        domains=("erera.co.in",),
        id_patterns=(r"DLRERA\d{4}P\d{4}",),
        coverage="search_only",
        examples=("DLRERA2023P0008", "DLRERA2022P0036"),
        complaint_url="https://erera.co.in/reradelhiindex/GenComplaint/RegComplaint",
        search_url="https://erera.co.in/reradelhiindex/PublicView/ProjectInfo",
        query_name="Delhi RERA",
        note=("Delhi RERA's e-portal; Fetch cannot reach it."),
    )
)
