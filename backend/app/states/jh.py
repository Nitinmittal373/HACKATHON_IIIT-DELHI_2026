"""Jharkhand: JHARERA."""

from app.states.base import StateSpec
from app.states.search_adapter import SearchStateAdapter

ADAPTER = SearchStateAdapter(
    StateSpec(
        code="JH",
        name="Jharkhand",
        rera_name="JHARERA",
        domains=("jharera.jharkhand.gov.in",),
        id_patterns=(r"JHARERA/ ?PROJECT/\d+/\d{4}",),
        coverage="partial",
        examples=("JHARERA/PROJECT/215/2024", "JHARERA/PROJECT/132/2021"),
        complaint_url="https://jharera.jharkhand.gov.in/",
        search_url="https://jharera.jharkhand.gov.in/Home/RegisteredProjectsList",
        query_name="Jharkhand RERA JHARERA",
        note=(
            "Fetch reads the first page of the registered-projects list; a project "
            "further down is found through Search only."
        ),
        row_parser="jharkhand",
    )
)
