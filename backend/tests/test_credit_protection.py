"""The limits that protect TinyFish credit. Every test uses fakes: no live call is ever made."""

from datetime import datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.tinyfish import WebError
from tests.conftest import FIXED_NOW, make_settings, make_web, read_events
from tests.fakes import FakeWebClient
from tests.test_accounts import SECRET, token

NUMBER = {"rera_id": "UPRERAPRJ8334"}


def build(
    tmp_path: Path,
    now: list[datetime] | None = None,
    web: FakeWebClient | None = None,
    **settings: object,
) -> TestClient:
    clock_now = now or [FIXED_NOW]
    values = {"auth_bridge_secret": SECRET, "require_signin_for_checks": True, **settings}
    app = create_app(
        make_settings(tmp_path, **values),
        web=web or make_web(),
        clock=lambda: clock_now[0],
        cache_dir=None,
    )
    return TestClient(app)


def auth(
    sub: str = "one", email: str = "buyer@example.com", at: datetime = FIXED_NOW
) -> dict[str, str]:
    """A sign-in token valid at `at`, for tests that move the clock."""
    expires = at + timedelta(minutes=10)
    return {"Authorization": f"Bearer {token(sub=sub, email=email, expires=expires)}"}


def start(client: TestClient, headers: dict[str, str] | None = None, **body: object):  # type: ignore[no-untyped-def]
    return client.post("/api/checks", json={**NUMBER, **body}, headers=headers or {})


def finish(client: TestClient, response_json: dict[str, str]) -> str:
    read_events(client, response_json["id"])
    return response_json["id"]


# --- A. sign in to start a live check ---------------------------------------------------------


def test_a_visitor_without_sign_in_cannot_start_a_live_check(tmp_path: Path) -> None:
    with build(tmp_path) as client:
        refused = start(client)

        assert refused.status_code == 401
        assert refused.json()["detail"]["code"] == "signin_required"
        assert client.app.state.web.calls == []  # type: ignore[attr-defined]


def test_a_signed_in_account_can_start_one(tmp_path: Path) -> None:
    with build(tmp_path) as client:
        assert start(client, auth()).status_code == 202


def test_the_sign_in_rule_can_be_switched_off(tmp_path: Path) -> None:
    with build(tmp_path, require_signin_for_checks=False) as client:
        assert start(client).status_code == 202


def test_an_account_has_a_few_live_checks_a_day_then_waits_for_midnight_ist(
    tmp_path: Path,
) -> None:
    with build(tmp_path, checks_per_account_per_day=2, reuse_report_days=0) as client:
        for _ in range(2):
            finish(client, start(client, auth(), fresh=True).json())

        third = start(client, auth(), fresh=True)

        assert third.status_code == 429
        detail = third.json()["detail"]
        assert detail["code"] == "account_limit"
        assert "2 live checks" in detail["message"]
        # 04:00 UTC is 09:30 IST, so midnight IST is 14.5 hours away.
        assert int(third.headers["Retry-After"]) == int(14.5 * 3600)
        assert detail["resets_at"].endswith("+05:30")
        # Another account is not affected.
        assert start(client, auth(sub="two"), fresh=True).status_code == 202


def test_the_account_count_starts_again_the_next_indian_day(tmp_path: Path) -> None:
    now = [FIXED_NOW]
    with build(tmp_path, now, checks_per_account_per_day=1, reuse_report_days=0) as client:
        finish(client, start(client, auth(), fresh=True).json())
        assert start(client, auth(), fresh=True).status_code == 429

        now[0] = FIXED_NOW + timedelta(days=1)

        assert start(client, auth(at=now[0]), fresh=True).status_code == 202


# --- B. reuse recent reports ------------------------------------------------------------------


def test_a_recent_report_is_returned_to_anyone_without_a_live_check(tmp_path: Path) -> None:
    with build(tmp_path) as client:
        first = finish(client, start(client, auth()).json())
        calls = len(client.app.state.web.calls)  # type: ignore[attr-defined]

        visitor = start(client)

        assert visitor.status_code == 200
        assert visitor.json()["id"] == first and visitor.json()["reused"] is True
        assert len(client.app.state.web.calls) == calls  # type: ignore[attr-defined]


