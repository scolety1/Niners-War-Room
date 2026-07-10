# High-Value Signal Data Locator Audit V1 Report

## Verdict

`GREEN_HIGH_VALUE_SIGNAL_DATA_FOUND_WITH_EXECUTABLE_NEXT_LANE`

## Remote / Scope

- Canonical remote checked by lane preflight: `origin/work/hq-parallel-control`
- Expected/current HQ HEAD: `b125be9ee73f1adc3487c1fa69ae954e8e49790f`
- Artifact path: `C:\NWR\Niners-War-Room-high-value-signal-data-locator-audit-v1-20260709\docs\hq\data_hygiene\high_value_signal_data_locator_audit_v1_20260709`
- Search type: targeted read-only locator audit
- Formula execution: none
- Ranking/app/model/runtime behavior changes: none
- Source promotion: none
- Canonical `local_exports` writes: none

## Clear Answer

Useful high-value signal artifacts do exist locally, but most are not immediately formula-ready. The strongest executable next lane remains `PFR RB Broken Tackle Data Mart Join / Component Test V1`: it targets a narrow RB-only, review-only hypothesis that was already preserved by Master HQ but could not be scored because values were absent from the Formula Data Mart.

Historical market/ADP, rookie/draft-capital, team context, injury/availability, and broader role/depth/opportunity artifacts also appear in the locator results, but they need source/use-gate, as-of, identity, and schema review before entering formula tests.

## Signal Families Searched

- `Historical market / ADP`
- `Rookie / draft capital / prospect data`
- `Team / offensive environment`
- `Injury / availability point-in-time context`
- `Role / depth / opportunity change context`
- `PFR RB broken tackle values`
- `Red-zone historical expansion`


## Candidate Counts

- Candidate artifacts ledgered: `1247`
- Signal families searched: `7`
- Availability status counts: `{'AVAILABLE_NEEDS_SCHEMA_VALIDATION': 200, 'AVAILABLE_NEEDS_ASOF_REVIEW': 480, 'AVAILABLE_NEEDS_IDENTITY_REVIEW': 185, 'AVAILABLE_NEEDS_SOURCE_GATE': 333, 'AVAILABLE_REVIEW_ONLY': 2, 'AVAILABLE_BUT_CURRENT_ONLY': 35, 'MISSING_RECEIPT': 12}`
- Candidate counts by family: `{'pfr_rb_broken_tackle': 200, 'historical_market_adp': 200, 'rookie_draft_capital_prospect': 200, 'role_depth_opportunity_change': 200, 'team_offensive_environment': 47, 'injury_availability': 200, 'red_zone_historical_expansion': 200}`

## Highest-Value Data Found

`PFR RB broken-tackle` remains the highest-value executable data branch because it is narrow, public-source-derived through nflverse PFR advanced rushing context, already preserved as review-only, and not yet joined into the Formula Data Mart. Ledgered PFR rows: `200`.

## Market / ADP Read

Market/ADP artifacts were found (`200` ledger rows), but the locator did not prove historical point-in-time safety. Current-only or latest-market snapshots must not be backfilled into historical formula tests.

## Useful Data Already Present

- `PFR RB broken-tackle source/review artifacts are present and remain the most executable missing non-duplicate branch.`
- `Market/ADP artifacts are present but require point-in-time/as-of and source-gate review before formula testing.`
- `Rookie/draft/prospect artifacts are present but require source and identity gate review.`
- `Role archetype context is present and already review-only admitted; broader role/depth opportunity data remains gated.`


## Useful Data Missing Or Blocked

- `Historical/as-of safe market/ADP is not proven by this locator.`
- `Full historical red-zone coverage beyond the accepted partial 2024-2025 lane is not proven.`
- `Production/model-use, rankings integration, broad PFR, PFF Elusive, and nwr_elusive_proxy_review_only remain blocked.`


## Recommendation

Recommended next execution lane:

`PFR RB Broken Tackle Data Mart Join / Component Test V1`

Formula work should wait for a data upgrade rather than continue same-ingredient formula tweaking. Production/model-use and rankings integration remain blocked.
