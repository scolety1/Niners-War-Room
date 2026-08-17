# Core Data Source Findings

## Keep

- Sleeper official API for free read-only league, roster, draft, pick, transaction and player identity facts. It has no token and documents a call-rate guideline; cache and respect it.
- nflverse governed snapshots for the NFL statistical data NWR already uses. The `nflverse-data` release repository is CC BY 4.0; individual datasets/packages and underlying rights must still be checked and attributed.
- Existing NWR production artifacts and exact receipts as primary local authority.

## Add only through provider registry

- Owner-imported ADP and projections with immutable hashes.
- Optional FantasyPros keyed endpoints when owner approves entitlement/terms and fallback behavior.
- Injury, weather, odds or news sources only when they have explicit licenses/terms, identity coverage, timestamp/freshness, outage behavior and evidence labels.

## Reject as implicit sources

GitHub snapshots without a license, scraping workflows, stale notebooks, app-client internals presented as official APIs, and any paid source made mandatory. Every provider snapshot must declare source, scope, generated/fetched time, content hash, identity coverage, missingness and freshness status.
