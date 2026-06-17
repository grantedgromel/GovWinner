# Systematic Screening Plan

The goal: process a large volume of surplus-auction listings cheaply, and surface the small handful that are **underpriced relative to verifiable resale value, with thin competition**. Everything below is built to be done by hand first, then automated piece by piece once the economics are proven.

---

## The funnel

We move from "everything for sale" to "lots we'll actually bid on" through a series of progressively more expensive filters. Cheap filters run first so we never spend human attention (or comp lookups) on lots that fail an obvious gate.

```
  Stage 0  Buy-box            define what we'll pursue (one time, then revisit)
              │
  Stage 1  Ingest             pull all listings from target platforms
              │   (thousands/day)
  Stage 2  Coarse filter      cheap rules: category, price band, geography, time-to-close, bid count
              │   (hundreds)
  Stage 3  Mispricing signals flag bad-listing / low-competition tells
              │   (dozens)
  Stage 4  Valuation          comp against resale markets, compute all-in cost & max bid
              │   (dozens, now with $$$)
  Stage 5  Risk + logistics   condition, access, removal deadline, transport quote
              │   (10–20 shortlist)
  Stage 6  Human review       eyeball photos, read fine print, sanity-check comps
              │   (3–8 to bid)
  Stage 7  Bid & snipe        place disciplined max bid; snipe near close
              │
  Stage 8  Settle & resell    pay, remove, refurb, list, ship
              │
  Stage 9  Feedback loop      log outcome; refine clearing-price model & buy-box
```

---

## Stage 0 — Buy-box (do this first)

You cannot screen without criteria. Before any bidding, fill in **[buy-box.md](buy-box.md)**:

- **Capital per deal** and total capital at risk at once.
- **Categories we understand** (where we can comp value and have resale channels). Start with **1–2 categories**, not ten.
- **Geography** we can physically reach / arrange freight to, and the max logistics cost we'll absorb.
- **Minimum net ROI** per deal (e.g. 40% net, or a 1.7× return after *all* costs) — this is the hurdle every lot must clear.
- **Hard nos** (hazmat, titled vehicles if we can't handle DMV, anything needing a license we don't have, anything requiring "being in the line of work").

The buy-box is the single most important artifact. A tight buy-box is what lets the rest of the funnel run on autopilot.

---

## Stage 1 — Ingest

Pull listings from the platforms in **[sources.md](sources.md)**. Order of preference:

1. **Official APIs / bulk data exports** (e.g. GSA's structured data). Cheapest, most reliable, ToS-clean.
2. **RSS feeds / saved-search email alerts.** Most platforms (GovDeals, AllSurplus) let you save a filtered search and get notified — this *is* a free ingestion pipeline in Phase 1.
3. **Scraping** — only where permitted. **Respect robots.txt and each site's Terms of Service**; prefer the methods above. Several industrial sites prohibit scraping outright.

Normalize every listing into one record:

```
listing_id, platform, url, title, description, category, photos[],
current_price, bid_count, closes_at, location (state/base/zip),
condition, removal_deadline, buyers_premium_pct, seller
```

---

## Stage 2 — Coarse filter (cheap rules)

Drop anything that fails a buy-box gate. These are pure field comparisons — fast and free:

- **Category** ∈ buy-box categories.
- **Geography** reachable, OR value high enough to justify long-haul freight.
- **Price band**: above floor (skip $10 junk that can't clear a profit after fees) and below capital ceiling.
- **Time-to-close**: enough runway to comp and arrange logistics, but flag "closes soon, still cheap" as a positive signal (see Stage 3).
- **Bid count**: this is a primary lever. **Prefer 0–3 bids.** A lot already at 15 bids is being efficiently priced — usually skip.

> Rule of thumb from the data: the value lives where **bid count is low but the item is not junk**. A high bid count is the auction telling you there's no margin left.

---

## Stage 3 — Mispricing signals

Among the survivors, up-rank lots showing tells that they're *underexposed* (few bidders will find or understand them):

- **Poor listing quality** — few/no photos, two-line description, generic title ("misc lot," "assorted"). Bad listings correlate strongly with low bids; if *we* can tell what it is, we have an edge.
- **Miscategorization / typos** — search by brand+model *across* categories; a Snap-on toolbox filed under "office furniture" is invisible to most searchers.
- **Vague bulk lots** — "pallet of assorted electronics" where the visible contents already exceed the current price.
- **Mislabeled condition** — "as-is / for parts" on items that are likely functional (very common for gov surplus that's simply untested).
- **Closes-soon-and-still-cheap** — low price with little time left and few bids = the market missed it.
- **Geographic isolation** — on a base / remote site. This *raises* our edge (fewer bidders) as long as our logistics math (Stage 5) still works.

---

## Stage 4 — Valuation & max bid

Now we spend real effort (comp lookups cost time/API calls). For each survivor, compute the numbers in **[valuation-and-scoring.md](valuation-and-scoring.md)**:

1. **Net resale value `R`** — median of comparable *sold* prices (eBay sold/Terapeak, dealer/market value, scrap value as a floor), minus marketplace fees and a risk haircut.
2. **All-in cost `C(B)`** at a hypothetical winning bid `B` — hammer + buyer's premium + sales tax + removal/labor + transport + refurb + storage + our time.
3. **Max bid `B*`** — the highest bid where the deal still clears our minimum ROI hurdle. **This is set before we watch the live auction.**
4. **Expected clearing price** — estimate from historical lots with similar category/value/bid-trajectory. If `B* < expected clearing price`, we'll likely get outbid into unprofitability → **deprioritize** (don't waste attention on lots we can't win profitably).

Only lots where **`B*` > current price** *and* **`B*` ≥ expected clearing price** advance.

---

## Stage 5 — Risk & logistics

Turn the abstract winners into executable deals:

- **Condition risk** — how confident are we in `R`? Untested/"as-is" gets a bigger haircut.
- **Access & removal** — base access requirements, appointment-only pickup, equipment needed (forklift?), and the **removal deadline** (miss it and you forfeit the lot *and* the payment — a classic gov-auction trap).
- **Transport quote** — get a real freight/transport number for anything that won't fit in a vehicle. This is where most paper-profit deals die; do it before bidding, not after.
- **Title / paperwork** — vehicles, trailers, anything needing registration.

---

## Stage 6 — Human review

The shortlist (target ~10–20/day at steady state) gets eyes-on:

- Zoom into every photo; read the entire description and seller terms.
- Sanity-check the comps (are we comparing to the right model/condition?).
- Confirm the removal deadline is survivable.
- Approve a **max bid** and a **walk-away** — and write them down.

---

## Stage 7 — Bid & snipe

- Place the approved **max bid only**. Never chase past it in the moment — the margin math doesn't move just because someone else wants it.
- **Snipe**: enter the binding bid late to avoid driving up the price early and to avoid emotional escalation. (Note many gov platforms use *soft close* / anti-sniping extensions — plan for that; sniping helps less when the clock auto-extends, so discipline on the max bid matters more.)

---

## Stage 8 — Settle & resell

Pay immediately, schedule removal **well inside** the deadline, refurb/clean/test, photograph well (our listing quality is now *our* edge on the sell side), and list on the channel with the best net.

---

## Stage 9 — Feedback loop

Every lot — won or lost — gets logged:

```
predicted_clearing, actual_clearing, predicted_R, realized_R,
all_in_cost, net_profit, days_to_resell, category, platform, friction_type
```

This is the dataset that (a) sharpens the clearing-price model, (b) tells us which **categories and platforms actually pay**, and (c) tightens the buy-box. Over time the funnel gets more selective and more accurate.

---

## Build roadmap (crawl → walk → run)

Prove the economics by hand before writing a single scraper.

### Phase 1 — Manual (Week 1–2)
- Fill in the buy-box. Pick **one platform** (GovDeals or AllSurplus) and **one category**.
- Use saved searches / email alerts for ingestion. Track candidates in a spreadsheet with the Stage 4 math.
- **Make 1–2 small test buys** specifically to learn the *real* fees, removal process, and logistics for your area. This calibrates every number in the model.

### Phase 2 — Semi-automated (Week 3–6)
- Script ingestion from RSS/exports into the normalized record format.
- Spreadsheet/notebook valuation with semi-automated comp lookups (eBay sold, etc.).
- Daily auto-generated shortlist; human does Stages 5–7.

### Phase 3 — Automated pipeline
- Proper ingestion across platforms (API where available, compliant scraping elsewhere), dedupe, storage.
- Comp engine + scoring service producing a ranked daily shortlist with alerts.
- Bid execution + outcome logging.

### Phase 4 — Learning system
- Train the clearing-price predictor on logged outcomes.
- Auto-tune category/platform allocation toward what actually nets profit.

**Gate between phases:** don't automate a stage until the manual version has produced consistently profitable buys. Automation scales whatever you've got — make sure it's profit, not a leak.
