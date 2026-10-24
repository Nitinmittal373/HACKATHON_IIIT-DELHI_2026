"""The investigation lanes. Each lane fills part of `Signals` and adds cited `Evidence`.

Escalation ladder (TinyFish's own advice): Search -> Fetch -> Agent.
Search/Fetch are free and run in parallel; the Agent is used only for UP-RERA and MCA pages.
Lane owners: tune GOALS and keyword lists here after testing each site in the TinyFish playground.
"""
from __future__ import annotations

import re
from datetime import datetime

from . import tf
from .models import Evidence, Signals

UPRERA_HOME = "https://www.up-rera.in/projects"

# ---------------- RERA (agent) ----------------
RERA_SCHEMA = {
    "type": "object",
    "properties": {
        "project_name": {"type": "string"},
        "rera_registration_number": {"type": "string"},
        "promoter_name": {"type": "string"},
        "registration_status": {"type": "string"},
        "promised_completion_date": {"type": "string"},
        "revised_completion_date": {"type": "string"},
        "extensions_count": {"type": "integer"},
        "total_units": {"type": "integer"},
        "quarterly_progress_reports": {"type": "array", "items": {"type": "object", "properties": {
            "quarter": {"type": "string"}, "filed": {"type": "boolean"}}}},
        "complaints_count": {"type": "integer"},
        "penalty_orders_count": {"type": "integer"},
    },
}
RERA_GOAL = (
    "This is a UP-RERA real estate project page. Read the project details and return: "
    "project name, RERA registration number, promoter (builder company) name, registration status, "
    "promised (original) completion date, revised/extended completion date, number of extensions granted, "
    "total units, the list of quarterly progress reports (QPRs) for the last 4 quarters with whether each "
    "was filed, number of complaints and number of penalty orders. If a field is not shown, leave it out. "
    "Write dates as YYYY-MM-DD where possible. Do not guess."
)
RERA_SEARCH_GOAL = (
    "Search UP-RERA registered projects for '{q}'. Open the best matching project's details page and "
    "return the requested fields. If nothing matches, return an empty object."
)


def _parse_date(s: str | None) -> datetime | None:
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d %b %Y", "%d %B %Y", "%b %Y", "%B %Y"):
        try:
            return datetime.strptime(s.strip(), fmt)
        except ValueError:
            continue
    return None


async def resolve_rera_url(query: str) -> str | None:
    """Free Search first: find the project's own UP-RERA summary page from a name or RERA number."""
    hits = await tf.search(f"{query} UP RERA project", include_domains="up-rera.in", limit=10)
    pages = [h for h in hits if any(k in h["url"].lower()
                                    for k in ("projectsummary", "frm_view_project_details"))]
    if not pages:
        return None
    # Prefer the result whose snippet mentions most of the words the user typed
    words = [w for w in re.sub(r"[^a-z0-9 ]", " ", query.lower()).split() if len(w) > 2]
    pages.sort(key=lambda h: sum(w in (h["title"] + " " + h["snippet"]).lower() for w in words),
               reverse=True)
    return pages[0]["url"]


async def rera_lane(query: str, sig: Signals, ev: list[Evidence], ctx: dict, emit) -> None:
    await emit({"lane": "rera", "type": "progress", "message": "Finding the project on UP-RERA (free Search)..."})
    url = await resolve_rera_url(query)
    if url:
        res = await tf.agent("rera", url=url, goal=RERA_GOAL, schema=RERA_SCHEMA, emit=emit)
    else:
        url = UPRERA_HOME
        res = await tf.agent("rera", url=url, goal=RERA_SEARCH_GOAL.format(q=query) + " " + RERA_GOAL,
                             schema=RERA_SCHEMA, emit=emit)
    if not res:
        raise RuntimeError("UP-RERA page could not be read")

    ctx.update(rera_url=url, project_name=res.get("project_name"),
               rera_number=res.get("rera_registration_number"),
               promoter_name=res.get("promoter_name"))
    sig.registration_status = (res.get("registration_status") or "").lower() or None
    sig.extensions_count = res.get("extensions_count")
    sig.total_units = res.get("total_units")
    sig.rera_complaints = res.get("complaints_count")
    sig.rera_penalty_orders = res.get("penalty_orders_count")
    promised, revised = _parse_date(res.get("promised_completion_date")), _parse_date(res.get("revised_completion_date"))
    if promised and revised:
        sig.delay_months = max(0, (revised.year - promised.year) * 12 + revised.month - promised.month)
    qprs = res.get("quarterly_progress_reports") or []
    if qprs:
        sig.qprs_missed_last4 = sum(1 for q in qprs[:4] if q.get("filed") is False)

    snippet = {k: v for k, v in res.items() if v not in (None, "", [])}
    ev.append(Evidence(lane="rera", claim=f"UP-RERA record for {ctx.get('project_name') or query}",
                       source_url=url, snippet=str(snippet)[:1500]))
    if sig.delay_months:
        ev.append(Evidence(lane="rera", source_url=url,
                           claim=f"Completion moved from {res.get('promised_completion_date')} to "
                                 f"{res.get('revised_completion_date')} ({sig.delay_months} months)"))
    if sig.qprs_missed_last4:
        ev.append(Evidence(lane="rera", source_url=url,
                           claim=f"{sig.qprs_missed_last4} of the last 4 quarterly progress reports not filed"))


