"""Chhattisgarh: CG RERA."""

from app.states.base import StateSpec
from app.states.search_adapter import SearchStateAdapter

ADAPTER = SearchStateAdapter(
    StateSpec(
        code="CG",
        name="Chhattisgarh",
        rera_name="CG RERA",
        domains=("rera.cgstate.gov.in",),
        id_patterns=(r"PCGRERA\d{12}",),
        coverage="search_only",
        examples=("PCGRERA220618000295", "PCGRERA030424001753"),
        complaint_url="https://rera.cgstate.gov.in/",
        search_url="https://rera.cgstate.gov.in/Approved_project_List.aspx",
        query_name="Chhattisgarh RERA",
        note=("Search returns the approved, delayed and extended project lists."),
    )
)
