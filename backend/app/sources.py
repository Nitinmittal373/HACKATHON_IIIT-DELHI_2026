"""The investigation lanes. Each lane fills part of `Signals`, adds cited `Evidence`, and records `checks`.

Escalation ladder (TinyFish's own advice): Search -> Fetch -> Agent.
Search/Fetch are free and run in parallel; the Agent is used only for the UP-RERA and company pages.

Every lane follows docs/METHODOLOGY.md:
  * official records need the promoter's exact legal name (see matching.py)
  * news is a signal that "requires review", never proof on its own
  * one story repeated by several outlets counts once
"""
from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import urlparse

from . import tf
from .matching import blob, brand, dedupe_titles, has_word, legal_name_in, looks_like_rera_number, normalize, project_pattern
from .models import Check, Evidence, Signals

UPRERA_HOME = "https://www.up-rera.in/projects"
SOCIAL = "facebook.com,instagram.com,twitter.com,x.com,youtube.com,quora.com,pinterest.com,linkedin.com,reddit.com"
LAND_AUTHORITY_DOMAINS = ("noidaauthorityonline.in", "greaternoidaauthority.in", "yamunaexpresswayauthority.com")
FORCE_MAJEURE = ("covid", "corona", "pandemic", "force majeure", "lockdown")


def _domain(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def _parse_date(s: str | None) -> datetime | None:
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d %b %Y", "%d %B %Y", "%b %Y", "%B %Y"):
        try:
            return datetime.strptime(s.strip(), fmt)
        except ValueError:
            continue
    return None


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
        "extensions": {"type": "array", "items": {"type": "object", "properties": {
            "new_completion_date": {"type": "string"}, "reason": {"type": "string"}}}},
        "extensions_count": {"type": "integer"},
        "total_units": {"type": "integer"},
        "quarterly_progress_reports": {"type": "array", "items": {"type": "object", "properties": {
            "quarter": {"type": "string"}, "filed": {"type": "boolean"}}}},
        "complaints_count": {"type": "integer"},
        "penalty_orders_count": {"type": "integer"},
        "project_photo_url": {"type": "string"},
    },
}
RERA_GOAL = (
    "This is a UP-RERA real estate project page. Read the project details and return: "
    "project name, RERA registration number, promoter (builder company) name exactly as written, "
    "registration status, promised (original) completion date, revised/extended completion date, "
    "each extension granted with its new completion date and the reason given (for example COVID-19 "
    "force majeure), number of extensions, total units, the quarterly progress reports (QPRs) for the "
    "last 4 quarters with whether each was filed, number of complaints and number of penalty orders. "
    "If the page shows a photo or rendering of the project, return its full image URL as project_photo_url. "
    "If a field is not shown, leave it out. Write dates as YYYY-MM-DD where possible. Do not guess."
)
RERA_SEARCH_GOAL = (
    "Search UP-RERA registered projects for '{q}'. Open the best matching project's details page and "
    "return the requested fields. If nothing matches, return an empty object."
)


async def resolve_rera_url(query: str) -> str | None:
    """Free Search first: find the project's own UP-RERA page from a name or RERA number."""
    hits = await tf.search(f"{query} UP RERA project", include_domains="up-rera.in", limit=10)
    pages = [h for h in hits if any(k in h["url"].lower()
                                    for k in ("projectsummary", "frm_view_project_details"))]
    if not pages:
        return None
    if looks_like_rera_number(query):
        # A registration number must appear on the page itself, otherwise we would read the wrong project
        num = normalize(query).replace(" ", "")
        exact = [h for h in pages if num in blob(h).replace(" ", "")]
        return exact[0]["url"] if exact else None
    words = [w for w in normalize(query).split() if len(w) > 2]
    pages.sort(key=lambda h: sum(w in blob(h) for w in words), reverse=True)
    return pages[0]["url"]