# ---------------- MCA company (agent on a public company page) ----------------
MCA_SCHEMA = {
    "type": "object",
    "properties": {
        "company_name": {"type": "string"},
        "cin": {"type": "string"},
        "company_status": {"type": "string"},
        "directors": {"type": "array", "items": {"type": "object", "properties": {
            "name": {"type": "string"}, "din": {"type": "string"}}}},
        "open_charges_count": {"type": "integer"},
        "latest_charge_date": {"type": "string"},
        "last_annual_filing_date": {"type": "string"},
    },
}
MCA_GOAL = ("Read this company profile. Return company name, CIN, company status (Active / Strike Off / "
            "Under liquidation etc.), current directors with DIN, number of open charges, date of the latest "
            "charge and date of the last annual filing. Do not guess missing fields.")


async def mca_lane(query: str, sig: Signals, ev: list[Evidence], ctx: dict, emit) -> None:
    promoter = ctx.get("promoter_name")
    if not promoter:
        # Never guess the company: a wrong-company claim in a report is worse than no claim
        raise RuntimeError("Builder company unknown (UP-RERA did not load), so the company check was skipped")
    await emit({"lane": "mca", "type": "progress", "message": f"Looking up company '{promoter}' (free Search)..."})
    hits = await tf.search(f"{promoter} CIN directors", include_domains="zaubacorp.com,tofler.in,qorpiq.com", limit=8)
    core = _core_name(promoter)
    hits = [h for h in hits if core and core in _blob(h)]
    if not hits:
        raise RuntimeError(f"No company page matching '{promoter}' was found")
    url = hits[0]["url"]
    res = await tf.agent("mca", url=url, goal=MCA_GOAL, schema=MCA_SCHEMA, emit=emit, max_seconds=90)
    if not res:
        raise RuntimeError("Company page could not be read")
    ctx["company"] = res
    status = (res.get("company_status") or "").lower()
    sig.company_or_director_struck_off = any(w in status for w in ("strike", "struck", "liquidat", "dissolved"))
    latest = _parse_date(res.get("latest_charge_date"))
    sig.recent_charge_creation = bool(latest and (datetime.now() - latest).days < 365)
    ev.append(Evidence(lane="mca", source_url=url,
                       claim=f"{res.get('company_name') or promoter}: status '{res.get('company_status')}', "
                             f"{len(res.get('directors') or [])} director(s), "
                             f"{res.get('open_charges_count', '?')} open charge(s)",
                       snippet=str(res)[:1500]))


# ---------------- IBBI / NCLT insolvency (free Search + Fetch) ----------------
async def ibbi_lane(query: str, sig: Signals, ev: list[Evidence], ctx: dict, emit) -> None:
    promoter = ctx.get("promoter_name") or query
    core = _core_name(ctx.get("promoter_name")) or _first_word(query)
    await emit({"lane": "ibbi", "type": "progress", "message": f"Checking insolvency records for '{promoter}'..."})
    # 1) Official insolvency sites: a match here counts as the promoter being in CIRP
    official = await tf.search(f'"{promoter}" corporate insolvency resolution process',
                               include_domains="ibbi.gov.in,nclt.gov.in", limit=5)
    off = [h for h in official if core and core in _blob(h)]
    sig.promoter_in_cirp = bool(off)
    for h in off[:3]:
        ev.append(Evidence(lane="ibbi", source_url=h["url"], snippet=h["snippet"][:500],
                           claim=f"Official insolvency record mentions {promoter}: {h['title']}"))
    # 2) News reports of insolvency proceedings: weaker evidence, shown as 'reported, verify'
    news = await tf.search(f'"{core}" NCLT insolvency proceedings', news=True, limit=8,
                           exclude_domains=SOCIAL)
    rep = [h for h in news if core in _blob(h)
           and any(w in _blob(h) for w in ("insolvency", "nclt", "nclat", "cirp"))]
    if rep and not sig.promoter_in_cirp:
        sig.sister_company_in_cirp = True     # penalised less than an official record
    for h in rep[:3]:
        d = f" ({h['date']})" if h.get("date") else ""
        ev.append(Evidence(lane="ibbi", source_url=h["url"], snippet=h["snippet"][:400],
                           claim=f"Reported insolvency proceedings, verify status{d}: {h['title']}"))
    total = len(off) + len(rep)
    await emit({"lane": "ibbi", "type": "progress",
                "message": f"{total} insolvency record(s)/report(s) found" if total else "No insolvency record found"})


