"""The money math (docs/valuation-and-scoring.md).

The discipline this module enforces: compute the maximum profitable bid
``B*`` BEFORE watching the live auction, then never exceed it.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import floor
from typing import Optional

from .models import CostParams


def net_resale_value(p: CostParams) -> float:
    """R = comp_median * (1 - resale_fee) * (1 - risk_haircut).

    What we can actually realize on the sell side, not the optimistic sticker.
    """
    return p.comp_median * (1.0 - p.resale_fee_pct) * (1.0 - p.risk_haircut)


def all_in_cost(bid: float, p: CostParams) -> float:
    """C(B) = B*(1 + premium + tax) + fixed costs (removal, transport, refurb...)."""
    return bid * (1.0 + p.buyers_premium_pct + p.sales_tax_pct) + p.fixed_costs


def max_bid(p: CostParams, margin_multiple: float) -> float:
    """B* — the highest hammer bid that still clears the margin hurdle.

    Solves C(B*) = R / m for B*:

        B* = (R/m - fixed_costs) / (1 + premium + tax)

    Returns a value floored to whole currency units (never bid fractions),
    and never negative. A non-positive result means the lot can't clear the
    hurdle at any price -> don't pursue.
    """
    if margin_multiple <= 0:
        raise ValueError("margin_multiple must be > 0")
    r = net_resale_value(p)
    target_all_in = r / margin_multiple
    numerator = target_all_in - p.fixed_costs
    denom = 1.0 + p.buyers_premium_pct + p.sales_tax_pct
    raw = numerator / denom
    return float(max(0.0, floor(raw)))


def win_probability(b_star: float, expected_clearing: Optional[float]) -> float:
    """Rough P(win at B*) from the cushion of B* over expected clearing price.

    Heuristic until the Phase-4 model exists (docs §4). Bounded to [0.02, 0.98].
    No estimate available -> 0.5 (coin flip, neutral for ranking).
    """
    if expected_clearing is None:
        return 0.5
    if b_star <= 0:
        return 0.02
    cushion = (b_star - expected_clearing) / b_star  # >0 means we can outbid
    p = 0.5 + cushion  # full cushion of B* -> near-certain; negative -> unlikely
    return float(min(0.98, max(0.02, p)))


@dataclass
class Valuation:
    """Computed economics for one lot."""

    resale_value: float          # R
    max_bid: float               # B*
    profit_at_max: float         # R - C(B*)  (worst-case profit if we win at B*)
    win_probability: float       # P(win at B*)
    confidence: float            # 1 - risk_haircut
    effort_index: float          # logistics/refurb burden, >= 1
    score: float                 # ranking score (higher = better)
    expected_clearing: Optional[float]

    @property
    def expected_value(self) -> float:
        """Profit-at-max weighted by the odds of actually winning it."""
        return self.profit_at_max * self.win_probability


def deal_score(
    p: CostParams,
    margin_multiple: float,
    expected_clearing: Optional[float] = None,
) -> Valuation:
    """Full valuation + ranking score for one lot.

        score = profit_at_max * P(win) * confidence / effort_index

    Effort penalizes logistics/refurb-heavy lots relative to their value, so a
    clean flip outranks a forklift-and-freight nightmare of equal paper profit
    (unless the profit is big enough to pay for the moat).
    """
    r = net_resale_value(p)
    b_star = max_bid(p, margin_multiple)
    profit_at_max = r - all_in_cost(b_star, p)
    win_p = win_probability(b_star, expected_clearing)
    confidence = 1.0 - p.risk_haircut
    # Effort: 1 + fixed costs as a fraction of resale value. Lots whose
    # logistics rival their value are heavily penalized.
    effort_index = 1.0 + (p.fixed_costs / r if r > 0 else p.fixed_costs)
    score = (profit_at_max * win_p * confidence) / effort_index
    return Valuation(
        resale_value=round(r, 2),
        max_bid=b_star,
        profit_at_max=round(profit_at_max, 2),
        win_probability=round(win_p, 4),
        confidence=round(confidence, 4),
        effort_index=round(effort_index, 4),
        score=round(score, 2),
        expected_clearing=expected_clearing,
    )
