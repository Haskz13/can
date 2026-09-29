from datetime import date, datetime, timedelta

from leadgen.config import Config
from leadgen.models import Opportunity
from leadgen.scoring import rank, score_opportunity

TODAY = date(2026, 9, 29)


def opp(**kw) -> Opportunity:
    base = dict(source="t", ref="r1", title="Leadership training services", description="", buyer="DND", city="",
                province="Ontario", notice_type="Request for Proposal", procurement_method="Competitive", status="Open",
                published=TODAY - timedelta(days=3), closing=datetime(2026, 10, 20, 14), contract_start=None,
                contract_end=None, unspsc=[], gsin=[], unspsc_desc="", regions="", contact_name="", contact_email="",
                contact_phone="", url="u")
    base.update(kw)
    return Opportunity(**base)


def test_training_bid_is_a_lead():
    assert score_opportunity(opp(), Config(), TODAY)


def test_non_training_dropped():
    assert score_opportunity(opp(title="Snow removal services"), Config(), TODAY) is None


def test_closing_too_soon_dropped():
    assert score_opportunity(opp(closing=datetime(2026, 10, 1)), Config(), TODAY) is None


def test_stale_publication_dropped():
    assert score_opportunity(opp(published=TODAY - timedelta(days=90)), Config(), TODAY) is None


def test_long_term_and_stated_value_rank_higher():
    small = score_opportunity(opp(), Config(), TODAY)
    big = score_opportunity(opp(description="Multi-year contract, budget $750,000 for 300 employees",
                                contract_start=date(2027, 1, 1), contract_end=date(2030, 1, 1)), Config(), TODAY)
    assert big.score > small.score and big.est_value == 750_000


def test_rfi_closing_soon_still_early_signal():
    l = score_opportunity(opp(notice_type="Request for Information", closing=datetime(2026, 9, 30)), Config(min_score=0), TODAY)
    assert l and l.stage == "early signal"


def test_rank_sorted():
    ls = rank([opp(ref="a", title="Training"), opp(ref="b", description="multi-year")], Config(), TODAY)
    assert [l.score for l in ls] == sorted((l.score for l in ls), reverse=True)