async def rera_lane(query: str, sig: Signals, ev: list[Evidence], checks: list[Check], ctx: dict, emit) -> None:
    await emit({"lane": "rera", "type": "progress", "message": "Finding the project on UP-RERA (free Search)..."})
    url = await resolve_rera_url(query)
    if url:
        res = await tf.agent("rera", url=url, goal=RERA_GOAL, schema=RERA_SCHEMA, emit=emit)
    else:
        url = UPRERA_HOME
        res = await tf.agent("rera", url=url, goal=RERA_SEARCH_GOAL.format(q=query) + " " + RERA_GOAL,
                             schema=RERA_SCHEMA, emit=emit)
    if not res or not res.get("project_name"):
        checks.append(Check(lane="rera", what="UP-RERA project record", outcome="unavailable",
                            detail="The page could not be read"))
        raise RuntimeError("UP-RERA page could not be read")

    at = res.pop("_fetched_at", None)
    ctx.update(rera_url=url, project_name=res.get("project_name"),
               rera_number=res.get("rera_registration_number"), promoter_name=res.get("promoter_name"))
    photo = res.get("project_photo_url") or ""
    if photo.startswith("https://") or photo.startswith("http://"):
        ctx["photo_url"] = photo
    sig.registration_status = (res.get("registration_status") or "").lower() or None
    exts = res.get("extensions") or []
    sig.extensions_count = res.get("extensions_count") if res.get("extensions_count") is not None else (len(exts) if exts else None)
    sig.force_majeure_extensions = sum(1 for e in exts if any(w in (e.get("reason") or "").lower() for w in FORCE_MAJEURE))
    sig.total_units = res.get("total_units")
    sig.rera_complaints = res.get("complaints_count")
    sig.rera_penalty_orders = res.get("penalty_orders_count")
    sig.promised_completion = res.get("promised_completion_date")
    sig.revised_completion = res.get("revised_completion_date")
    promised, revised = _parse_date(sig.promised_completion), _parse_date(sig.revised_completion)
    if promised and revised:
        sig.delay_months = max(0, (revised.year - promised.year) * 12 + revised.month - promised.month)
    qprs = res.get("quarterly_progress_reports") or []
    if qprs:
        sig.qprs_missed_last4 = sum(1 for q in qprs[:4] if q.get("filed") is False)

    kw = dict(lane="rera", source_url=url, source_type="official", status="verified", **({"fetched_at": at} if at else {}))
    snippet = {k: v for k, v in res.items() if v not in (None, "", [])}
    ev.append(Evidence(claim=f"UP-RERA record for {ctx['project_name']}", snippet=str(snippet)[:1500], **kw))
    checks.append(Check(lane="rera", what="UP-RERA project record", outcome="found"))
    if sig.extensions_count:
        fm = f", {sig.force_majeure_extensions} of them COVID-era force majeure" if sig.force_majeure_extensions else ""
        ev.append(Evidence(claim=f"Completion date extended {sig.extensions_count} time(s){fm}", **kw))
    if sig.delay_months:
        ev.append(Evidence(claim=f"Completion moved from {sig.promised_completion} to {sig.revised_completion} "
                                 f"({sig.delay_months} months)", **kw))
    if sig.qprs_missed_last4:
        ev.append(Evidence(claim=f"{sig.qprs_missed_last4} of the last 4 quarterly progress reports not filed", **kw))
    if sig.delay_months is None:
        checks.append(Check(lane="rera", what="Original and revised completion dates", outcome="not_found",
                            detail="Dates not readable on the page"))


# ---------------- Company (agent on a public company page) ----------------
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
            "Under liquidation / Under CIRP etc.), current directors with DIN, number of open charges, date of "
            "the latest charge and date of the last annual filing. Do not guess missing fields.")


