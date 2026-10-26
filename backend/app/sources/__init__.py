from app.sources.base import Source
from app.sources.consumer import ConsumerSource
from app.sources.group import GroupSource
from app.sources.insolvency import InsolvencySource
from app.sources.land import LandSource
from app.sources.news import NewsSource
from app.sources.registry import RegistrySource
from app.sources.uprera import UpreraSource


def build_sources(v2: bool = False) -> list[Source]:
    """UP-RERA first: it confirms the project and names the promoter for the others."""
    sources: list[Source] = [
        UpreraSource(),
        RegistrySource(),
        InsolvencySource(),
        LandSource(),
        ConsumerSource(),
        NewsSource(),
    ]
    if v2:
        sources.insert(2, GroupSource())
    return sources