def test_a_reused_report_is_saved_to_the_account_that_asked(tmp_path: Path) -> None:
    with build(tmp_path) as client:
        first = finish(client, start(client, auth("one")).json())

        reused = start(client, auth("two"))

        assert reused.status_code == 200
        saved = client.get("/api/me/reports", headers=auth("two")).json()
        assert [c["id"] for c in saved] == [first]


def test_a_report_older_than_the_reuse_window_is_checked_again(tmp_path: Path) -> None:
    now = [FIXED_NOW]
    with build(tmp_path, now, reuse_report_days=7) as client:
        first = finish(client, start(client, auth()).json())
        now[0] = FIXED_NOW + timedelta(days=8)

        later = start(client, auth(at=now[0]))

        assert later.status_code == 202 and later.json()["id"] != first


def test_recheck_now_waits_for_the_minimum_days_and_shows_the_date(tmp_path: Path) -> None:
    now = [FIXED_NOW]
    with build(tmp_path, now, recheck_min_days=7) as client:
        first = finish(client, start(client, auth()).json())

        soon = start(client, auth(), fresh=True)

        assert soon.status_code == 429
        assert soon.json()["detail"]["code"] == "recheck_wait"
        assert "Next re-check possible on 01 Nov 2026" in soon.json()["detail"]["message"]
        report = client.get(f"/api/checks/{first}/report").json()
        assert report["check"]["next_recheck_at"].startswith("2026-11-01")

        now[0] = FIXED_NOW + timedelta(days=7, minutes=1)

        assert start(client, auth(at=now[0]), fresh=True).status_code == 202
        # The new check restarts the wait for this project.
        waiting = client.get(f"/api/checks/{first}").json()["next_recheck_at"]
        assert waiting.startswith("2026-11-08")


def test_a_search_answer_is_saved_and_a_saved_answer_does_not_count(tmp_path: Path) -> None:
    with build(tmp_path, searches_per_ip_per_day=2) as client:
        first = client.get("/api/projects/search", params={"q": "Gaur City"})
        searches = len(client.app.state.web.calls)  # type: ignore[attr-defined]

        for _ in range(5):
            again = client.get("/api/projects/search", params={"q": "gaur  city"})

        assert again.json() == first.json()
        assert len(client.app.state.web.calls) == searches  # type: ignore[attr-defined]
        # Only the first search ran, so one more of the two still works.
        other = client.get("/api/projects/search", params={"q": "Supertech Eco Village"})
        assert other.status_code == 200


def test_a_search_answer_expires_after_the_cache_days(tmp_path: Path) -> None:
    now = [FIXED_NOW]
    with build(tmp_path, now, search_cache_days=7) as client:
        client.get("/api/projects/search", params={"q": "Gaur City"})
        searches = len(client.app.state.web.calls)  # type: ignore[attr-defined]
        now[0] = FIXED_NOW + timedelta(days=8)

        client.get("/api/projects/search", params={"q": "Gaur City"})

        assert len(client.app.state.web.calls) > searches  # type: ignore[attr-defined]


def test_searches_per_address_are_limited_signed_out_and_signed_in(tmp_path: Path) -> None:
    queries = ["Gaur City", "Supertech Eco Village", "UPRERAPRJ8334", "Lodha Palava"]
    with build(tmp_path, searches_per_ip_per_day=2, searches_per_ip_per_day_signed_in=3) as client:
        out = [client.get("/api/projects/search", params={"q": q}) for q in queries]

        assert [r.status_code for r in out] == [200, 200, 429, 429]
        detail = out[2].json()["detail"]
        assert detail["code"] == "search_limit" and "Sign in" in detail["message"]
        assert int(out[2].headers["Retry-After"]) >= 1

        # Signed in, the same address has 3 a day; the 2 above used up 2 of them.
        signed = [
            client.get("/api/projects/search", params={"q": q}, headers=auth())
            for q in queries[2:]
        ]
        assert [r.status_code for r in signed] == [200, 429]


def test_the_search_count_starts_again_the_next_indian_day(tmp_path: Path) -> None:
    now = [FIXED_NOW]
    with build(tmp_path, now, searches_per_ip_per_day=1) as client:
        assert client.get("/api/projects/search", params={"q": "Gaur City"}).status_code == 200
        assert client.get("/api/projects/search", params={"q": "Lodha Palava"}).status_code == 429

        now[0] = FIXED_NOW + timedelta(days=1)

        assert client.get("/api/projects/search", params={"q": "Lodha Palava"}).status_code == 200