async def mca_lane(query: str, sig: Signals, ev: list[Evidence], checks: list[Check], ctx: dict, emit) -> None:
    promoter = ctx.get("promoter_name")
    if not promoter:
        checks.append(Check(lane="mca", what="Company registry record", outcome="skipped",
                            detail="Builder company unknown because UP-RERA did not load"))
        raise RuntimeError("Builder company unknown (UP-RERA did not load), so the company check was skipped")
    await emit({"lane": "mca", "type": "progress", "message": f"Looking up company '{promoter}' (free Search)..."})
    hits = await tf.search(f"{promoter} CIN directors", include_domains="zaubacorp.com,tofler.in,qorpiq.com", limit=8)
    hits = [h for h in hits if legal_name_in(promoter, blob(h))]
    if not hits:
        checks.append(Check(lane="mca", what=f"Company page for {promoter}", outcome="not_found"))
        raise RuntimeError(f"No company page with the exact name '{promoter}' was found")
    url = hits[0]["url"]
    res = await tf.agent("mca", url=url, goal=MCA_GOAL, schema=MCA_SCHEMA, emit=emit, max_seconds=90)
    if not res:
        checks.append(Check(lane="mca", what=f"Company page for {promoter}", outcome="unavailable"))
        raise RuntimeError("Company page could not be read")
    at = res.pop("_fetched_at", None)
    if res.get("company_name") and not legal_name_in(promoter, normalize(res.get("company_name"))):
        checks.append(Check(lane="mca", what=f"Company page for {promoter}", outcome="not_found",
                            detail=f"Page was for '{res.get('company_name')}', so it was not used"))
        raise RuntimeError("The company page did not match the promoter's exact name")
    ctx["company"] = res
    status = (res.get("company_status") or "")
    sig.company_status = status or None
    sig.cin = res.get("cin")
    sig.directors = len(res.get("directors") or []) or None
    sig.open_charges = res.get("open_charges_count")
    sig.company_or_director_struck_off = any(w in status.lower() for w in ("strike", "struck", "liquidat", "dissolved"))
    latest = _parse_date(res.get("latest_charge_date"))
    sig.recent_charge_creation = bool(latest and (datetime.now() - latest).days < 365)
    if "cirp" in status.lower() or "insolvency" in status.lower():
        ctx["registry_says_cirp"] = True
    official = _domain(url).endswith("mca.gov.in")
    ev.append(Evidence(lane="mca", source_url=url,
                       source_type="official" if official else "registry_mirror",
                       status="verified" if official else "partially_verified",
                       claim=f"{res.get('company_name') or promoter}: status '{status or 'not shown'}', "
                             f"{sig.directors or 0} director(s), {res.get('open_charges_count', 'unknown')} open charge(s)",
                       snippet=str(res)[:1500], **({"fetched_at": at} if at else {})))
    checks.append(Check(lane="mca", what=f"Company page for {promoter}", outcome="found",
                        detail="Registry mirror; confirm on mca.gov.in" if not official else ""))


# ---------------- IBBI / NCLT insolvency (free Search) ----------------
# An NCLT document can name a company as a creditor or in an unrelated matter, so a name alone is not enough:
# the same hit must also carry insolvency words. IBBI public announcements are issued only after admission,
# so only those (or the registry status "Under CIRP") count as the promoter being in CIRP.
INSOLVENCY_WORDS = ("corporate debtor", "cirp", "insolvency resolution", "resolution professional",
                    "public announcement", "section 7", "section 9", "section 10", "liquidat", "moratorium")
SCOPE_RE = re.compile(
    r"project[\s-]*wise\s+(insolvency|cirp|resolution)"
    r"|(insolvency|cirp|proceedings?|resolution process)[^.]{0,80}\b(limited|confined|restricted)\s+to\b"
    r"|\bonly\s+(to\s+)?(one|a single|the)\s+project\b",
    re.I,
)
GROUP_SUFFIX = ("Realtors", "Realty", "Estates", "Infratech", "Infra", "Housing", "Townships", "Buildwell",
                "Homes", "Constructions", "Projects", "Properties", "Developers", "Builders")


def _raw(h: dict) -> str:
    return f"{h.get('title', '')} {h.get('snippet', '')}"


