"""Gujarat: GujRERA."""

from app.states.base import StateSpec
from app.states.search_adapter import SearchStateAdapter

ADAPTER = SearchStateAdapter(
    StateSpec(
        code="GJ",
        name="Gujarat",
        rera_name="GujRERA",
        domains=("gujrera.gujarat.gov.in",),
        id_patterns=(r"PR/GJ/[A-Z ]+/[A-Z ]+/[A-Za-z ]+/[A-Z]{3}\d{4,6}/\d{6}",),
        coverage="search_only",
        examples=(
            "PR/GJ/SURAT/SURAT CITY/SUDA/RAA00299/290917",
            "PR/GJ/AHMEDABAD/AHMEDABAD CITY/AUDA/RAA04710/210119",
        ),
        complaint_url="https://gujrera.gujarat.gov.in/",
        search_url="https://gujrera.gujarat.gov.in/",
        query_name="GujRERA Gujarat",
        note=("Search returns registration certificates; Fetch cannot reach the portal."),
    )
)
