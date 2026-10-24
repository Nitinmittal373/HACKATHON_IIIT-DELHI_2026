"""Entity matching. A wrong-company claim is worse than no claim, so matching is strict.

- Official records must contain the promoter's full legal name ("supertech limited"),
  not just a brand word ("supertech" also matches "Supertech Realtors").
- Project names must match whole tokens, so "Eco Village I" never matches "Eco Village II".
"""
from __future__ import annotations

import re

_SUFFIXES = [
    (r"\bpvt\b\.?", "private"), (r"\bltd\b\.?", "limited"), (r"\bco\b\.?", "company"),
    (r"\bcorpn?\b\.?", "corporation"), (r"&", " and "),
]
_GENERIC = r"\b(private|limited|llp|india|infra(structure)?s?|developers?|builders?|company|and|the)\b"


def normalize(text: str | None) -> str:
    """Lower case, expand legal suffixes, flatten punctuation: 'Supertech Ltd.' -> 'supertech limited'."""
    t = (text or "").lower()
    for pat, rep in _SUFFIXES:
        t = re.sub(pat, rep, t)
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def blob(hit: dict) -> str:
    """Normalized title + url + snippet of a search hit."""
    return normalize(f"{hit.get('title', '')} {hit.get('url', '')} {hit.get('snippet', '')}")


def legal_name_in(name: str | None, text_norm: str) -> bool:
    """Exact legal-name match on whole words: 'supertech limited' in '... supertech limited ...'."""
    n = normalize(name)
    return bool(n) and re.search(rf"\b{re.escape(n)}\b", text_norm) is not None


_HONORIFICS = {"m", "s", "ms", "mr", "mrs", "shri", "sri", "smt", "new", "the", "a", "to"}


def brand(name: str | None) -> str:
    """'Jaypee Infratech Private Limited' -> 'jaypee'; 'M/s Mr Proview Realtech Pvt Ltd' -> 'proview'.

    Used only for weak signals (news), never for hard stops. Short or generic words are skipped,
    so a brand like 'mr' can never match half the internet.
    """
    n = re.sub(_GENERIC, " ", normalize(name))
    words = [w for w in n.split() if w not in _HONORIFICS and len(w) >= 3 and not w.isdigit()]
    return words[0] if words else ""


def has_word(word: str, text_norm: str) -> bool:
    """Whole-word match: 'ats' matches 'ats greens' but not 'stats'."""
    return bool(word) and re.search(rf"\b{re.escape(word)}\b", text_norm) is not None


def looks_like_rera_number(text: str | None) -> bool:
    return bool(re.search(r"\bup ?rera ?prj ?\d+", normalize(text)))


def project_pattern(project: str | None, promoter: str | None = None) -> re.Pattern | None:
    """Regex for a project's distinguishing name, whole tokens only.

    'SUPERTECH ECO VILLAGE-I PHASE I-C' with promoter 'SUPERTECH LIMITED' -> r'\\beco\\W+village\\W+i\\b'
    """
    n = normalize(project)
    if not n:
        return None
    b = brand(promoter)
    if b:
        n = re.sub(rf"^{re.escape(b)}\s+", "", n)
    n = re.split(r"\b(phase|tower|block|wing|sector)\b", n)[0].strip()
    tokens = n.split()
    if not tokens:
        return None
    return re.compile(r"\b" + r"\W+".join(re.escape(t) for t in tokens) + r"\b")


def dedupe_titles(hits: list[dict]) -> list[dict]:
    """One story repeated by several outlets counts once (avoid double counting)."""
    seen: set[str] = set()
    out = []
    for h in hits:
        title = re.split(r"\s[-|–]\s", h.get("title") or "")[0]      # drop " - Outlet name" suffixes
        key = " ".join(normalize(title).split()[:8])
        if key and key not in seen:
            seen.add(key)
            out.append(h)
    return out