async def ibbi_lane(query: str, sig: Signals, ev: list[Evidence], checks: list[Check], ctx: dict, emit) -> None:
    promoter = ctx.get("promoter_name")
    b = brand(promoter) or brand(query)
    who = promoter or query
    await emit({"lane": "ibbi", "type": "progress", "message": f"Checking IBBI and NCLT records for '{who}'..."})

    # 1) Official records: exact legal name AND insolvency words in the same record.
    official = await tf.search(f'"{who}" corporate insolvency resolution process',
                               include_domains="ibbi.gov.in,nclt.gov.in", limit=10)
    matched = [h for h in official
               if promoter and legal_name_in(promoter, blob(h))
               and any(w in _raw(h).lower() or w in blob(h) for w in INSOLVENCY_WORDS)]
    ibbi_hits = [h for h in matched if _domain(h["url"]).endswith("ibbi.gov.in")]
    nclt_hits = [h for h in matched if h not in ibbi_hits]
    sig.promoter_in_cirp = bool(ibbi_hits)
    sig.insolvency_case_found = bool(nclt_hits) if not ibbi_hits else None
    for h in ibbi_hits[:2]:
        ev.append(Evidence(lane="ibbi", source_url=h["url"], source_type="official", status="verified",
                           snippet=h["snippet"][:500], fetched_at=h["fetched_at"],
                           claim=f"IBBI public record names {promoter} in an insolvency process: {h['title'] or 'IBBI notice'}"))
    for h in nclt_hits[:3]:
        ev.append(Evidence(lane="ibbi", source_url=h["url"], source_type="official", status="requires_review",
                           snippet=h["snippet"][:500], fetched_at=h["fetched_at"],
                           claim=f"NCLT record names {promoter} in an insolvency matter; check its role and stage: "
                                 f"{h['title'] or 'NCLT document'}"))
    checks.append(Check(lane="ibbi", what="IBBI / NCLT insolvency records with the promoter's exact name",
                        outcome="found" if matched else "not_found",
                        detail="" if promoter else "Promoter unknown, exact-name check not possible"))

    # 2) If proceedings exist, what do they cover? (Project-wise insolvency is allowed in India.)
    if matched or ctx.get("registry_says_cirp"):
        await emit({"lane": "ibbi", "type": "progress", "message": "Checking whether the proceedings cover this project..."})
        scope_hits = await tf.search(f'"{b}" project-wise insolvency NCLAT', limit=8, exclude_domains=SOCIAL)
        pat = project_pattern(ctx.get("project_name"), promoter)
        scoped = [h for h in scope_hits if has_word(b, blob(h)) and SCOPE_RE.search(_raw(h))]
        if scoped:
            mentions_us = bool(pat and any(pat.search(blob(h)) for h in scoped))
            sig.cirp_scope = "this_project" if mentions_us else "other_project"
            h = scoped[0]
            ev.append(Evidence(lane="ibbi", source_url=h["url"], source_type="news", status="requires_review",
                               snippet=h["snippet"][:500], fetched_at=h["fetched_at"],
                               claim=("Reported: the insolvency process is limited to specific projects"
                                      + (" and names this project" if mentions_us else ", and this project is not named")
                                      + f". Verify in the order: {h['title']}")))
        else:
            sig.cirp_scope = "company"
        checks.append(Check(lane="ibbi", what="Scope of the insolvency proceedings", outcome="found",
                            detail={"company": "No project-wise limit found: treated as company-wide",
                                    "this_project": "Project-wise, and this project is covered",
                                    "other_project": "Project-wise, and this project is not named"}[sig.cirp_scope]))

    # 3) News: a signal only, never proof. Brand as a whole word + insolvency words, de-duplicated.
    news = await tf.search(f'"{b}" NCLT insolvency', news=True, limit=10, exclude_domains=SOCIAL) if b else []
    rep = dedupe_titles([h for h in news if has_word(b, blob(h))
                         and any(w in blob(h) for w in ("insolvency", "nclt", "nclat", "cirp"))])
    rep = [h for h in rep if h["url"] not in {e.source_url for e in ev}]
    if rep and not matched:
        sig.insolvency_reported_in_news = True
    for h in rep[:3]:
        d = f" ({h['date']})" if h.get("date") else ""
        ev.append(Evidence(lane="ibbi", source_url=h["url"], source_type="news", status="requires_review",
                           snippet=h["snippet"][:400], fetched_at=h["fetched_at"],
                           claim=f"Reported{d}: {h['title']}"))
    ctx["group_names"] = _group_names(rep + matched, b, promoter)
    await emit({"lane": "ibbi", "type": "progress",
                "message": f"{len(ibbi_hits)} IBBI record(s), {len(nclt_hits)} NCLT record(s), {len(rep)} news report(s)"})


