"""The funnel (docs/screening-plan.md): apply cheap buy-box gates, flag
mispricing signals, run valuation, and emit a verdict + ranking score.

A lot must clear every buy-box gate to be PURSUED. Lots that pass the gates
but fail the economics (B* <= current price, or B* below expected clearing,
or profit under the floor) are WATCH/SKIP, not PURSUE.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from .models import Listing, BuyBox, CostParams
from .valuation import Valuation, deal_score


class Verdict(str, Enum):
    PURSUE = "PURSUE"   # clears gates AND economics — human-review then bid
    WATCH = "WATCH"     # close: economics marginal or competition creeping up
    SKIP = "SKIP"       # fails a buy-box gate or can't clear the hurdle


@dataclass
class ScreenResult:
    listing: Listing
    verdict: Verdict
    reasons: list[str] = field(default_factory=list)   # why gated / flagged
    signals: list[str] = field(default_factory=list)   # mispricing tells found
    valuation: Optional[Valuation] = None

    @property
    def score(self) -> float:
        return self.valuation.score if self.valuation else float("-inf")


# --- Stage 2: coarse buy-box gates --------------------------------------

def _coarse_gate_failures(lst: Listing, box: BuyBox, now: datetime) -> list[str]:
    fails: list[str] = []

    if box.categories:
        cat = lst.category.lower()
        if not any(c.lower() in cat for c in box.categories):
            fails.append(f"category '{lst.category}' not in buy-box")

    hay = f"{lst.title} {lst.category} {lst.description}".lower()
    for kw in box.excluded_keywords:
        if kw.lower() in hay:
            fails.append(f"excluded keyword '{kw}'")

    if box.allowed_states and lst.location_state:
        if lst.location_state.upper() not in {s.upper() for s in box.allowed_states}:
            fails.append(f"state {lst.location_state} outside service area")

    if lst.on_base and not box.can_handle_base_pickup:
        fails.append("on-base pickup, buy-box can't handle it")

    if lst.current_price < box.min_current_price:
        fails.append(f"price ${lst.current_price:g} below floor ${box.min_current_price:g}")

    if lst.bid_count > box.max_bid_count:
        fails.append(f"{lst.bid_count} bids over ceiling {box.max_bid_count} (crowded)")

    rem = lst.removal_days(now)
    if rem is not None and rem < box.min_removal_days:
        fails.append(f"removal window {rem:.1f}d under {box.min_removal_days:g}d minimum")

    if lst.is_as_is and not box.allow_as_is:
        fails.append("as-is/untested, buy-box disallows")

    return fails


# --- Stage 3: mispricing signals (up-rank candidates) -------------------

def mispricing_signals(lst: Listing, now: datetime) -> list[str]:
    sig: list[str] = []

    if lst.bid_count <= 1:
        sig.append("thin competition (<=1 bid)")
    if lst.photo_count == 0:
        sig.append("no photos (poor listing quality)")
    elif lst.photo_count == 1:
        sig.append("single photo (weak listing)")
    if len(lst.description.strip()) < 60:
        sig.append("sparse description")

    title = lst.title.lower()
    if any(w in title for w in ("assorted", "misc", "miscellaneous", "lot of", "pallet")):
        sig.append("vague bulk lot (contents may exceed price)")
    if lst.is_as_is:
        sig.append("as-is/untested label (often functional)")

    hrs = lst.hours_to_close(now)
    if hrs is not None and 0 < hrs <= 24 and lst.bid_count <= 3:
        sig.append("closes <24h and still cheap")

    if lst.on_base:
        sig.append("on-base (geographic friction thins the field)")

    return sig


# --- Stage 4+: combine into a verdict -----------------------------------

def screen(
    lst: Listing,
    box: BuyBox,
    costs: CostParams,
    expected_clearing: Optional[float] = None,
    now: Optional[datetime] = None,
) -> ScreenResult:
    """Run one listing through the funnel.

    ``costs`` carries the valuation inputs for THIS lot (comp_median etc.) —
    in production these come from the comp engine; here they're supplied per
    listing. If a Listing declares its own buyers_premium_pct, it overrides
    the CostParams default.
    """
    now = now or datetime.now(timezone.utc)

    # Listing-level premium overrides the generic default.
    if lst.buyers_premium_pct is not None:
        costs = CostParams(**{**costs.__dict__, "buyers_premium_pct": lst.buyers_premium_pct})

    fails = _coarse_gate_failures(lst, box, now)
    signals = mispricing_signals(lst, now)

    # Logistics gate needs the cost inputs, so it lives here not in the
    # listing-only coarse filter.
    if costs.fixed_costs > box.max_logistics_cost:
        fails.append(
            f"logistics ${costs.fixed_costs:g} over budget ${box.max_logistics_cost:g}"
        )

    if fails:
        return ScreenResult(lst, Verdict.SKIP, reasons=fails, signals=signals)

    val = deal_score(costs, box.margin_multiple, expected_clearing)

    reasons: list[str] = []
    verdict = Verdict.PURSUE

    if val.max_bid <= lst.current_price:
        verdict = Verdict.SKIP
        reasons.append(
            f"max bid ${val.max_bid:g} <= current price ${lst.current_price:g} (gone)"
        )
    elif val.profit_at_max < box.min_net_profit:
        verdict = Verdict.SKIP
        reasons.append(
            f"profit-at-max ${val.profit_at_max:g} under floor ${box.min_net_profit:g}"
        )
    elif expected_clearing is not None and val.max_bid < expected_clearing:
        # We'd have to overpay to win — keep it on the radar, don't commit.
        verdict = Verdict.WATCH
        reasons.append(
            f"max bid ${val.max_bid:g} below expected clearing ${expected_clearing:g}"
        )
    else:
        reasons.append(
            f"clears hurdle: bid up to ${val.max_bid:g}, ~${val.profit_at_max:g} profit"
        )

    return ScreenResult(lst, verdict, reasons=reasons, signals=signals, valuation=val)
