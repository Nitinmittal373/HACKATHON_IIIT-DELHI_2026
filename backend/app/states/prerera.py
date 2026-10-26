"""Projects that public pages say were finished before RERA, so there is no number to find.

Listing sites answer "what is the RERA number of X" with "X does not apply to RERA and has
already been delivered". That sentence is not a finding about the project: it only tells us to
stop looking for a project number and to check the builder instead. The card shows the sentence
and its page, so the buyer can read it too.
"""

import re
from collections.abc import Iterable

from app.models import PreReraNote
from app.states.openweb import NAME_SHARE, name_from, name_words, share_of
from app.states.text import clean
from app.tinyfish import SearchHit

# The sentences listings use. Each says the project is outside RERA, not that it is unsafe.
BEFORE_RERA = re.compile(
    r"(?:does not|doesn't|do not|did not)\s+(?:apply|require|need|come under)[^.]{0,40}RERA"
    r"|RERA\s+(?:is\s+)?not\s+applicable|not\s+(?:applicable|required)\s+(?:to|for|under)\s+RERA"
    r"|(?:delivered|completed|handed over|occupied)[^.]{0,40}before\s+RERA"
    r"|before\s+RERA\s+(?:came|was|act)",
    re.IGNORECASE,
)
SENTENCE_END = re.compile(r"(?<=[.?!])\s")
MAX_NOTES = 2


def pre_rera_notes(hits: Iterable[SearchHit], query: str) -> list[PreReraNote]:
    """One note per page that says, next to the project's name, that RERA does not apply."""
    words = name_words(query)
    notes: list[PreReraNote] = []
    for hit in hits:
        text = clean(f"{hit.title}. {hit.snippet}")
        found = BEFORE_RERA.search(text)
        if found is None or share_of(words, text.lower()) < NAME_SHARE:
            continue
        notes.append(
            PreReraNote(
                name=name_from([hit.title], query) or query.strip(),
                statement=sentence_around(text, found.start())[:300],
                source_url=hit.url,
            )
        )
    return list({note.source_url: note for note in notes}.values())[:MAX_NOTES]


def sentence_around(text: str, position: int) -> str:
    start = 0
    for end in SENTENCE_END.finditer(text):
        if end.end() > position:
            return text[start : end.start() + 1].strip()
        start = end.end()
    return text[start:].strip()
