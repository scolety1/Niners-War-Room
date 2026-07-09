# nflverse Advanced Ingredient Availability / Formula Mart Gap Audit V1 Report

## Verdict

`GREEN_NFLVERSE_ADVANCED_INGREDIENTS_FOUND_WITH_EXECUTABLE_SIDECARE_LANE`

## Clear Answer

Useful public nflverse-family advanced ingredients are already present locally, and the highest-value executable lane is a review-only `ffopportunity` expected-fantasy-points sidecar. This audit does not run formulas, does not promote any source, and does not change rankings/app/model behavior.

## Remote / Prior Verification

- Current remote HQ HEAD verified before lane: `b125be9ee73f1adc3487c1fa69ae954e8e49790f`
- Prior PFR RB broken-tackle component-test commit verified: `843c17838caa020f5f123e6df5cd1fdd45d5b9c6`
- Prior PFR accepted result preserved: `RED_PFR_RB_BROKEN_TACKLE_NO_INCREMENTAL_SIGNAL`

## Scope Audited

- Ingredient families audited: `12`
- Families with local artifacts or prior-locator leads: `12`
- Families with public/rebuildable nflverse path or partial public path: `9`
- Candidate artifacts ledgered: `75`

## Highest-Value Present Data

`expected_fantasy_points_ffopportunity` is the highest-value immediately executable ingredient because local `ep_weekly` parquet files contain player-week expected fantasy points, expected yards, expected touchdowns, expected first downs, and actual-minus-expected fields for `2021-2024`.

## Other Useful Present Ingredients

- `next_gen_stats`: local QB/RB/WR/TE NGS files, mostly `2021-2023` plus tiny `2024` fragments; public NGS is rebuildable from `2016+`.
- `ftn_charting`: local `2022-2024` play-level charting files with motion, play-action, screen, RPO, catchable/drop/pressure-like fields.
- `receiving_opportunity_air_yards`: current mart and local advanced files contain useful receiving opportunity primitives, but WOPR/RACR/PACR need sidecar derivation.
- `qb_passing_quality`: NGS passing is useful; ESPN QBR and broad PFR passing are present locally but require separate source/use gates and are not admitted by this audit.

## Parked / Blocked

- PFR RB broken tackles remain descriptive RB review-only context only; no PFR-specific formula branch is recommended.
- Broad PFR, PFR QB passing production use, PFF Elusive Rating, and `nwr_elusive_proxy_review_only` remain blocked.
- Historical Market / ADP still has high future value, but it should sit behind nflverse ingredient sidecars until point-in-time/as-of safety is proven.
- Injury/availability remains point-in-time review context only and not injury prediction.

## Recommended Sidecar Order

1. `ffopportunity Expected Fantasy Points Formula Mart Sidecar V1`
2. `nflverse NGS Formula Mart Sidecar V1`
3. `nflverse EPA / Opportunity Formula Mart Sidecar V1`
4. `nflverse Receiving Opportunity Formula Mart Sidecar V1`
5. `FTN charting sidecar later`
6. `nflverse Snap Counts / Depth Chart Role Sidecar V1`
7. `Point-in-Time Injury Availability Data Mart Gate V1`
8. `Historical Market / ADP Source Gate and Data Mart Join V1`

## Decision

Formula testing should wait for an ingredient sidecar rather than more same-ingredient formula refinement. The next executable lane is `ffopportunity Expected Fantasy Points Formula Mart Sidecar V1`.

## Gates Preserved

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- App/runtime/model/ranking behavior did not change.
- No Formula Gauntlet, formula tuning, or production accuracy claim occurred.
- No canonical `local_exports` write occurred.
