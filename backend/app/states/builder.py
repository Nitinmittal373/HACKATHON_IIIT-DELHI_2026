"""Name the builder of a project whose UP-RERA page did not show one.

A Search snippet often leaves out the promoter. Without a name the company registry,
insolvency, group and news sources have nothing to look up. So one more free Search runs
for the exact registration number, with no domain limit, and a name counts only when it
stands next to that exact number in at least two different results. The name is used to
identify the builder and is stored as a "secondary"
identity; it is never a scored finding, and the report asks the buyer to verify it on
UP-RERA.
"""

import re
from collections import defaultdict
from dataclasses import dataclass

from app.matching import normalize
from app.states.text import clean, squash
from app.tinyfish import SearchHit, WebClient

PURPOSE = "Find the builder named next to one RERA registration number on public listings"
MIN_RESULTS = 2
# How far from the number a name may stand and still be "next to" it.
WINDOW = 220

LEGAL_SUFFIX = r"(?:Pvt\.? ?Ltd\.?|Private Limited|Limited|Ltd\.?|LLP|LLC)"
NAME_CHARS = r"[A-Z][A-Za-z0-9&'\-]*(?: (?:and |& |of |the )?[A-Z][A-Za-z0-9&'\-]*){0,6}"
# "Promoter: X", "Builder - X", "Developed by X", "by X": the label says it is the builder.
LABELLED = re.compile(
    rf"(?:Promoter(?: Name)?|Developer(?: Name)?|Builder|Developed by|Promoted by|Company)"
    rf"\s*[:\-,]?\s*(?:M/s\.? )?(?P<name>{NAME_CHARS})"
)
BY = re.compile(rf"\bby\s+(?:M/s\.? )?(?P<name>{NAME_CHARS})")
LEGAL = re.compile(rf"(?:M/s\.? )?(?P<name>{NAME_CHARS}\s{LEGAL_SUFFIX})")
# Words that mean the text names an authority, a site or a sentence, not a builder.
NOT_A_BUILDER = re.compile(
    r"\b(rera|regulatory|authority|government|"
    r"terms|conditions|privacy|registration|read more|starting|possession|price|bhk|sq ft|"
    r"homebuyers?|allottees?|project|properties for|listing|sale|rent|yes|no)\b",
    re.IGNORECASE,
)
TRAILING = re.compile(r"\s+(?:in|at|on|for|with|is|are|and|the|starting|from)$", re.IGNORECASE)


@dataclass(frozen=True)
class BuilderIdentity:
    name: str
    # The listings that print the name next to the number, with the words around it.
    sources: tuple[tuple[str, str], ...]


async def identify_builder(rera_id: str, web: WebClient) -> BuilderIdentity | None:
    hits = await web.search(f'"{rera_id}"', purpose=PURPOSE)
    return builder_in(rera_id, hits)


def builder_in(rera_id: str, hits: list[SearchHit]) -> BuilderIdentity | None:
    """The one name that at least two different results print next to this exact number."""
    seen: dict[str, dict[str, tuple[str, str]]] = defaultdict(dict)
    shown: dict[str, str] = {}
    for hit in hits:
        text = clean(f"{hit.title}. {hit.snippet}")
        near = _window(text, rera_id)
        if near is None:
            continue
        for name in _names(near):
            key = normalize(name)
            shown.setdefault(key, name)
            seen[key].setdefault(hit.url, (hit.url, near[:300]))
    agreed = {key: found for key, found in seen.items() if len(found) >= MIN_RESULTS}
    # Two different names both agreed by two results is a conflict, so nobody is named.
    if len(agreed) != 1:
        return None
    [(key, found)] = agreed.items()
    return BuilderIdentity(name=shown[key], sources=tuple(found.values()))


def _window(text: str, rera_id: str) -> str | None:
    """The text around the exact number, or None when this result does not print it."""
    # The number as listings print it: separators may differ, the letters and digits may not.
    parts = re.findall(r"[A-Za-z0-9]", squash(rera_id))
    found = re.search(r"[^A-Za-z0-9]{0,2}".join(parts), text, re.IGNORECASE)
    if found is None:
        return None
    return text[max(0, found.start() - WINDOW) : found.end() + WINDOW]


def _names(text: str) -> list[str]:
    names = []
    for pattern in (LABELLED, BY, LEGAL):
        for match in pattern.finditer(text):
            name = TRAILING.sub("", match.group("name")).strip(" .,:-")
            if 3 <= len(name) <= 70 and not NOT_A_BUILDER.search(name):
                names.append(name)
    return list(dict.fromkeys(names))
