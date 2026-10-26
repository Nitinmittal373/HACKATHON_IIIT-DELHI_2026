"""Reading labelled facts out of the text of a portal page or a search snippet.

Portals label the same fact in different words ("Project End Date", "Proposed Date of
Completion"), and search snippets cut pages at random, so every value is optional and a value
that looks cut off ("Gaursons Promoters Private ...") is never trusted.
"""

import re
from collections.abc import Sequence
from datetime import date, datetime, timedelta, timezone
from typing import Protocol


class _Named(Protocol):
    name: str | None
    promoter: str | None


IST = timezone(timedelta(hours=5, minutes=30))  # records are dated in Indian time

DASHES = str.maketrans({"‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-"})
DATE = (
    r"(?:[A-Za-z]{3},? )?"
    r"(?:\d{1,2}[/.-]\d{1,2}[/.-]\d{4}"
    r"|\d{1,2}(?:st|nd|rd|th)?[ -][A-Za-z]{3,9}[ ,-]+\d{4}"
    r"|[A-Za-z]{3,9} \d{1,2},? (?:\d{2}:\d{2}:\d{2} [A-Z]{2,4} )?\d{4}"
    r"|\d{4}-\d{2}-\d{2})"
)
DATE_FORMATS = (
    "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d-%b-%Y", "%d %b %Y", "%d %B %Y",
    "%d-%B-%Y", "%b %d %Y", "%B %d %Y", "%Y-%m-%d",
)  # fmt: skip
# Where a value ends: the next field of a snippet, a table cell or a sentence.
END = r"(?=\s*(?:;|\||\n|·|\s{2,}|\.\s|\s\.\.\.|$))"

REGISTERED_LABELS = (
    "Date of Registration",
    "Registration Date",
    "Approval Date",
    "Registered on",
    "commencing from",
)
PROMISED_LABELS = (
    "Proposed Date of Completion",
    "Proposed Completion Date",
    "Project Completion Date",
    "Project End Date",
    "Date of Completion",
    "ending with",
)
REVISED_LABELS = (
    "Revised Date of Completion",
    "Revised Completion Date",
    "Extension Completion Date",
)
NAME_LABELS = ("Project Name", "Name of Project")
PROMOTER_LABELS = (
    "Promoter Name",
    "Name of the Promoter",
    "Developer Name",
    r"Promoter(?=\s*[:\-])",
)
DISTRICT_LABELS = ("District",)
STATUS_LABELS = ("Project Status", "Current Status")


def clean(text: str) -> str:
    """Plain dashes and single spaces, so a number matches however the page spelled it."""
    return re.sub(r"[ \t\r\f\v]+", " ", text.translate(DASHES)).strip()


def squash(text: str) -> str:
    """Only letters and digits, upper case: how two spellings of a number are compared."""
    return re.sub(r"[^A-Z0-9]", "", text.translate(DASHES).upper())


def parse_date(text: str | None) -> date | None:
    if not text:
        return None
    text = re.sub(r"^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,? ", "", text.strip())  # a weekday
    text = re.sub(r"\d{2}:\d{2}:\d{2} [A-Z]{2,4} ", "", text).replace(",", "")
    text = re.sub(r"^(\d{1,2})(?:st|nd|rd|th) ", r"\1 ", text)
    for pattern in DATE_FORMATS:
        try:
            return datetime.strptime(text, pattern).date()
        except ValueError:
            continue
    return None


def labelled_date(text: str, labels: tuple[str, ...]) -> date | None:
    found = re.search(rf"(?:{'|'.join(labels)})\s*[:.\-]?\s*({DATE})", text, re.IGNORECASE)
    return parse_date(found.group(1)) if found else None


def labelled_text(text: str, labels: tuple[str, ...]) -> str | None:
    pattern = rf"(?:{'|'.join(labels)})\s*[:.\-]?\s*(?P<value>[^;|\n·]{{2,120}}?){END}"
    found = re.search(pattern, text, re.IGNORECASE)
    if found is None:
        return None
    value = found.group("value").strip(" .,:")
    # A value cut off by the search engine is not trusted.
    if text[found.end() :].lstrip().startswith("...") or value.lower() in {"na", "n/a", "-"}:
        return None
    return value or None


def id_segments(text: str, patterns: list[re.Pattern[str]]) -> list[tuple[str, str]]:
    """Each registration number in the text with the words after it, up to the next number.

    A listing prints many projects in one snippet; this keeps one project's words apart.
    """
    found = sorted(
        {(m.start(), m.group(0)) for pattern in patterns for m in pattern.finditer(text)},
    )
    segments = []
    for index, (start, rera_id) in enumerate(found):
        end = found[index + 1][0] if index + 1 < len(found) else len(text)
        segments.append((rera_id, text[start:end]))
    return segments


# Words that do not tell one project from another.
COMMON_WORDS = {"rera", "project", "projects", "phase", "the", "and", "by", "of", "in"}


def _words(text: str) -> set[str]:
    words = re.split(r"[^a-z0-9]+", text.lower())
    return {w for w in words if len(w) > 1 and w not in COMMON_WORDS}


def distinctive_words(text: str) -> set[str]:
    """The words of a project name that tell it from other projects."""
    return _words(text)


def rank[T: _Named](candidates: Sequence[T], query: str) -> list[T]:
    """Projects whose name or promoter holds more of the query's words come first."""

    def overlap(project: T) -> int:
        return len(_words(query) & _words(f"{project.name or ''} {project.promoter or ''}"))

    return sorted(candidates, key=overlap, reverse=True)
