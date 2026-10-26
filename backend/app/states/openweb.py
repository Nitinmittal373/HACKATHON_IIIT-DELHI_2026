"""Find a project's RERA number anywhere on the public web, then vote on what was found.

A state portal that Search cannot read still has its project's number printed by the builder,
by listing sites and sometimes by the authority's own certificate pages. So Search runs with no
domain limit, every state's number format is looked for in the results, and each number is
scored by who prints it:

- +3 when a page of that state's RERA domain prints it,
- +2 when the builder's own site does (its domain holds the brand word of the query),
- +1 for every other distinct domain.

A number is kept when it scores 3 or more, or when two different domains print it, and at
least one of them prints it next to the project's name. A number printed beside a different
project's name (a listing of many projects) does not count for the one asked about.
Listing sites are only a way to find the number; the report never scores their words.
"""

import asyncio
import re
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from app.models import Project
from app.states.places import without_places
from app.states.registry import ADAPTERS
from app.states.text import clean, distinctive_words, squash
from app.tinyfish import SearchHit, WebClient

# Four wordings, because Search answers each with different pages: a builder's page prints the
# number under "registration number", a listing's FAQ under "What is the RERA number of ...".
SEARCH_TEMPLATES = (
    "{q} RERA registration number",
    "{q} RERA",
    "{q} RERA number",
    "What is the RERA number of {q}",
)
SEARCH_PURPOSE = "Find the RERA registration number of a project a homebuyer named, on the open web"
CACHE_SECONDS = 24 * 3600
# How far from a number its project's name may stand and still be "next to" it.
WINDOW = 160
# The share of a query's distinctive words that must stand near a number.
NAME_SHARE = 0.75
SCORE_TO_KEEP = 3
STATE_POINTS, BUILDER_POINTS, OTHER_POINTS = 3, 2, 1
MAX_CANDIDATES = 8

# Words of the page, not of the project: "Real Estate" must not make "Golf Estate" match.
NOISE = re.compile(r"RERA\s*ACK\w*|Real Estate Regulatory Authority", re.IGNORECASE)
# MahaRERA numbers are copied with spaces ("P 51900 008345") by some listings.
SPACED_MAHARERA = re.compile(r"\bP[\s-]?[1-9](?:[\s-]?\d){10}\b")
TITLE_SPLIT = re.compile(r"\s+[-|–—]\s+|\s*,\s+|\s+in\s+", re.IGNORECASE)


class SearchCache:
    """Search answers kept for a day, so a repeated name does not spend the rate limit."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._kept: dict[str, tuple[float, list[SearchHit]]] = {}

    def get(self, query: str) -> list[SearchHit] | None:
        kept = self._kept.get(query)
        if kept is None or self._clock() - kept[0] > CACHE_SECONDS:
            return None
        return kept[1]

    def put(self, query: str, hits: list[SearchHit]) -> None:
        self._kept[query] = (self._clock(), hits)

    def clear(self) -> None:
        self._kept.clear()


CACHE = SearchCache()


@dataclass
class Votes:
    """Everything the search results say about one number."""

    state: str
    rera_id: str
    # domain -> points it earned; a domain counts once, at its best role.
    domains: dict[str, int] = field(default_factory=dict)
    named: bool = False
    on_portal: bool = False
    titles: list[str] = field(default_factory=list)

    @property
    def score(self) -> int:
        return sum(self.domains.values())

    def kept(self) -> bool:
        return self.named and (self.score >= SCORE_TO_KEEP or len(self.domains) >= 2)


async def search_open_web(query: str, web: WebClient, cache: SearchCache = CACHE) -> list[Project]:
    return candidates_from(await open_web_hits(query, web, cache), query)


async def open_web_hits(query: str, web: WebClient, cache: SearchCache = CACHE) -> list[SearchHit]:
    texts = [template.format(q=query) for template in SEARCH_TEMPLATES]
    groups = await asyncio.gather(*(cached_search(text, web, cache) for text in texts))
    return [hit for group in groups for hit in group]


async def cached_search(
    text: str, web: WebClient, cache: SearchCache = CACHE, domains: str | None = None
) -> list[SearchHit]:
    """One Search, remembered for a day under its text and the domains it was limited to."""
    key = f"{text} @{domains}" if domains else text
    if (kept := cache.get(key)) is not None:
        return kept
    hits = await web.search(text, purpose=SEARCH_PURPOSE, include_domains=domains)
    cache.put(key, hits)
    return hits


def candidates_from(hits: Iterable[SearchHit], query: str) -> list[Project]:
    """The numbers the votes keep, best first, as candidates that name where they were seen."""
    votes = tally(hits, query)
    kept = sorted((v for v in votes.values() if v.kept()), key=lambda v: -v.score)
    return [project_of(v, query) for v in kept[:MAX_CANDIDATES]]


def name_words(query: str) -> set[str]:
    """The query's distinctive words without its city, which a page may not repeat."""
    return distinctive_words(without_places(query)) or distinctive_words(query)


