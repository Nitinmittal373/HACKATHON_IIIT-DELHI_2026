"""Every state adapter, and how a buyer's text finds the right one."""

from app.states import (
    ap,
    assam,
    br,
    cg,
    dl,
    ga,
    gj,
    hp,
    hr,
    jh,
    jk,
    ka,
    kl,
    mh,
    mp,
    od,
    pb,
    rj,
    tg,
    tn,
    uk,
    up,
    wb,
)
from app.states.base import StateAdapter
from app.states.names import DEFAULT_STATE

# UP first: its numbers are the most specific, and old UP checks have no other state.
ADAPTERS: tuple[StateAdapter, ...] = (
    up.ADAPTER,
    mh.ADAPTER,
    hr.ADAPTER,
    ka.ADAPTER,
    dl.ADAPTER,
    tg.ADAPTER,
    gj.ADAPTER,
    tn.ADAPTER,
    rj.ADAPTER,
    mp.ADAPTER,
    wb.ADAPTER,
    pb.ADAPTER,
    kl.ADAPTER,
    ap.ADAPTER,
    uk.ADAPTER,
    br.ADAPTER,
    od.ADAPTER,
    ga.ADAPTER,
    cg.ADAPTER,
    hp.ADAPTER,
    jh.ADAPTER,
    assam.ADAPTER,
    jk.ADAPTER,
)
BY_CODE: dict[str, StateAdapter] = {adapter.code: adapter for adapter in ADAPTERS}


def adapter_for(code: str) -> StateAdapter:
    """The adapter of a state code; an unknown code is a programming error, not user input."""
    return BY_CODE[code]


def known_state(code: str | None) -> bool:
    return code in BY_CODE


def detect_state(query: str) -> tuple[StateAdapter, float] | None:
    """The state whose number format the text matches best, or None when it is not a number."""
    scored = [(adapter, adapter.detect(query)) for adapter in ADAPTERS]
    best = max(scored, key=lambda pair: pair[1])
    return best if best[1] > 0 else None


def state_of(rera_id: str) -> str:
    """The state of a stored number; numbers that fit no format are old UP checks."""
    found = detect_state(rera_id)
    return found[0].code if found else DEFAULT_STATE
