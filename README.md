# GovWinner

A systematic pipeline for finding **underpriced lots in U.S. government & industrial surplus auctions** and turning them over for profit.

## The thesis (in one chart)

A widely-shared analysis of ~70,000 completed U.S. government auctions found that **~40% get zero or one bid**, and that price and competition are tightly correlated:

- **Cheap stuff sells to whoever bothered to show up.** A $10 Husqvarna mower had one bidder.
- **Obviously valuable, liquid stuff gets fought over.** A pallet of 125 iPhones drew 248 bidders — by the time it clears, there's no margin left.
- **The money is in the outliers:** high underlying value, almost no competition. "A whole school" sold for $250,000 to a *single bidder*.

GovWinner exists to **industrialize the search for that third quadrant** — real value, thin competition — and to apply disciplined max-bid math so we only win the lots that pay.

```
   bids
   high │            . . . :::::::::          <- crowded, efficiently priced
        │        . . :::::::::::::::            (NO MARGIN — avoid)
        │     . :::::::::::::::::: .
        │   :::::::::::::::: . .  .
        │ :::::::::: . .  .   .  .   ★         <- THE TARGET ZONE
   low  │:::::: . .  .  .  .  .  .  .  ★          high value, few bidders
        └────────────────────────────────────
         $1      $100     $1k    $10k   $100k+   final sale price
```

We deliberately **do not** compete in the top-left-to-top-right band (popular consumer categories where the auction has already found fair value). We hunt the bottom-right.

## Why thin-competition lots exist

Mispricing is created by *friction*. Each type of friction is a filter we can exploit:

| Friction | Why bidders stay away | How we exploit it |
|---|---|---|
| **Liquidity / size** | Too big, niche, or capital-heavy for hobbyists (a school, a production line) | Have capital + buyers lined up for specific categories |
| **Geography** | Located on a military base or remote site; expensive to reach | Pre-build logistics so pickup cost is known, not scary |
| **Information** | Bad listing: no photos, vague/misspelled title, wrong category | Read better than the average bidder; search by model across categories |
| **Timing** | Closes at an odd hour with a short removal window | Automated monitoring + sniping |
| **Knowledge** | Specialized gear whose value only insiders know | Build comp data per category so we *are* the insider |

## What's here

- **[docs/screening-plan.md](docs/screening-plan.md)** — the screening funnel, the deal-scoring math, and the build roadmap (manual → semi-automated → automated). **Start here.**
- **[docs/sources.md](docs/sources.md)** — catalog of auction platforms, what they're good for, and how to ingest their listings.
- **[docs/valuation-and-scoring.md](docs/valuation-and-scoring.md)** — the all-in cost model, max-bid formula, and deal score.
- **[docs/buy-box.md](docs/buy-box.md)** — the explicit criteria that define what we will and won't pursue (fill this in before bidding on anything).

## First principles

1. **Margin is made on the buy, not the sale.** The max bid is computed *before* we ever look at the live price.
2. **Competition is the enemy of margin.** Bid count is a primary filter, not an afterthought.
3. **All-in cost is the real price.** Buyer's premium + tax + removal + transport + refurb + resale fees routinely add 30–60% on top of the hammer price.
4. **Logistics is the moat.** Most bidders can't get a 2-ton lot off a base 600 miles away. If we can, the competition self-selects out.
