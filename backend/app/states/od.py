"""Odisha: ORERA."""

from app.states.base import StateSpec
from app.states.search_adapter import SearchStateAdapter

ADAPTER = SearchStateAdapter(
    StateSpec(
        code="OD",
        name="Odisha",
        rera_name="ORERA",
        domains=("rera.odisha.gov.in",),
        id_patterns=(r"RP/\d{2}/\d{4}/\d{5}",),
        coverage="search_only",
        examples=("RP/09/2019/00287", "RP/07/2024/01240"),
        complaint_url="https://rera.odisha.gov.in/complaint-status/",
        search_url="https://rera.odisha.gov.in/projects/project-list",
        query_name="Odisha RERA ORERA",
        note=("Project data loads with JavaScript, so Fetch sees an empty shell."),
    )
)