def test_the_whole_site_has_a_daily_search_cap_that_saved_answers_do_not_use(
    tmp_path: Path,
) -> None:
    with build(tmp_path, site_searches_per_day=2) as client:

        def search(q: str, **headers: str):
            return client.get("/api/projects/search", params={"q": q}, headers=headers or None)

        assert search("Gaur City").status_code == 200
        for _ in range(3):
            assert search("Gaur City").status_code == 200  # saved, so free
        assert search("Supertech Eco Village").status_code == 200

        # A different visitor still has their own allowance, but the site is out.
        refused = search("UPRERAPRJ8334", **auth("someone-else"))
        assert refused.status_code == 429
        detail = refused.json()["detail"]
        assert detail["code"] == "site_search_limit"
        assert "used up" in detail["message"] and "tomorrow" in detail["message"]
        assert int(refused.headers["Retry-After"]) >= 1
        assert search("Gaur City").status_code == 200  # saved answers stay open


def test_a_search_refused_for_one_visitor_does_not_use_up_the_site_cap(tmp_path: Path) -> None:
    with build(tmp_path, searches_per_ip_per_day=1, site_searches_per_day=2) as client:
        ok = client.get("/api/projects/search", params={"q": "Gaur City"})
        for q in ("Lodha Palava", "UPRERAPRJ8334"):
            assert client.get("/api/projects/search", params={"q": q}).status_code == 429
        assert ok.status_code == 200
        other = client.get(
            "/api/projects/search", params={"q": "Supertech Eco Village"}, headers=auth("x")
        )
        assert other.status_code == 200


def test_the_site_search_cap_starts_again_the_next_indian_day(tmp_path: Path) -> None:
    now = [FIXED_NOW]
    with build(tmp_path, now, site_searches_per_day=1) as client:
        assert client.get("/api/projects/search", params={"q": "Gaur City"}).status_code == 200
        assert client.get("/api/projects/search", params={"q": "Lodha Palava"}).status_code == 429

        now[0] = FIXED_NOW + timedelta(days=1)

        assert client.get("/api/projects/search", params={"q": "Lodha Palava"}).status_code == 200


# --- C. a budget for the whole site -----------------------------------------------------------


def test_the_site_day_budget_refuses_new_checks_calmly_but_reports_stay_open(
    tmp_path: Path,
) -> None:
    with build(tmp_path, site_checks_per_day=1, reuse_report_days=0) as client:
        first = finish(client, start(client, auth("one")).json())

        refused = start(client, auth("two"), fresh=True)

        assert refused.status_code == 429
        detail = refused.json()["detail"]
        assert detail["code"] == "site_budget"
        assert detail["message"] == (
            "Today's live checks are used up. Saved reports are still open; "
            "new checks open again tomorrow."
        )
        assert client.get(f"/api/checks/{first}/report").status_code == 200
        assert client.get("/api/projects/search", params={"q": "Gaur City"}).status_code == 200


def test_the_site_month_budget_refuses_until_the_next_month(tmp_path: Path) -> None:
    now = [FIXED_NOW]
    limits = {"site_checks_per_day": 10, "site_checks_per_month": 2, "reuse_report_days": 0}
    with build(tmp_path, now, **limits) as client:
        for sub in ("a", "b"):
            finish(client, start(client, auth(sub), fresh=True).json())
        now[0] = FIXED_NOW + timedelta(days=3)  # a new day, the same month

        refused = start(client, auth("c", at=now[0]), fresh=True)

        assert refused.status_code == 429 and refused.json()["detail"]["code"] == "site_budget"
        assert "this month" in refused.json()["detail"]["message"].lower()
        now[0] = FIXED_NOW + timedelta(days=8)  # November

        assert start(client, auth("c", at=now[0]), fresh=True).status_code == 202


# --- E. invite only ---------------------------------------------------------------------------


def test_invite_only_lets_only_listed_emails_start_checks(tmp_path: Path) -> None:
    allowed = "Friend@Example.com, other@x.in"
    with build(tmp_path, invite_only=True, allowed_emails=allowed) as client:
        stranger = start(client, auth(email="stranger@example.com"))
        assert stranger.status_code == 403
        assert stranger.json()["detail"]["message"] == "Live checks are invite-only right now."

        friend = start(client, auth(email="friend@example.com"))
        assert friend.status_code == 202
        # Saved reports stay open to the stranger.
        finish(client, friend.json())
        assert start(client, auth(email="stranger@example.com")).status_code == 200


