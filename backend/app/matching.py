"""Entity matching. A claim about the wrong company is worse than no claim, so it is strict.

- A company page counts only when it holds the promoter's full legal name
  ("supertech limited"); the brand word alone also matches "Supertech Realtors".
- A project counts only when its distinguishing words match as whole tokens,
  so "Eco Village-I" never matches "Eco Village-II", and "Eco Village-1" does.
"""

import re

from app.tinyfish import SearchHit

LEGAL_SUFFIXES = [
    (r"\bpvt\b\.?", "private"),
    (r"\bltd\b\.?", "limited"),
    (r"\bco\b\.?", "company"),
    (r"\bcorpn?\b\.?", "corporation"),
    (r"&", " and "),
]
GENERIC_WORDS = re.compile(
    r"\b(private|limited|llp|india|infra(structure)?s?|developers?|builders?|company|and|the)\b"
)
HONORIFICS = {"m", "s", "ms", "mr", "mrs", "shri", "sri", "smt", "new", "the", "a", "to"}
# Where a project's name stops being distinctive: "... Eco Village-I Phase I-C".
PROJECT_NAME_END = re.compile(r"\b(phase|tower|block|wing|sector)\b")
ROMAN_NUMBERS = {
    "i": "1",
    "ii": "2",
    "iii": "3",
    "iv": "4",
    "v": "5",
    "vi": "6",
    "vii": "7",
    "viii": "8",
    "ix": "9",
    "x": "10",
}


def normalize(text: str | None) -> str:
    """Lower case, spell out legal suffixes, flatten punctuation.

    'Supertech Ltd.' -> 'supertech limited'
    """
    lowered = (text or "").lower()
    for pattern, replacement in LEGAL_SUFFIXES:
        lowered = re.sub(pattern, replacement, lowered)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", lowered)).strip()


def canonical(text: str | None) -> str:
    """Normalized text with roman numerals as digits, for comparing project names."""
    return " ".join(ROMAN_NUMBERS.get(word, word) for word in normalize(text).split())


def blob(hit: SearchHit) -> str:
    """Normalized title, address and snippet of a search hit."""
    return normalize(f"{hit.title} {hit.url} {hit.snippet}")


def legal_name_in(name: str | None, normalized_text: str) -> bool:
    """The exact legal name, on whole words, inside already-normalized text."""
    wanted = normalize(name)
    return bool(wanted) and re.search(rf"\b{re.escape(wanted)}\b", normalized_text) is not None


def brand(name: str | None) -> str:
    """The first distinctive word of a company name.

    'Jaypee Infratech Private Limited' -> 'jaypee'; 'M/s Mr Proview Realtech Pvt Ltd' -> 'proview'.
    Short or generic words are skipped, so "mr" can never match half the internet.
    """
    words = GENERIC_WORDS.sub(" ", normalize(name)).split()
    for word in words:
        if word not in HONORIFICS and len(word) >= 3 and not word.isdigit():
            return word
    return ""


def project_pattern(project: str | None, promoter: str | None = None) -> re.Pattern[str] | None:
    """Regex for a project's distinguishing name, whole tokens only, over canonical() text.

    'SUPERTECH ECO VILLAGE-I PHASE I-C' by 'SUPERTECH LIMITED' -> r'\\beco\\W+village\\W+1\\b'
    """
    name = canonical(project)
    if not name:
        return None
    promoter_brand = brand(promoter)
    if promoter_brand:
        name = re.sub(rf"^{re.escape(promoter_brand)}\s+", "", name)
    tokens = PROJECT_NAME_END.split(name)[0].split()
    if not tokens:
        return None
    return re.compile(r"\b" + r"\W+".join(re.escape(token) for token in tokens) + r"\b")


def has_word(word: str, text: str | None) -> bool:
    """Whole-word match: 'ats' is in 'ATS Greens' but not in 'stats'."""
    return bool(word) and re.search(rf"{re.escape(word)}", normalize(text)) is not None


def mentions_project(pattern: re.Pattern[str] | None, text: str | None) -> bool:
    return pattern is not None and pattern.search(canonical(text)) is not None


def dedupe_titles(hits: list[SearchHit]) -> list[SearchHit]:
    """One story repeated by several outlets counts once."""
    seen: set[str] = set()
    unique = []
    for hit in hits:
        headline = re.split(r"\s[-|–]\s", hit.title)[0]  # drop " - Outlet name" suffixes
        key = " ".join(normalize(headline).split()[:8])
        if key and key not in seen:
            seen.add(key)
            unique.append(hit)
    return unique