def tally(hits: Iterable[SearchHit], query: str) -> dict[str, Votes]:
    words = name_words(query)
    brands = brand_tokens(query)
    votes: dict[str, Votes] = {}
    for hit in hits:
        domain = domain_of(hit.url)
        text = prepare(f"{hit.title}. {hit.snippet}")
        found = numbers_in(text)
        for index, (state, rera_id, _, _) in enumerate(found):
            vote = votes.setdefault(squash(rera_id), Votes(state=state, rera_id=rera_id))
            on_portal = on_state_domain(state, domain)
            vote.domains[domain] = max(
                vote.domains.get(domain, 0), points_for(on_portal, domain, brands)
            )
            vote.on_portal = vote.on_portal or on_portal
            if names_project(text, found, index, words, hit):
                vote.named = True
                vote.titles.append(hit.title)
    return votes


def points_for(on_portal: bool, domain: str, brands: set[str]) -> int:
    if on_portal:
        return STATE_POINTS
    if any(brand in domain for brand in brands):
        return BUILDER_POINTS
    return OTHER_POINTS


def prepare(text: str) -> str:
    text = NOISE.sub(" ", clean(text))
    return SPACED_MAHARERA.sub(lambda m: re.sub(r"[\s-]", "", m.group(0)), text)


def numbers_in(text: str) -> list[tuple[str, str, int, int]]:
    """(state, number, start, end) of every registration number in the text."""
    found: dict[tuple[int, int], tuple[str, str]] = {}
    for adapter in ADAPTERS:
        for pattern in adapter.id_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                if plausible(match.group(0), text, match.start()):
                    found.setdefault(match.span(), (adapter.code, match.group(0).upper()))
    # Of two numbers that overlap, the longer one is the real number.
    kept: list[tuple[int, int]] = []
    for span in sorted(found, key=lambda s: s[0] - s[1]):
        if not any(span[0] < other[1] and other[0] < span[1] for other in kept):
            kept.append(span)
    return [(*found[span], *span) for span in sorted(kept)]


def plausible(number: str, text: str, start: int) -> bool:
    """Plain digit formats ("112 of 2021") also fit phrases, so they need 'RERA' beside them."""
    if not number[0].isdigit():
        return True
    return "RERA" in text[max(0, start - 40) : start + 60].upper()


def names_project(
    text: str,
    found: list[tuple[str, str, int, int]],
    index: int,
    words: set[str],
    hit: SearchHit,
) -> bool:
    """Whether this number stands next to the project's name, or the page is about only it.

    The words around a number stop at the neighbouring numbers, so a list of projects gives
    each number only its own project's words.
    """
    if not words:
        return True
    _, _, start, end = found[index]
    before = found[index - 1][3] if index > 0 else 0
    after = found[index + 1][2] if index + 1 < len(found) else len(text)
    near = text[max(before, start - WINDOW) : min(after, end + WINDOW)].lower()
    if share_of(words, near) >= NAME_SHARE:
        return True
    return len(found) == 1 and share_of(words, f"{hit.title} {hit.url}".lower()) >= NAME_SHARE