# --- C. usage and the admin route -------------------------------------------------------------


def test_usage_is_recorded_per_check_and_shown_to_the_admin_only(tmp_path: Path) -> None:
    with build(tmp_path, admin_token="admin-secret-for-tests") as client:  # noqa: S106
        finish(client, start(client, auth()).json())

        assert client.get("/api/admin/usage").status_code == 401
        wrong = client.get("/api/admin/usage", headers={"X-Admin-Token": "nope"})
        assert wrong.status_code == 401

        usage = client.get("/api/admin/usage", headers={"X-Admin-Token": "admin-secret-for-tests"})
        body = usage.json()
        assert usage.status_code == 200
        assert body["today"]["checks"] == 1 and body["this_month"]["checks"] == 1
        assert body["today"]["fetch"] >= 1
        assert body["average_per_check"]["fetch"] == body["today"]["fetch"]


def test_the_admin_route_is_off_without_a_token(tmp_path: Path) -> None:
    with build(tmp_path) as client:
        response = client.get("/api/admin/usage", headers={"X-Admin-Token": "anything"})

        assert response.status_code == 404


# --- D. credit runs out -----------------------------------------------------------------------


def test_a_lane_that_hits_the_credit_limit_stops_the_remaining_lanes(tmp_path: Path) -> None:
    web = make_web()
    web.search_error = WebError("Search failed: no credit left", "wallet_empty")
    with build(tmp_path, web=web) as client:
        check_id = finish(client, start(client, auth()).json())
        searches = [c for c in web.calls if c[0] == "search"]

        check = client.get(f"/api/checks/{check_id}").json()
        message = "Paused: live-check credits are low"
        paused = [s for s in check["sources"] if s["message"] == message]

        assert paused, check["sources"]
        # The first search failed; every lane after it was refused without calling TinyFish.
        assert len(searches) == 1
        assert all(s["status"] != "completed" for s in paused)


# --- F. the gallery of saved reports ----------------------------------------------------------


def test_the_gallery_shows_only_saved_checks_of_the_listed_numbers(tmp_path: Path) -> None:
    with build(tmp_path, featured_rera_ids="UPRERAPRJ6742, UPRERAPRJ8334") as client:
        assert client.get("/api/featured").json() == []  # nothing saved yet: no invented card

        check_id = finish(client, start(client, auth("someone-private")).json())
        cards = client.get("/api/featured").json()

        assert [c["rera_id"] for c in cards] == ["UPRERAPRJ8334"]
        card = cards[0]
        assert card["check_id"] == check_id and card["name"]
        assert card["display_score"]["band"] and card["read_at"]
        assert "someone-private" not in str(cards) and "buyer@example.com" not in str(cards)


def test_a_failed_check_is_not_in_the_gallery(tmp_path: Path) -> None:
    web: FakeWebClient = make_web()
    with build(tmp_path, web=web, featured_rera_ids="UPRERAPRJ9999") as client:
        failed = client.post(
            "/api/checks",
            json={"rera_id": "UPRERAPRJ9999", "details_url": "https://www.up-rera.in/x?id=1"},
            headers=auth(),
        )
        read_events(client, failed.json()["id"])

        assert client.get("/api/featured").json() == []


# --- what a visitor is told before starting --------------------------------------------------


def test_limits_tell_a_signed_in_account_how_many_live_checks_are_left(tmp_path: Path) -> None:
    with build(tmp_path, checks_per_account_per_day=2, reuse_report_days=0) as client:
        out = client.get("/api/limits").json()
        assert out["checks_left_today"] is None and out["require_signin"] is True
        assert out["live_checks_open"] is True and out["reuse_report_days"] == 0

        finish(client, start(client, auth(), fresh=True).json())

        assert client.get("/api/limits", headers=auth()).json()["checks_left_today"] == 1


def test_limits_say_when_the_site_budget_is_used_up(tmp_path: Path) -> None:
    with build(tmp_path, site_checks_per_day=1) as client:
        finish(client, start(client, auth()).json())

        assert client.get("/api/limits").json()["live_checks_open"] is False
