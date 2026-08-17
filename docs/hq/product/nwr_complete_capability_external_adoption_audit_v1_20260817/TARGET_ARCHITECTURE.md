# Target Architecture

## Shared platform

- `LeagueWorkspace`: immutable mode, platform, league, season, scoring and roster-slot identity.
- `PlayerIdentityRegistry`: stable NWR IDs and evidenced provider crosswalks.
- `SleeperReadAdapter`: cached, rate-aware league/roster/draft/pick/transaction/player facts; no writes.
- `ProviderRegistry` + immutable `SourceSnapshot`: terms receipt, hash, scope, generated/fetched time, coverage, freshness and fallback.
- `LeagueAvailability`: active rostered/unrostered state projected from exact IDs.
- `OwnerStore`: local atomic state, locks, backups, migrations and separate Dynasty/Redraft roots.
- `AuthorityLedger`: explicit `Official`, `Market`, `War Room`, `My Rank`, research and missingness labels.

## Dynasty

Finished V1 remains veteran production authority; Rookie Review, Outcome V3, Unified Research and Market remain separate. Multi-authority comparison and Trade Decision Assistant compose evidence without blending. Planning, scenarios and decision history become owner-visible task flows. Weekly/waiver features reuse the shared platform only where Dynasty owner value is clear.

## Redraft

Redraft Champion remains projection/rank authority. Add provider-neutral ADP, position-first tiers, an event-sourced Draft Room, seeded ADP/history CPU mocks, Beat ADP timing, live companion, legal weekly lineup, waivers and streamers. Redraft trades are secondary and reuse NWR trade contracts if owner-approved.

## UI boundary

The two installed apps may stay separate. Both call shared application services; UI and optional assistant never duplicate domain logic. Labs, raw receipts and technical controls live under System/Development, not Owner navigation. Offline last-known snapshots remain usable and visibly stale.
