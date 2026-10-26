"""Maharashtra: MahaRERA."""

from app.states.base import StateSpec
from app.states.search_adapter import SearchStateAdapter

ADAPTER = SearchStateAdapter(
    StateSpec(
        code="MH",
        name="Maharashtra",
        rera_name="MahaRERA",
        domains=("maharera.maharashtra.gov.in",),
        id_patterns=(r"P[1-9]\d{10}",),
        coverage="search_only",
        examples=("P51800000937", "P52100031791"),
        complaint_url="https://www.maharera.maharashtra.gov.in/complaint-filing-under-registered-project",
        search_url="https://www.maharera.maharashtra.gov.in/projects-search-result",
        query_name="MahaRERA",
        note=(
            "Search shows the number, name, promoter and district. The full project view "
            "is behind a login, so it is never opened."
        ),
        details_template="https://maharera.maharashtra.gov.in/projects-search-result?certificate_no={id}",
        positional_in="projects-search-result",
        positional=r"P[1-9]\d{10}\.\s+(?P<name>[^.]{2,100})\.\s+(?P<promoter>[^.]{2,100})\.",
    )
)
