from app.matching import brand, dedupe_titles, legal_name_in, normalize, project_pattern


def test_exact_legal_name_does_not_match_sister_company():
    assert legal_name_in("SUPERTECH LIMITED", normalize("Order against Supertech Ltd. under IBC"))
    assert not legal_name_in("SUPERTECH LIMITED", normalize("NCLT admits plea against Supertech Realtors Pvt Ltd"))


def test_project_tokens_never_confuse_phase_one_and_two():
    pat = project_pattern("SUPERTECH ECO VILLAGE-I PHASE I-C", "SUPERTECH LIMITED")
    assert pat.search(normalize("Eco Village-I towers handed over"))
    assert not pat.search(normalize("CIRP limited to Eco Village-II project"))


def test_brand_strips_legal_words():
    assert brand("Jaypee Infratech Private Limited") == "jaypee"


def test_brand_skips_honorifics_and_short_words():
    assert brand("MR PROVIEW REALTECH PRIVATE LIMITED") == "proview"
    assert brand("M/s. A2Z Infra") == "a2z"


def test_same_story_from_two_outlets_counts_once():
    hits = [{"title": "NCLAT limits Supertech insolvency to one project"},
            {"title": "NCLAT limits Supertech insolvency to one project - LiveLaw"},
            {"title": "Buyers protest at Eco Village"}]
    assert len(dedupe_titles(hits)) == 2


def test_scope_phrase_is_not_fooled_by_company_names():
    from app.sources import SCOPE_RE
    assert not SCOPE_RE.search("Order dated 3 May in MR PROVIEW REALTECH PRIVATE LIMITED to be listed")
    assert SCOPE_RE.search("The CIRP is limited to the Eco Village-II project")
    assert SCOPE_RE.search("NCLAT allows project-wise insolvency resolution")


def test_brand_is_whole_word():
    from app.matching import has_word
    assert has_word("ats", normalize("ATS Greens buyers protest"))
    assert not has_word("ats", normalize("Latest stats on housing"))
