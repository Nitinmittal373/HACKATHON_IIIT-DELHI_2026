from app.models import Signals
from app.scoring import score


def test_missing_rera_data_is_never_low_risk():
    # the UP-RERA lane failed but other lanes found nothing bad: must not look safe
    r = score(Signals(promoter_in_cirp=False, company_or_director_struck_off=False,
                      authority_defaulter=False, adverse_news_count=0))
    assert r["band"] == "Not enough data"


def test_clean_project_scores_low_risk():
    s = Signals(registration_status="registered", extensions_count=0, delay_months=0,
                qprs_missed_last4=0, promoter_in_cirp=False,
                company_or_director_struck_off=False, authority_defaulter=False,
                adverse_news_count=0)
    r = score(s)
    assert r["score"] == 900 and r["band"] == "Low risk" and r["confidence"] == 1.0


def test_insolvent_promoter_is_always_high_risk():
    r = score(Signals(registration_status="registered", promoter_in_cirp=True))
    assert r["hard_stop"] and r["band"] == "High risk" and r["score"] <= 449
    assert r["reasons"][0]["code"] == "R06"


def test_lapsed_registration_is_hard_stop():
    r = score(Signals(registration_status="Lapsed"))
    assert r["band"] == "High risk" and r["reasons"][0]["code"] == "R01"


def test_delays_and_missed_qprs_lower_the_score():
    r = score(Signals(registration_status="registered", extensions_count=2,
                      delay_months=30, qprs_missed_last4=3, adverse_news_count=2))
    codes = [x["code"] for x in r["reasons"]]
    assert {"R02", "R03", "R04", "R11"} <= set(codes)
    assert r["score"] < 750


def test_unknown_data_is_not_clean():
    r = score(Signals())
    assert r["confidence"] == 0 and any(x["code"] == "R12" for x in r["reasons"])
    assert r["band"] == "Not enough data"   # never "Low risk" when nothing was checked
