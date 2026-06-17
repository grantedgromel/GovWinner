# Source Platforms

The auction landscape, what each is good for, and how to ingest listings. Platforms in **bold** are the recommended starting points.

> **Compliance note:** Always prefer official APIs, data exports, and saved-search/RSS alerts. Where you scrape, **respect each site's robots.txt and Terms of Service** — several industrial platforms prohibit automated access. Ingestion method notes below are about *what exists*, not a license to ignore ToS.

## Government surplus

| Platform | Sweet spot | Notes on access / quirks |
|---|---|---|
| **GovDeals.com** | State/local + some federal surplus; vehicles, equipment, IT, misc. The volume play. | Formerly tied to GovLiquidation branding. Saved searches + email alerts. Widely distributed locations (not only bases). Operated by Liquidity Services. |
| **AllSurplus / AllSurplus Deals** | Broad commercial + government surplus, retail returns, bulk lots. | Also Liquidity Services. Good for general-category bulk lots and the "vague pallet" mispricing play. |
| **GSAAuctions.gov** | Federal civilian-agency surplus (vehicles, IT, equipment, even real property). | Run by GSA. The most *structured* data — best target for an official/bulk ingestion path. |
| **GovPlanet / GovLiquidation** | Ex-military rolling stock, heavy equipment, vehicles, parts. | Ritchie Bros / IronPlanet network. Higher ticket; logistics-heavy (often on bases). |
| Municibid | Municipal/local government surplus. | Smaller markets = thinner competition. |
| PublicSurplus | Schools, counties, municipalities. | Good for niche institutional gear; uneven listing quality (= opportunity). |
| U.S. Treasury auctions (CWS Marketing) / U.S. Marshals | Seized & forfeited assets (vehicles, jewelry, real estate). | Episodic; specialized. |

## Industrial / commercial

| Platform | Sweet spot | Notes on access / quirks |
|---|---|---|
| **Salvex** | Industrial, energy, marine, distressed inventory. | Big lots. "You gotta be in the same line of work" — value is real but specialized; only play categories you can comp and resell. |
| **Iron Horse Auctions** | Factory gear, industrial liquidations. | NC-based; lots of plant/factory equipment. |
| AllSurplus (again) | Crosses into commercial/industrial too. | See above. |
| HiBid / Proxibid | Aggregators hosting many regional auction houses. | Huge volume, very uneven listing quality — strong territory for the bad-listing mispricing signal. |

## Aggregators / data

| Source | Use |
|---|---|
| **GovAuctions.app/research** | The source of the thesis chart. Useful as a research/benchmark reference for completed-auction price↔bid distributions. |

---

## Ingestion priority by phase

- **Phase 1 (manual):** GovDeals **or** AllSurplus, one category, via saved-search email alerts.
- **Phase 2 (semi-auto):** add GSAAuctions (structured data) + RSS/exports from the Phase 1 platform.
- **Phase 3 (auto):** broaden across the table above, API-first, compliant scraping only where needed, with dedupe across platforms (the same lot or same seller's inventory can appear in multiple places).

## Fee reality check (verify per platform — these move)

Build the *actual* current numbers into [valuation-and-scoring.md](valuation-and-scoring.md); don't trust memory:

- **Buyer's premium** is common and material (often ~10–15%, sometimes capped). It is charged on top of your hammer price.
- **Sales tax** typically applies unless you have a resale certificate — get one.
- **Removal deadlines** are strict and forfeiture is real. Treat the deadline as a hard logistics constraint, not a suggestion.
