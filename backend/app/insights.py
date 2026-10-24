"""Everything built FROM a finished report: family tree, grounded answers, complaint draft.

No language model is involved. Answers are assembled only from the report's evidence and cite it
by number, so nothing can be invented. If the evidence does not cover a question, we say so.
"""
from __future__ import annotations

import re

from .models import Evidence, Report, Signals


# ---------------- builder family tree ----------------
def build_graph(project: str | None, promoter: str | None, sig: Signals, group_names: list[str]) -> dict:
    nodes, edges = [], []
    if not promoter:
        return {"nodes": nodes, "edges": edges}
    if sig.promoter_in_cirp and sig.cirp_scope == "other_project":
        p_status = "Insolvency limited to another project"
    elif sig.promoter_in_cirp:
        p_status = "Under insolvency (CIRP)"
    else:
        p_status = sig.company_status or "Status not read"
    nodes.append({"id": "promoter", "label": promoter, "kind": "promoter", "status": p_status,
                  "risk": "high" if sig.promoter_in_cirp else "none"})
    nodes.append({"id": "project", "label": project or "This project", "kind": "project",
                  "status": "This project · UP-RERA", "risk": "none"})
    edges.append({"source": "promoter", "target": "project", "verified": True, "label": "Promoter on UP-RERA"})
    for i, name in enumerate(group_names):
        nid = f"group{i}"
        nodes.append({"id": nid, "label": name, "kind": "group", "status": "Named in insolvency news · verify",
                      "risk": "review"})
        edges.append({"source": "promoter", "target": nid, "verified": False, "label": "Same brand name"})
    return {"nodes": nodes, "edges": edges}


# ---------------- grounded Q&A ----------------
INTENTS = [
    ("insolvency", r"insolv|bankrupt|nclt|nclat|cirp|ibbi|दिवाल"),
    ("delay", r"delay|late|extension|extend|deadline|possession|complet|kab|देर|कब"),
    ("registration", r"regist|lapse|revok|rera status|valid"),
    ("company", r"company|director|charge|loan|cin|mca|financ"),
    ("land", r"land|authority|dues|noida|yeida|defaulter"),
    ("news", r"news|protest|media|report(ed)?s? about"),
    ("score", r"score|why|449|rating|calculat|band|risk"),
    ("next", r"what (should|can|do)|next|advice|book|buy|safe"),
]


def _cite(ev: list[Evidence], lanes: set[str]) -> list[int]:
    return [e.n for e in ev if e.lane in lanes][:5]


