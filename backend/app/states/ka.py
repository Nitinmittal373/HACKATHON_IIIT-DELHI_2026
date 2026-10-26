"""Karnataka: K-RERA."""

from app.states.base import StateSpec
from app.states.search_adapter import SearchStateAdapter

ADAPTER = SearchStateAdapter(
    StateSpec(
        code="KA",
        name="Karnataka",
        rera_name="K-RERA",
        domains=("rera.karnataka.gov.in",),
        id_patterns=(r"PRM/KA/RERA/\d+/\d+/PR/\d{6}/\d{6}",),
        coverage="search_only",
        examples=("PRM/KA/RERA/1251/309/PR/190517/002554", "PRM/KA/RERA/1251/446/PR/170915/000176"),
        complaint_url="https://rera.karnataka.gov.in/",
        search_url="https://rera.karnataka.gov.in/viewAllProjects",
        query_name="Karnataka RERA",
        note=(
            "Fetch cannot reach the portal; Search returns the registration certificate "
            "page and project lists."
        ),
        positional_in="reraCertificate",
        extra_positional=(
            (
                "/view",
                r"PR/\d{6}/\d{6},\s+(?P<promoter>[^,;]{3,80}),\s+(?P<name>[^,;]{3,80}),"
                r"\s+[^,;]{3,30},\s+(?P<district>[^,;]{3,40})",
            ),
        ),
        positional=r"PR/\d{6}/\d{6}[.\s]+(?P<name>[A-Z0-9][A-Z0-9 &'.\-]{2,80}?),\s",
        details_template="https://rera.karnataka.gov.in/reraCertificate?CER_NO={id}",
    )
)
