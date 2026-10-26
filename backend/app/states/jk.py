"""Jammu and Kashmir: JK RERA."""

from app.states.base import StateSpec
from app.states.search_adapter import SearchStateAdapter

ADAPTER = SearchStateAdapter(
    StateSpec(
        code="JK",
        name="Jammu and Kashmir",
        rera_name="JK RERA",
        domains=("rera.jk.gov.in",),
        id_patterns=(r"RERA-JK-[A-Z]{3}-\d+-\d{4}",),
        coverage="search_only",
        examples=("RERA-JK-JMU-6-2026", "RERA-JK-JMU-5-2026"),
        complaint_url="https://rera.jk.gov.in/",
        search_url="https://rera.jk.gov.in/admincontrol/registered_projects/1",
        query_name="JK RERA Jammu Kashmir",
        note=("Search returns the registered project list and project pages."),
    )
)
