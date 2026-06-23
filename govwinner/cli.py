"""Command-line driver: load listings + a buy-box, run the funnel, print a
ranked shortlist.

    python -m govwinner.cli --listings examples/listings.sample.json \
                            --buy-box config/buy-box.example.json

Each listing in the JSON array may carry a ``costs`` object (valuation inputs
for that lot) and an optional ``expected_clearing`` number. In production those
come from the comp engine; for now they live alongside the listing so the tool
is runnable end-to-end.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Optional

from .models import Listing, BuyBox, CostParams
from .screening import screen, Verdict, ScreenResult


def _load_json(path: str) -> object:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def run(
    listings_path: str,
    buy_box_path: Optional[str],
    now: Optional[datetime] = None,
    only: Optional[set[Verdict]] = None,
) -> list[ScreenResult]:
    now = now or datetime.now(timezone.utc)
    raw = _load_json(listings_path)
    if not isinstance(raw, list):
        raise SystemExit("listings file must be a JSON array of listing objects")

    box = BuyBox.from_dict(_load_json(buy_box_path)) if buy_box_path else BuyBox()

    results: list[ScreenResult] = []
    for item in raw:
        lst = Listing.from_dict(item)
        cost_data = item.get("costs")
        if not cost_data or "comp_median" not in cost_data:
            # No comp -> can't value it; treat as needing manual valuation.
            res = ScreenResult(
                lst, Verdict.WATCH, reasons=["no comp/costs supplied — needs valuation"]
            )
            results.append(res)
            continue
        costs = CostParams.from_dict(cost_data)
        expected = item.get("expected_clearing")
        results.append(screen(lst, box, costs, expected_clearing=expected, now=now))

    # Rank: PURSUE first, then by score desc.
    order = {Verdict.PURSUE: 0, Verdict.WATCH: 1, Verdict.SKIP: 2}
    results.sort(key=lambda r: (order[r.verdict], -r.score))

    if only:
        results = [r for r in results if r.verdict in only]
    return results


def _format(res: ScreenResult) -> str:
    lst = res.listing
    head = f"[{res.verdict.value:6}] {lst.title or lst.listing_id}"
    bits = [head, f"    platform={lst.platform or '-'}  price=${lst.current_price:g}  bids={lst.bid_count}"]
    if res.valuation:
        v = res.valuation
        bits.append(
            f"    R=${v.resale_value:g}  max_bid=${v.max_bid:g}  "
            f"profit@max=${v.profit_at_max:g}  P(win)={v.win_probability:g}  score={v.score:g}"
        )
    if res.signals:
        bits.append("    signals: " + "; ".join(res.signals))
    if res.reasons:
        bits.append("    " + "; ".join(res.reasons))
    return "\n".join(bits)


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="govwinner", description=__doc__)
    ap.add_argument("--listings", required=True, help="JSON array of listings")
    ap.add_argument("--buy-box", help="JSON buy-box config (defaults if omitted)")
    ap.add_argument(
        "--only",
        choices=[v.value for v in Verdict],
        nargs="*",
        help="filter output to these verdicts (e.g. --only PURSUE)",
    )
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args(argv)

    only = {Verdict(v) for v in args.only} if args.only else None
    results = run(args.listings, args.buy_box, only=only)

    if args.json:
        payload = [
            {
                "listing_id": r.listing.listing_id,
                "title": r.listing.title,
                "verdict": r.verdict.value,
                "score": r.score if r.valuation else None,
                "valuation": r.valuation.__dict__ if r.valuation else None,
                "signals": r.signals,
                "reasons": r.reasons,
            }
            for r in results
        ]
        print(json.dumps(payload, indent=2, default=str))
        return 0

    pursue = sum(1 for r in results if r.verdict is Verdict.PURSUE)
    print(f"Screened {len(results)} listings  ->  {pursue} PURSUE\n")
    for r in results:
        print(_format(r))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
