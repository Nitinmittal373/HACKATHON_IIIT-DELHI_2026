"""End-to-end API test with TinyFish mocked. Mirrors the real Supertech Eco Village I run:
official NCLT records name SUPERTECH LIMITED, but the insolvency is limited to another project."""
import json

import pytest
from fastapi.testclient import TestClient

from app import main, tf

T = "2026-10-24T08:00:00+00:00"


def row(title, url, snippet="", date=None):
    return {"title": title, "url": url, "snippet": snippet, "date": date, "fetched_at": T}


async def fake_search(q, include_domains=None, exclude_domains=None, recency_minutes=None, news=False, limit=5):
    if include_domains and "up-rera" in include_domains:
        return [row("Eco Village I", "https://www.up-rera.in/Frm_View_Project_Details.aspx?id=8334")]
    if include_domains and "zauba" in include_domains:
        return [row("SUPERTECH LIMITED - Company profile", "https://www.zaubacorp.com/SUPERTECH-LIMITED-U74899DL1995PLC074422")]
    if include_domains and "ibbi" in include_domains:
        return [row("Order", "https://nclt.gov.in/order1.pdf", "In the matter of Supertech Limited, corporate debtor"),
                row("Order", "https://nclt.gov.in/order2.pdf", "Supertech Realtors Pvt Ltd")]   # sister company: must not count
    if "project-wise" in q:
        return [row("NCLAT limits Supertech insolvency to one project", "https://www.livelaw.in/x",
                    "The CIRP is limited to the Eco Village-II project of Supertech")]
    if "dues" in q:
        return [row("Noida Authority lists defaulter societies", "https://indianexpress.com/a", "generic list of societies")]
    if news and "NCLT" in q:
        return [row("NCLT initiates insolvency against Supertech Realtors", "https://news.example/b", "Supertech Realtors"),
                row("NCLT initiates insolvency against Supertech Realtors - Outlet", "https://news2.example/b", "Supertech")]
    if news:
        return [row("Supertech Eco Village buyers protest delay", "https://news.example/c", "buyers protest", "2026-09-01")]
    return []


async def fake_agent(lane, url, goal, schema, emit, stealth=True, max_seconds=110):
    await emit({"lane": lane, "type": "progress", "message": "Opening page"})
    if lane == "rera":
        return {"project_name": "SUPERTECH ECO VILLAGE-I PHASE I-C", "promoter_name": "SUPERTECH LIMITED",
                "registration_status": "Registered", "extensions_count": 3, "_fetched_at": T}
    return {"company_name": "SUPERTECH LIMITED", "cin": "U74899DL1995PLC074422", "company_status": "Under CIRP",
            "directors": [{"name": "A"}] * 19, "open_charges_count": 94, "_fetched_at": T}


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(tf, "search", fake_search)
    monkeypatch.setattr(tf, "agent", fake_agent)
    with TestClient(main.app) as c:
        yield c


def test_full_flow_supertech_like(client):
    inv = client.post("/api/investigations", json={"query": "Supertech Eco Village"}).json()["id"]
    with client.stream("GET", f"/api/investigations/{inv}/events") as r:
        events = [json.loads(line[5:]) for line in r.iter_lines() if line.startswith("data:")]
    assert any(e.get("type") == "report" for e in events)

    rep = client.get(f"/api/reports/{inv}").json()
    s = rep["score"]
    assert rep["signals"]["cirp_scope"] == "other_project"
    # 0.30*70 (3 extensions) + 0.25*60 (insolvency of another project) + 0.05*10 (one news story) = 36.5
    assert not s["hard_stop"] and s["weighted_penalty"] == 36.5 and s["score"] == 681 and s["band"] == "Watch"
    # sister-company record and generic authority list must not become claims about this builder
    urls = [e["source_url"] for e in rep["evidence"]]
    assert "https://nclt.gov.in/order2.pdf" not in urls
    assert rep["signals"]["authority_defaulter"] is False
    # the same news story from two outlets counts once
    assert sum("Supertech Realtors" in e["claim"] for e in rep["evidence"]) == 1
    # original retrieval time is kept
    assert all(e["fetched_at"] == T for e in rep["evidence"])
    statuses = {e["status"] for e in rep["evidence"]}
    assert {"verified", "partially_verified", "requires_review"} <= statuses
    assert any(n["label"] == "Supertech Realtors" for n in rep["graph"]["nodes"])

    ans = client.post(f"/api/reports/{inv}/ask", json={"question": "Is my builder insolvent?"}).json()
    assert ans["intent"] == "insolvency" and "not named" in ans["answer"] and ans["citations"]
    draft = client.post(f"/api/reports/{inv}/complaint-draft").json()["text"]
    assert "NOT LEGAL ADVICE" in draft and "SUPERTECH LIMITED" in draft

    assert client.get("/api/reports").json()[0]["id"] == inv


def test_bad_input_and_webhook_secret(client, monkeypatch):
    assert client.post("/api/investigations", json={"query": "ab"}).status_code == 422
    monkeypatch.setattr(main.config, "WEBHOOK_SECRET", "s3cret")
    assert client.post("/api/webhooks/tinyfish?token=wrong", json={}).status_code == 401
    assert client.post("/api/webhooks/tinyfish?token=s3cret&report=x", json={"a": 1}).status_code == 200
