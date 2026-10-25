from app.sources.base import Source
from app.sources.insolvency import InsolvencySource
from app.sources.pending import NotConnected
from app.sources.registry import RegistrySource
from app.sources.uprera import UpreraSource


def build_sources() -> list[Source]:
    """UP-RERA first: it confirms the project and names the promoter for the others."""
    return [
        UpreraSource(),
        RegistrySource(),
        InsolvencySource(),
        NotConnected("land", ("land_dues",)),
        NotConnected("consumer", ("consumer_cases",)),
        NotConnected("news", ()),
    ]
