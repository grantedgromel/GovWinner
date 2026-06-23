"""Tests for the valuation math and the screening funnel.

Run with:  python -m pytest tests/ -q     (or)     python -m unittest -q
The worked example pins the numbers documented in
docs/valuation-and-scoring.md (comp $1000 -> bid no more than $300).
"""

import unittest
from datetime import datetime, timezone

from govwinner.models import Listing, BuyBox, CostParams
from govwinner.valuation import net_resale_value, all_in_cost, max_bid, deal_score
from govwinner.screening import screen, Verdict

NOW = datetime(2026, 6, 23, 12, 0, tzinfo=timezone.utc)


class TestWorkedExample(unittest.TestCase):
    """docs/valuation-and-scoring.md §3 worked example."""

    def setUp(self):
        self.p = CostParams(
            comp_median=1000,
            resale_fee_pct=0.15,
            risk_haircut=0.10,
            buyers_premium_pct=0.13,
            sales_tax_pct=0.0,
            transport=60,
            refurb=30,
            time_cost=20,  # "removal/time" bucket in the doc
        )

    def test_net_resale_value(self):
        # 1000 * 0.85 * 0.90 = 765
        self.assertAlmostEqual(net_resale_value(self.p), 765.0, places=6)

    def test_max_bid_is_300(self):
        # (765/1.7 - 110) / 1.13 = 300.88 -> floor 300
        self.assertEqual(max_bid(self.p, margin_multiple=1.7), 300.0)

    def test_all_in_cost_at_max_hits_hurdle(self):
        b = max_bid(self.p, 1.7)
        # All-in at the floored bid stays at/under resale / m.
        self.assertLessEqual(all_in_cost(b, self.p), 765.0 / 1.7 + 1e-9)

    def test_profit_is_positive(self):
        v = deal_score(self.p, margin_multiple=1.7)
        self.assertGreater(v.profit_at_max, 0)


class TestMaxBidEdges(unittest.TestCase):
    def test_unprofitable_lot_returns_zero(self):
        # Fixed costs alone exceed the target all-in -> no bid clears.
        p = CostParams(comp_median=100, transport=500)
        self.assertEqual(max_bid(p, 1.7), 0.0)

    def test_bad_margin_multiple_raises(self):
        with self.assertRaises(ValueError):
            max_bid(CostParams(comp_median=100), 0)

    def test_higher_hurdle_lowers_max_bid(self):
        p = CostParams(comp_median=1000)
        self.assertGreater(max_bid(p, 1.5), max_bid(p, 2.5))


class TestScreening(unittest.TestCase):
    def setUp(self):
        self.box = BuyBox(
            margin_multiple=1.7,
            min_net_profit=75,
            categories=["tools", "industrial", "electronics", "equipment"],
            max_bid_count=8,
            min_removal_days=3,
            excluded_keywords=["hazmat", "firearm"],
            min_current_price=20,
            max_logistics_cost=400,
        )

    def _lst(self, **kw):
        base = dict(
            listing_id="X",
            title="metal cabinet of hand tools",
            category="tools",
            current_price=85,
            bid_count=1,
            photos=["a.jpg"],
            closes_at=datetime(2026, 6, 27, tzinfo=timezone.utc),
            removal_deadline=datetime(2026, 7, 10, tzinfo=timezone.utc),
        )
        base.update(kw)
        return Listing(**base)

    def test_pursue_underpriced_lot(self):
        costs = CostParams(comp_median=900, transport=40, refurb=20, removal_labor=15)
        res = screen(self._lst(), self.box, costs, expected_clearing=220, now=NOW)
        self.assertIs(res.verdict, Verdict.PURSUE)
        self.assertGreater(res.valuation.max_bid, res.listing.current_price)

    def test_skip_crowded_lot(self):
        costs = CostParams(comp_median=18000)
        res = screen(self._lst(bid_count=62, category="electronics"), self.box, costs, now=NOW)
        self.assertIs(res.verdict, Verdict.SKIP)
        self.assertTrue(any("crowded" in r for r in res.reasons))

    def test_skip_below_price_floor(self):
        costs = CostParams(comp_median=120)
        res = screen(self._lst(current_price=10), self.box, costs, now=NOW)
        self.assertIs(res.verdict, Verdict.SKIP)

    def test_skip_excluded_keyword(self):
        costs = CostParams(comp_median=800, transport=100, removal_labor=50)
        res = screen(
            self._lst(title="lot of drums hazmat labeled", category="industrial"),
            self.box, costs, now=NOW,
        )
        self.assertIs(res.verdict, Verdict.SKIP)

    def test_watch_when_below_expected_clearing(self):
        costs = CostParams(comp_median=5000, risk_haircut=0.25, transport=300,
                           removal_labor=80, buyers_premium_pct=0.15)
        res = screen(
            self._lst(category="industrial", current_price=600, bid_count=2),
            self.box, costs, expected_clearing=1500, now=NOW,
        )
        self.assertIs(res.verdict, Verdict.WATCH)

    def test_logistics_over_budget_skips(self):
        costs = CostParams(comp_median=5000, transport=900)
        res = screen(self._lst(category="industrial"), self.box, costs, now=NOW)
        self.assertIs(res.verdict, Verdict.SKIP)
        self.assertTrue(any("logistics" in r for r in res.reasons))

    def test_signals_detected(self):
        costs = CostParams(comp_median=900)
        res = screen(self._lst(bid_count=1, photos=[], description="x"),
                     self.box, costs, now=NOW)
        self.assertTrue(any("thin competition" in s for s in res.signals))
        self.assertTrue(any("no photos" in s for s in res.signals))


if __name__ == "__main__":
    unittest.main()
