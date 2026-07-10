# Formula Data Mart / Feature Availability Audit V1 Report

## Verdict

`YELLOW_FORMULA_DATA_MART_PARTIAL_COMPONENT_ONLY`

## Clear Answer

NWR has enough joined, leakage-safe, review-only historical data to build a small component-test data mart, but not enough complete/source-cleared data for a 50-100 candidate Formula Gauntlet sprint or rankings integration.

## Data Mart Result

- Rows: `5518`
- Season coverage: `2013-2025`
- Position coverage: `QB=754|RB=1429|WR=2124|TE=1211`
- Grain: `player_id + season + position`
- Allowed scope: `review_only_component_signal_tests_only`

## Feature Availability Summary

- Feature families audited: `40`
- Actual value families in mart: `23`
- Review-only allowed families: `25`
- Blocked/missing families: `13`

## Highest-Value Available Features

- PYF/prior-year points baseline
- historical fantasy labels and startable labels
- lagged passing/rushing/receiving volume stats
- lagged first-down proxy fields
- offensive snaps/opportunity/touches
- role archetype guardrail/miss taxonomy
- confidence-cap caution/coverage context

## Highest-Priority Missing Upgrades

- route/YPRR/TPRR exact receipts
- return scoring receipts
- red-zone exact receipts
- shadow_model_v2_metrics.csv
- exact historical checkpoint and position-specific Model v4 receipts
- age/lifecycle sidecars
- historical point-in-time injury/market gates

## Formula Sprint Decision

Enough data exists for review-only component signal tests. Enough data does not exist for a 100-candidate Formula Gauntlet, champion refinement, rankings integration, production/model-use, or exact Model v4 historical replay.

## Production Status

- Exact Model v4 replay remains blocked.
- Formula Gauntlet tournaments remain blocked.
- 100-candidate Gauntlet remains blocked.
- Champion refinement remains blocked.
- Rankings integration remains blocked.
- Production/model-use remains blocked.
- No source was promoted.
