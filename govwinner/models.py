"""Data models: the normalized Listing record, the BuyBox gates, and the
per-lot CostParams that feed the valuation math.

Everything is a plain dataclass with ``from_dict`` helpers so listings and
config can be loaded from JSON (see ``examples/`` and ``config/``).
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from typing import Any, Optional


def _parse_dt(value: Any) -> Optional[datetime]:
    """Parse an ISO-8601 string (or pass through a datetime) to aware UTC."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        # Accept a trailing 'Z' as UTC.
        text = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _only_known(cls: type, data: dict) -> dict:
    """Drop keys the dataclass doesn't declare, so extra JSON fields are OK."""
    known = {f.name for f in fields(cls)}
    return {k: v for k, v in data.items() if k in known}


@dataclass
class Listing:
    """One auction lot, normalized across platforms (see docs/screening-plan.md
    Stage 1). Only ``listing_id`` and ``current_price`` are strictly required;
    the rest improve screening quality when present.
    """

    listing_id: str
    platform: str = ""
    url: str = ""
    title: str = ""
    description: str = ""
    category: str = ""
    photos: list[str] = field(default_factory=list)
    current_price: float = 0.0
    bid_count: int = 0
    closes_at: Optional[datetime] = None
    location_state: str = ""          # e.g. "TX"
    on_base: bool = False             # military base / restricted-access pickup
    location_zip: str = ""
    condition: str = ""               # free text; "as-is", "for parts", etc.
    removal_deadline: Optional[datetime] = None
    buyers_premium_pct: Optional[float] = None  # platform default if None
    seller: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "Listing":
        d = _only_known(cls, dict(data))
        d["closes_at"] = _parse_dt(d.get("closes_at"))
        d["removal_deadline"] = _parse_dt(d.get("removal_deadline"))
        return cls(**d)

    # --- derived helpers used by the screening signals -------------------

    def hours_to_close(self, now: Optional[datetime] = None) -> Optional[float]:
        if self.closes_at is None:
            return None
        now = now or datetime.now(timezone.utc)
        return (self.closes_at - now).total_seconds() / 3600.0

    def removal_days(self, now: Optional[datetime] = None) -> Optional[float]:
        if self.removal_deadline is None:
            return None
        now = now or datetime.now(timezone.utc)
        return (self.removal_deadline - now).total_seconds() / 86400.0

    @property
    def photo_count(self) -> int:
        return len(self.photos)

    @property
    def is_as_is(self) -> bool:
        c = self.condition.lower()
        return any(k in c for k in ("as-is", "as is", "untested", "for parts", "salvage"))


@dataclass
class CostParams:
    """All-in cost inputs for one lot (docs/valuation-and-scoring.md §2).

    Percentages are fractions: 0.13 == 13%. ``buyers_premium_pct`` here is a
    fallback; a Listing's own value wins when present.
    """

    comp_median: float                       # median SOLD comparable price
    resale_fee_pct: float = 0.13             # marketplace + payment fees on the sell side
    risk_haircut: float = 0.10               # confidence discount on resale
    buyers_premium_pct: float = 0.13         # charged on top of hammer price
    sales_tax_pct: float = 0.0               # 0 with a valid resale certificate
    removal_labor: float = 0.0               # crew / forklift / base appointment
    transport: float = 0.0                   # freight quote
    refurb: float = 0.0                       # parts + labor to make resellable
    storage: float = 0.0                      # staging / storage
    time_cost: float = 0.0                    # our listing & handling time, valued

    @property
    def fixed_costs(self) -> float:
        """Costs that don't scale with the bid (everything but premium/tax)."""
        return self.removal_labor + self.transport + self.refurb + self.storage + self.time_cost

    @classmethod
    def from_dict(cls, data: dict) -> "CostParams":
        return cls(**_only_known(cls, dict(data)))


@dataclass
class BuyBox:
    """The gates from docs/buy-box.md, in machine-readable form."""

    # Capital
    max_capital_per_deal: float = float("inf")
    # Return hurdle — express EITHER as a margin multiple m OR a min net ROI.
    margin_multiple: float = 1.7             # all-in cost must be <= resale / m
    min_net_profit: float = 0.0              # absolute floor on profit at B*
    # Categories we'll pursue (empty == no category gate)
    categories: list[str] = field(default_factory=list)
    # Geography
    allowed_states: list[str] = field(default_factory=list)  # empty == any
    can_handle_base_pickup: bool = True
    max_logistics_cost: float = float("inf")
    # Competition
    max_bid_count: int = 10                   # hard stop; prefer 0-3 in scoring
    # Timing / risk
    min_removal_days: float = 0.0
    allow_as_is: bool = True
    # Hard category nos (substring match against title/category/description)
    excluded_keywords: list[str] = field(default_factory=list)
    # Floor below which fees eat any profit
    min_current_price: float = 0.0

    @classmethod
    def from_dict(cls, data: dict) -> "BuyBox":
        return cls(**_only_known(cls, dict(data)))
