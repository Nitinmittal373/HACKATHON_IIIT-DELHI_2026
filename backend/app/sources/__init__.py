from app.sources.base import Source
from app.sources.pending import NotConnected
from app.sources.uprera import UpreraSource


def build_sources() -> list[Source]:
    """UP-RERA first: it confirms the project and names the promoter for the others."""
    return [
        UpreraSource(),
        NotConnected("registry", ("company_status",)),
        NotConnected("insolvency", ("insolvency",)),
        NotConnected("land", ("land_dues",)),
        NotConnected("consumer", ("consumer_cases",)),
        NotConnected("news", ()),
    ]
