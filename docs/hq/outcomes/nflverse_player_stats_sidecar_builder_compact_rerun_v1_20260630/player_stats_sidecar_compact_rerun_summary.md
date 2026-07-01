# Player Stats Sidecar Compact Rerun Summary

Verdict: `GREEN_PLAYER_STATS_SIDECAR_BUILT_REVIEW_ONLY_FROM_COMPACT_CANDIDATE`

## Executive Summary

The official tracked review-only NFLVerse player_stats sidecar artifact was built from the merged compact sidecar candidate.

## Counts

- Source compact candidate rows: `13,628`
- Official sidecar rows created: `13,628`
- Unique NWR players: `233`
- Derived dataset: `player_stats_weekly`
- Seasons covered: `2024-2025`
- Weeks covered: `1-22`
- Positions covered: `K, QB, RB, TE, WR`

## Stat Families

- `passing_first_downs`: `1,580`
- `receiving_first_downs`: `7,350`
- `rushing_first_downs`: `4,698`

## Source Receipts

- Weekly receipt: `76,804` rows, SHA `a38c47ea830e6929e8de31d822496862d13873d13689ff90d2e50dac854901ba`
- Seasonal receipt: `42,419` rows, SHA `57f76cfeee3211885f6d05504cc61b6529d023d5eb15a60ae21cc81c21c07b59`

The compact candidate uses weekly player_stats only. Seasonal receipt evidence remains admitted review-only source context but is not emitted into this V1 sidecar artifact.

## Guardrails

- Sidecar rows are comparison substrate only.
- Sidecar rows are not labels.
- Sidecar rows are not model features.
- Sidecar rows are not source truth.
- Existing labels remain evaluation targets, not inputs.
- Missing data remains `Not enough information`.
- Absence from the compact sidecar is not zero production.
- Quarantined fields are not used.
