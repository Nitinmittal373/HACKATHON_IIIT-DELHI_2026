"""Himachal Pradesh: HP RERA."""

from app.states.base import StateSpec
from app.states.search_adapter import SearchStateAdapter

ADAPTER = SearchStateAdapter(
    StateSpec(
        code="HP",
        name="Himachal Pradesh",
        rera_name="HP RERA",
        domains=("hprera.nic.in",),
        id_patterns=(r"RERAHP[A-Z]{2,4}\d{8,}",),
        coverage="search_only",
        examples=("RERAHPSOP09170006",),
        complaint_url="https://hprera.nic.in/",
        search_url="https://hprera.nic.in/PublicDashboard",
        query_name="Himachal Pradesh HPRERA",
        note=("The public dashboard needs a form; Search returns the quarterly project list."),
    )
)