def answer(r: Report, question: str) -> dict:
    q = (question or "").lower()
    intent = next((name for name, pat in INTENTS if re.search(pat, q)), None)
    s, ev, sc = r.signals, r.evidence, r.score
    if intent == "insolvency":
        if s.promoter_in_cirp and s.cirp_scope == "other_project":
            text = (f"Official records name {r.promoter_name} in insolvency proceedings. Reports say the process is "
                    "limited to specific projects and this project is not named. Read the order to confirm.")
        elif s.promoter_in_cirp:
            text = f"Yes. Official insolvency records name {r.promoter_name}, and nothing found limits them to another project."
        elif s.insolvency_case_found:
            text = (f"An NCLT record names {r.promoter_name} in an insolvency matter, but we could not confirm it was "
                    "admitted or that the company is the one being resolved. Open the record and check its role and stage.")
        elif s.insolvency_reported_in_news:
            text = "News reports mention insolvency proceedings, but no official record with the exact company name was found. Treat it as unverified."
        elif s.promoter_in_cirp is False:
            text = "No official insolvency record with the promoter's exact name was found in IBBI and NCLT results. That is not proof none exists."
        else:
            text = "The insolvency check did not run, so we cannot say."
        return {"intent": intent, "answer": text, "citations": _cite(ev, {"ibbi", "mca"})}
    if intent == "delay":
        parts = []
        if s.extensions_count:
            parts.append(f"The completion date was extended {s.extensions_count} time(s) on UP-RERA")
        if s.delay_months is not None:
            parts.append(f"the revised date is {s.delay_months} months after the original")
        text = (". ".join(parts) + ".") if parts else "We could not read the completion dates from UP-RERA yet."
        return {"intent": intent, "answer": text[0].upper() + text[1:], "citations": _cite(ev, {"rera"})}
    if intent == "registration":
        st = s.registration_status
        text = f"UP-RERA shows the registration status as '{st}'." if st else "The registration status could not be read."
        return {"intent": intent, "answer": text, "citations": _cite(ev, {"rera"})}
    if intent == "company":
        if s.company_status or s.open_charges is not None:
            text = (f"{r.promoter_name}: status '{s.company_status or 'not shown'}', {s.directors or 0} directors, "
                    f"{s.open_charges if s.open_charges is not None else 'unknown'} open charges. "
                    "A charge is a secured loan; on its own it does not mean default.")
        else:
            text = "The company record could not be read."
        return {"intent": intent, "answer": text, "citations": _cite(ev, {"mca"})}
    if intent == "land":
        text = ("A land-authority dues record names the builder." if s.authority_defaulter
                else "No attributable land-authority dues record naming the builder was found in the lists we checked.")
        return {"intent": intent, "answer": text, "citations": _cite(ev, {"authority"})}
    if intent == "news":
        n = s.adverse_news_count or 0
        text = (f"{n} distinct news stories mention delays or buyer protests. News is a signal, not proof."
                if n else "No news about delays or protests naming the builder was found.")
        return {"intent": intent, "answer": text, "citations": _cite(ev, {"news"})}
    if intent == "score":
        top = [x["text"] for x in sc["reasons"] if x["impact"] > 0][:2]
        cap = f" A hard stop capped it at {sc['score']}." if sc["hard_stop"] else ""
        text = (f"The formula gave {sc['formula_score']} (900 minus 6 × weighted penalty {sc['weighted_penalty']})."
                f"{cap} Main reasons: {'; '.join(top) or 'none found'}.")
        return {"intent": intent, "answer": text, "citations": [e.n for e in ev][:3]}
    if intent == "next":
        text = ("Read the cited records yourself, especially anything marked 'requires review'. If you have not booked, "
                "wait until open questions are answered. If you are already a buyer and the promoter is in insolvency, "
                "check the public announcement for the homebuyer claim deadline. Talk to a RERA lawyer before deciding.")
        return {"intent": intent, "answer": text, "citations": [e.n for e in ev if e.status == "verified"][:3]}
    return {"intent": None, "citations": [],
            "answer": "I only answer from this report's evidence. Ask about insolvency, delays, registration, "
                      "the company, land dues, news, the score, or what to do next."}


# ---------------- complaint draft ----------------
def complaint(r: Report) -> str:
    """Draft for the buyer to review and file. Uses verified facts; unverified ones are listed separately."""
    verified = [e for e in r.evidence if e.status in ("verified", "partially_verified")]
    review = [e for e in r.evidence if e.status == "requires_review"]
    facts = "\n".join(f"{i}. {e.claim}. Source: {e.source_url} (retrieved {e.fetched_at[:10]})"
                      for i, e in enumerate(verified, 1)) or "No verified adverse facts were found."
    unverified = "\n".join(f"- {e.claim} ({e.source_url})" for e in review)
    return (
        "DRAFT FOR THE ALLOTTEE TO REVIEW, EDIT AND FILE. NOT LEGAL ADVICE.\n\n"
        "To: Uttar Pradesh Real Estate Regulatory Authority (UP-RERA)\n"
        f"Subject: Complaint under the Real Estate (Regulation and Development) Act, 2016 regarding "
        f"'{r.project_name or r.query}' (Registration No. {r.rera_number or '[enter]'})\n\n"
        "Complainant: [Your name], allottee of unit [number], [contact details]\n"
        f"Respondent: {r.promoter_name or '[Promoter name]'}\n\n"
        "Facts from public records:\n" + facts + "\n\n"
        "Relief sought: [possession with interest for delay / refund with interest / direction to file "
        "pending quarterly progress reports]\n\n"
        "Annexures: copies of the source pages above, allotment letter, payment receipts.\n"
        + ("\nNot included because they still need checking:\n" + unverified + "\n" if unverified else "")
    )
