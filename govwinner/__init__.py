"""GovWinner — systematic screening for underpriced surplus-auction lots.

The package turns the plan in ``docs/`` into runnable code:

- :mod:`govwinner.models`     — normalized Listing record, BuyBox, CostParams
- :mod:`govwinner.valuation`  — net resale, all-in cost, max-bid, deal score
- :mod:`govwinner.screening`  — the funnel: coarse filter, signals, ranking

Margin is made on the buy: the maximum profitable bid (``B*``) is computed
before the live auction is ever watched, and never exceeded.
"""

from .models import Listing, BuyBox, CostParams
from .valuation import (
    net_resale_value,
    all_in_cost,
    max_bid,
    deal_score,
    Valuation,
)
from .screening import screen, ScreenResult, Verdict

__all__ = [
    "Listing",
    "BuyBox",
    "CostParams",
    "net_resale_value",
    "all_in_cost",
    "max_bid",
    "deal_score",
    "Valuation",
    "screen",
    "ScreenResult",
    "Verdict",
]
