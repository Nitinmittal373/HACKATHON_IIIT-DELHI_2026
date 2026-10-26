"""Assam: RERA Assam."""

from app.states.base import StateSpec
from app.states.search_adapter import SearchStateAdapter

ADAPTER = SearchStateAdapter(
    StateSpec(
        code="AS",
        name="Assam",
        rera_name="RERA Assam",
        domains=("rera.assam.gov.in",),
        id_patterns=(r"RERAA KM \d+ OF \d{4}-\d{4}",),
        coverage="search_only",
        examples=("RERAA KM 68 OF 2022-2023", "RERAA KM 105 OF 2022-2023"),
        complaint_url="https://rera.assam.gov.in/",
        search_url="https://rera.assam.gov.in/admincontrol/registered_projects/1",
        query_name="Assam RERA",
        note=("Search returns project pages with approval remarks; Fetch cannot reach the portal."),
    )
)