# ---------------- Land authority dues (free Search) ----------------
async def authority_lane(query: str, sig: Signals, ev: list[Evidence], ctx: dict, emit) -> None:
    promoter = ctx.get("promoter_name") or query
    await emit({"lane": "authority", "type": "progress", "message": "Checking Noida / Greater Noida / YEIDA dues lists..."})
    core = _core_name(ctx.get("promoter_name")) or _first_word(query)
    hits = await tf.search(f'"{core}" builder dues defaulter Noida Authority OR "Greater Noida Authority" OR YEIDA',
                           limit=8, exclude_domains=SOCIAL)
    words = ("dues", "defaulter", "auction", "recovery")
    matches = [h for h in hits if core in _blob(h)
               and any(w in _blob(h) for w in words)
               and not any(w in _blob(h) for w in ("insolvency", "nclt", "nclat"))]  # those belong to the insolvency lane
    sig.authority_defaulter = bool(matches)
    for h in matches[:3]:
        ev.append(Evidence(lane="authority", source_url=h["url"], snippet=h["snippet"][:500],
                           claim=f"Land-authority dues report: {h['title']}"))


# ---------------- News & protests (free Search) ----------------
ADVERSE = ("delay", "stalled", "protest", "homebuyers", "nclt", "insolvency", "fir", "possession not",
           "stuck", "default", "auction", "sarfaesi")


async def news_lane(query: str, sig: Signals, ev: list[Evidence], ctx: dict, emit) -> None:
    name = ctx.get("project_name") or query
    promoter = ctx.get("promoter_name") or ""
    await emit({"lane": "news", "type": "progress", "message": "Scanning news for delays and buyer protests..."})
    hits = await tf.search(f"{name} {promoter} homebuyers delay", news=True, limit=10, exclude_domains=SOCIAL)
    core = _core_name(promoter) or _core_name(name)
    adverse = [h for h in hits if core in _blob(h)
               and any(w in (h["title"] + " " + h["snippet"]).lower() for w in ADVERSE)]
    sig.adverse_news_count = len(adverse)
    sig.sarfaesi_notice = any("sarfaesi" in (h["title"] + h["snippet"]).lower() for h in adverse)
    for h in adverse[:5]:
        ev.append(Evidence(lane="news", source_url=h["url"], snippet=h["snippet"][:400],
                           claim=f"News: {h['title']}" + (f" ({h['date']})" if h.get("date") else "")))


SOCIAL = "facebook.com,instagram.com,twitter.com,x.com,youtube.com,quora.com,pinterest.com"


def _blob(h: dict) -> str:
    """Lower-case title + url + snippet with punctuation flattened, for name matching."""
    return re.sub(r"[^a-z0-9]+", " ", f"{h.get('title', '')} {h.get('url', '')} {h.get('snippet', '')}".lower())


def _first_word(text: str) -> str:
    words = re.sub(r"[^a-z0-9 ]", " ", (text or "").lower()).split()
    return words[0] if words else ""


def _core_name(name: str | None) -> str:
    """'Jaypee Infratech Private Limited' -> 'jaypee infratech' (for matching in text)."""
    if not name:
        return ""
    n = re.sub(r"\b(private|pvt|limited|ltd|llp|india|infra(structure)?s?|developers?|builders?)\b\.?", " ",
               name.lower())
    n = re.sub(r"[^a-z0-9 ]", " ", n)
    words = n.split()
    return " ".join(words[:2]) if words else ""
