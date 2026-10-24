from app.models import Signals
from app.scoring import score

BASE = dict(registration_status="registered", delay_months=0, qprs_missed_last4=0, promoter_in_cirp=False,
            company_or_director_struck_off=False, authority_defaulter=False, adverse_news_count=0)


def sig(**kw) -> Signals:
    return Signals(**{**BASE, **kw})


def test_clean_project_scores_low_risk():
    r = score(sig())
    assert r["score"] == 900 and r["band"] == "Low risk" and r["confidence"] == 1.0


def test_formula_matches_methodology_worked_example():
    # 0.30*70 + 0.25*60 = 36 -> 900 - 216 = 684
    r = score(sig(extensions_count=3, promoter_in_cirp=True, cirp_scope="other_project"))
    assert r["weighted_penalty"] == 36 and r["formula_score"] == 684 and r["score"] == 684
    assert r["band"] == "Watch" and not r["hard_stop"]


def test_insolvency_covering_project_is_hard_stop():
    r = score(sig(extensions_count=3, promoter_in_cirp=True, cirp_scope="company"))
    assert r["hard_stop"] and r["hard_stop_code"] == "R06" and r["band"] == "High risk"
    assert r["formula_score"] == 624 and r["score"] == 449


def test_insolvency_of_another_project_needs_review_not_hard_stop():
    r = score(sig(promoter_in_cirp=True, cirp_scope="other_project"))
    assert not r["hard_stop"]
    assert any(x["code"] == "R06S" and x["status"] == "requires_review" for x in r["reasons"])


def test_news_alone_never_penalises():
    r = score(sig(insolvency_reported_in_news=True))
    assert r["score"] == 900
    assert any(x["code"] == "R06N" and x["impact"] == 0 for x in r["reasons"])


def test_covid_extensions_are_not_counted():
    r = score(sig(extensions_count=2, force_majeure_extensions=2))
    assert r["score"] == 900 and not any(x["code"] == "R02" for x in r["reasons"])


def test_lapsed_registration_is_hard_stop():
    r = score(Signals(registration_status="Lapsed"))
    assert r["band"] == "High risk" and r["reasons"][0]["code"] == "R01"


def test_delays_and_missed_qprs_lower_the_score():
    r = score(sig(extensions_count=2, delay_months=30, qprs_missed_last4=3, adverse_news_count=2))
    assert {"R02", "R03", "R04", "R11"} <= {x["code"] for x in r["reasons"]}
    assert r["score"] < 750


def test_missing_rera_data_is_never_low_risk():
    r = score(Signals(promoter_in_cirp=False, company_or_director_struck_off=False,
                      authority_defaulter=False, adverse_news_count=0))
    assert r["band"] == "Not enough data"


def test_unknown_data_is_not_clean():
    r = score(Signals())
    assert r["confidence"] == 0 and any(x["code"] == "R12" for x in r["reasons"])
    assert r["band"] == "Not enough data"


def test_missing_data_lowers_confidence_not_score():
    r = score(sig(delay_months=None, qprs_missed_last4=None))
    assert r["score"] == 900 and r["confidence"] < 1 and r["band"].startswith("Provisional")


def test_nclt_case_without_admission_is_review_not_hard_stop():
    r = score(sig(insolvency_case_found=True))
    assert not r["hard_stop"] and r["score"] == 855
    assert any(x["code"] == "R06P" and x["status"] == "requires_review" for x in r["reasons"])
