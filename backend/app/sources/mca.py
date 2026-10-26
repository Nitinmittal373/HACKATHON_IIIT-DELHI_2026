"""A company's public profile on an MCA mirror (Tofler): directors, charges, related companies.

Pure parsing of the text Fetch returns. Only what a buyer needs is kept: a director's name and
DIN (not addresses, phones or PAN), when charges were registered, and the names of related
companies. The page is used only when it names exactly the promoter's legal company.
"""

import re
from dataclasses import dataclass
from datetime import date, datetime

from app.matching import legal_name_in, normalize

DIRECTOR_ROW = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(\d{8})\s*\|", re.MULTILINE)
CHARGE_DATE = re.compile(r"Charge Date\s*:\s*(\d{1,2} [A-Za-z]{3}, \d{4})")
PAGE_NAME = re.compile(r"The CIN number of (.+?) is [A-Z0-9]{21}")
RELATED_HEADER = re.compile(r"^\|\s*Name\s*\|\s*State / Country\s*\|\s*Incorporation Year", re.M)
# Tofler marks a shareholding director by appending this to the name.
NAME_SUFFIX = re.compile(r"\s+Shareholder$")


@dataclass(frozen=True)
class Director:
    name: str
    din: str
    designation: str


@dataclass(frozen=True)
class CompanyProfile:
    legal_name: str | None
    directors: tuple[Director, ...]
    charge_dates: tuple[date, ...]
    related_companies: tuple[str, ...]


def parse_profile(text: str) -> CompanyProfile:
    name = PAGE_NAME.search(text)
    return CompanyProfile(
        legal_name=name.group(1).strip() if name else None,
        directors=tuple(
            Director(NAME_SUFFIX.sub("", m.group(2)), m.group(3), m.group(1))
            for m in DIRECTOR_ROW.finditer(text)
        ),
        charge_dates=tuple(d for raw in CHARGE_DATE.findall(text) if (d := _day(raw))),
        related_companies=_related(text),
    )


def is_this_company(profile: CompanyProfile, promoter: str | None) -> bool:
    return legal_name_in(promoter, normalize(profile.legal_name))


def _related(text: str) -> tuple[str, ...]:
    header = RELATED_HEADER.search(text)
    if header is None:
        return ()
    names: list[str] = []
    for line in text[header.end() :].splitlines()[1:]:
        if not line.startswith("|"):
            if names:
                break
            continue
        cell = line.strip("|").split("|")[0].strip()
        if cell and not cell.startswith("---"):
            names.append(cell)
    return tuple(names)


def _day(raw: str) -> date | None:
    try:
        return datetime.strptime(raw, "%d %b, %Y").date()
    except ValueError:
        return None
