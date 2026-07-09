# Historical Market / ADP Next Use Decision

Decision: `AVAILABLE_NEEDS_ASOF_PROOF`

Secondary status: `AVAILABLE_DISPLAY_ONLY_CURRENT`

Historical market / ADP artifacts exist, but the source/as-of gate did not pass. No review-only Formula Data Mart sidecar may be built from the current evidence, and no formula tests may run from these sources.

## Allowed Now

- Display-only market-awareness review from already-governed DynastyProcess and Sleeper packages.
- Source-policy review of market/ADP licensing, cache handling, identity joins, and stale/current labels.
- Manual search for a true historical market/ADP panel with row-level as-of dates.

## Blocked Now

- Historical formula input.
- Current-only ADP backfill into prior seasons.
- 2026 market value as a 2013-2025 feature.
- Model training, hidden sort, recommendations, ranking integration, production/model-use, or app/runtime wiring.

## Sidecar/Test Decision

- Sidecar built: `no`
- Component tests run: `no`
- Formula x ingredient tests run: `no`
- Bounded combinations run: `no`

## Recommended Next Lane

`Rookie Draft Capital Data Mart Join / Component Test V1`

Market/ADP should reopen only when a true historical/as-of-safe source is available or when Master HQ approves a narrow source-gate lane for a specific historical provider.
