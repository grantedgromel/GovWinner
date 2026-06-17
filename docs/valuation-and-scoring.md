# Valuation, Cost Model & Deal Scoring

The whole system lives or dies on one discipline: **compute the maximum profitable bid before watching the live auction, then never exceed it.** Margin is made on the buy.

---

## 1. Net resale value `R`

What we can actually realize when we sell, not the optimistic sticker:

```
R = comp_median × (1 − resale_fee_pct) × (1 − risk_haircut)
```

- **`comp_median`** — median of *sold* comparables (eBay sold listings / Terapeak, dealer or market value guides, auction history for the same model). Use **sold**, never "asking."
- **`resale_fee_pct`** — marketplace + payment fees on the sell side (e.g. eBay ~13% + payment processing), or dealer/wholesale discount if flipping in bulk.
- **`risk_haircut`** — confidence discount. Tested & photographed: small. "As-is / untested": large. Thin comp data: large.
- **Scrap/parts value** is the floor — for metals or dead equipment, `R` can default to recoverable material value.

## 2. All-in cost `C(B)`

The real price of winning at hammer bid `B`:

```
C(B) = B × (1 + buyers_premium_pct + sales_tax_pct)
       + removal_labor
       + transport
       + refurb_parts_and_labor
       + storage
       + listing_and_handling_time
```

- **`buyers_premium_pct`**, **`sales_tax_pct`** — per platform/jurisdiction; pull current values from [sources.md](sources.md) notes. Sales tax → 0 with a valid resale certificate.
- **`transport`** — get a real freight quote for anything that won't fit in a vehicle. This single line kills most paper-profit deals; quote it *before* bidding.
- **`removal_labor`** — forklift, crew, base-access appointment, etc.

## 3. Maximum bid `B*`

Let the hurdle be a required net return. Two equivalent ways to state the hurdle — pick one in the buy-box:

- **Margin multiple** `m` (want all-in cost ≤ `R / m`, e.g. `m = 1.7`), or
- **Minimum net profit** `π_min` plus minimum ROI.

Solving `C(B*) = R / m` for the bid:

```
            (R / m) − removal_labor − transport − refurb − storage − time
   B*  =   ──────────────────────────────────────────────────────────────
                       (1 + buyers_premium_pct + sales_tax_pct)
```

- If **`B* ≤ current_price`**, the deal is already gone → drop it.
- If **`B* < expected_clearing_price`** (Section 4), we'd have to overpay to win → deprioritize.
- The number you carry into Stage 7 is **`B*`, rounded down**. That is the walk-away line.

### Worked example
- Comp median for the item: **$1,000**; resale fee 15%; risk haircut 10% → `R = 1000 × 0.85 × 0.90 = $765`.
- Hurdle `m = 1.7` → max all-in cost = `765 / 1.7 = $450`.
- Costs: transport $60, refurb $30, removal/time $20 → $110.
- Premium 13% + tax 0% (resale cert) = 1.13.
- `B* = (450 − 110) / 1.13 = $300.9` → **bid no more than $300.**

If the current price is $90 with 1 bid and 2 days left, that's a live candidate. If it's already at $320 with 11 bids, walk.

---

## 4. Expected clearing price

Estimate where the lot will actually settle, so we don't chase lots we can't win profitably.

- **Phase 1–2 (heuristic):** category × value-tier × current-bid-trajectory, calibrated from observed completions and the thesis distribution (low-value/low-bid lots clear near reserve; high-value lots escalate fast once "discovered").
- **Phase 4 (model):** regression/ML trained on the Stage 9 outcome log (`predicted_clearing` vs `actual_clearing`).

Decision rule combining everything:

```
PURSUE if:  B* > current_price
       AND  B* ≥ expected_clearing_price
       AND  bid_count within buy-box ceiling
       AND  removal feasible before deadline
```

---

## 5. Deal score (for ranking the shortlist)

When many lots pass the gate, rank by expected value adjusted for effort and risk:

```
score =  expected_net_profit
         × P(win at B*)
         × confidence_in_R
         ÷ effort_index            (logistics + refurb + time)
```

- **`expected_net_profit`** = `R − C(B*)` (profit if we win at our max).
- **`P(win at B*)`** ≈ how far `B*` sits above expected clearing (more cushion → higher win odds).
- **`confidence_in_R`** = inverse of the risk haircut (good comps & tested items rank up).
- **`effort_index`** = relative pain of removal/transport/refurb (penalize logistics nightmares unless the profit is large enough to pay for the moat).

Sort descending; human-review the top of the list each day.

---

## 6. The one-line gut check

> **Would I pay `B* × (1 + premium + tax) + logistics` in cash, today, to own this — and am I confident I can resell it for materially more, soon?**

If the comps are thin or the logistics are hand-wavy, the answer is no. Skip it; there's another auction tomorrow.