def _group_names(hits: list[dict], b: str, promoter: str | None) -> list[str]:
    """Company names like 'Supertech Realtors' seen next to the brand. Shown as 'verify' links only."""
    if not b:
        return []
    found: dict[str, None] = {}
    pat = re.compile(rf"\b({re.escape(b.capitalize())}|{re.escape(b.upper())})\s+({'|'.join(GROUP_SUFFIX)})\b", re.I)
    for h in hits:
        for m in pat.finditer(f"{h.get('title', '')} {h.get('snippet', '')}"):
            name = f"{m.group(1).capitalize()} {m.group(2).capitalize()}"
            if normalize(name) not in normalize(promoter):
                found[name] = None
    return list(found)[:4]


# ---------------- Land authority dues (free Search) ----------------
async def authority_lane(query: str, sig: Signals, ev: list[Evidence], checks: list[Check], ctx: dict, emit) -> None:
    promoter = ctx.get("promoter_name")
    b = brand(promoter) or brand(query)
    await emit({"lane": "authority", "type": "progress", "message": "Checking Noida, Greater Noida and YEIDA dues lists..."})
    hits = await tf.search(f'"{b}" builder dues defaulter Noida Authority OR "Greater Noida Authority" OR YEIDA',
                           limit=10, exclude_domains=SOCIAL)
    words = ("dues", "defaulter", "auction", "recovery")
    found = False
    for h in dedupe_titles(hits):
        text = blob(h)
        if not any(w in text for w in words) or any(w in text for w in ("insolvency", "nclt", "nclat")):
            continue
        official = _domain(h["url"]).endswith(LAND_AUTHORITY_DOMAINS)
        # Attributable record: an official page naming the brand, or news naming the exact legal name
        if (official and has_word(b, text)) or (promoter and legal_name_in(promoter, text)):
            found = True
            ev.append(Evidence(lane="authority", source_url=h["url"],
                               source_type="official" if official else "news",
                               status="verified" if official else "requires_review",
                               snippet=h["snippet"][:500], fetched_at=h["fetched_at"],
                               claim=f"Land-authority dues record: {h['title']}"))
    sig.authority_defaulter = found
    checks.append(Check(lane="authority", what="Noida / Greater Noida / YEIDA dues and defaulter lists",
                        outcome="found" if found else "not_found",
                        detail="" if found else "No attributable record naming the builder"))


# ---------------- News & protests (free Search) ----------------
ADVERSE = ("delay", "stalled", "protest", "homebuyers", "possession not", "stuck", "sarfaesi", "fir ")


async def news_lane(query: str, sig: Signals, ev: list[Evidence], checks: list[Check], ctx: dict, emit) -> None:
    name = ctx.get("project_name") or query
    b = brand(ctx.get("promoter_name")) or brand(query)
    await emit({"lane": "news", "type": "progress", "message": "Scanning news for delays and buyer protests..."})
    hits = await tf.search(f"{name} homebuyers delay protest", news=True, limit=12, exclude_domains=SOCIAL)
    adverse = dedupe_titles([h for h in hits if has_word(b, blob(h))
                             and any(w in f"{h['title']} {h['snippet']} ".lower() for w in ADVERSE)])
    sig.adverse_news_count = len(adverse)
    sig.sarfaesi_notice = any("sarfaesi" in blob(h) for h in adverse) or None
    for h in adverse[:5]:
        ev.append(Evidence(lane="news", source_url=h["url"], source_type="news", status="requires_review",
                           snippet=h["snippet"][:400], fetched_at=h["fetched_at"],
                           claim=f"News{' (' + h['date'] + ')' if h.get('date') else ''}: {h['title']}"))
    checks.append(Check(lane="news", what="News about delays and buyer protests",
                        outcome="found" if adverse else "not_found",
                        detail=f"{len(adverse)} distinct stories after removing repeats" if adverse else ""))