def share_of(words: set[str], text: str) -> float:
    """The share of the words the text holds as whole words; a plural counts, "Woodscapes" does not.

    Names are spelled apart or together ("My Wood", "Mywoods", "Golf Estate", "Golfestate"), so two
    neighbouring words, or one word made only of the query's words, hold them too.
    """
    raw = re.findall(r"[a-z0-9]+", text.lower())
    stems = {_stem(word): word for word in words}
    tokens = {_stem(token) for token in raw} | {
        _stem(a + b) for a, b in zip(raw, raw[1:], strict=False)
    }
    present = {word for stem, word in stems.items() if stem in tokens}
    for token in raw:
        present |= {stems[stem] for stem in _joined(token, set(stems))}
    return len(present) / len(words)


def _stem(word: str) -> str:
    return word[:-1] if len(word) > 4 and word.endswith("s") else word


def _joined(token: str, stems: set[str]) -> set[str]:
    """The stems a token is made of when it is nothing but those stems written together."""
    for stem in stems:
        if token == stem:
            return set()  # one whole word: already counted
        if token.startswith(stem):
            rest = _joined_all(token[len(stem) :], stems)
            if rest is not None:
                return {stem} | rest
    return set()


def _joined_all(token: str, stems: set[str]) -> set[str] | None:
    if not token:
        return set()
    for stem in stems:
        if token.startswith(stem):
            rest = _joined_all(token[len(stem) :], stems)
            if rest is not None:
                return {stem} | rest
    return None


def brand_tokens(query: str) -> set[str]:
    """The builder's name as it would appear in its domain: the first word, or the first two."""
    words = [w for w in re.split(r"[^a-z0-9]+", query.lower()) if w]
    tokens = set()
    if words and len(words[0]) >= 3:
        tokens.add(words[0])
    if len(words) > 1 and len(words[0] + words[1]) >= 5:
        tokens.add(words[0] + words[1])
    return tokens


def domain_of(url: str) -> str:
    return (urlsplit(url).hostname or "").lower().removeprefix("www.")


def on_state_domain(state: str, domain: str) -> bool:
    adapter = next(a for a in ADAPTERS if a.code == state)
    return any(domain == d or domain.endswith("." + d) for d in adapter.domains)


def project_of(vote: Votes, query: str) -> Project:
    adapter = next(a for a in ADAPTERS if a.code == vote.state)
    probe = Project(state=vote.state, rera_id=vote.rera_id, details_url="")
    return Project(
        state=vote.state,
        rera_id=vote.rera_id,
        name=name_from(vote.titles, query),
        details_url=adapter.details_url(probe),
        status="confirmed" if vote.on_portal else "listings_only",
        sources=sorted(vote.domains, key=lambda d: (-vote.domains[d], d)),
    )


def name_from(titles: list[str], query: str) -> str | None:
    """The part of a page title that is the project's name: the shortest with most query words."""
    words = name_words(query)
    parts = {
        part.strip(" .:")
        for title in titles
        for part in TITLE_SPLIT.split(clean(title))
        if 3 <= len(part.strip(" .:")) <= 70
    }
    scored = [(-len(words & distinctive_words(part)), len(part), part) for part in parts]
    scored = [item for item in scored if item[0] < 0]
    return min(scored)[2] if scored else None


def hits_by_state(hits: list[SearchHit]) -> dict[str, list[SearchHit]]:
    grouped: dict[str, list[SearchHit]] = {}
    for hit in hits:
        host = domain_of(hit.url)
        for adapter in ADAPTERS:
            if any(host == d or host.endswith("." + d) for d in adapter.domains):
                grouped.setdefault(adapter.code, []).append(hit)
                break
    return grouped
