# Outcome V2 5Y Data Source Gate

## Decision

`EXTEND_LABEL_WINDOW_ALLOWED`

## Why This Is Allowed

The source policy already allows the source family needed for this narrow lane:

- `docs/hq/data_sources/nfl_usage/NWR_NFL_USAGE_SOURCE_CONTRACT_V0_20260624.md` allows nflverse/nflreadpy public structured data, including player stats.
- `docs/hq/data_sources/nfl_usage/target_backtest/NWR_NFL_USAGE_HISTORICAL_EXPANSION_STRATEGY_20260624.md` explicitly states that `player_stats`, `pbp`, and `snap_counts` can be pulled farther back through nflreadpy and cached outside git.
- `docs/hq/data_sources/nfl_usage/NWR_NFLREADPY_DEPENDENCY_APPROVAL_20260624.md` documents nflreadpy dependency approval.

This lane uses only `nflreadpy.load_player_stats(seasons, summary_level="reg")`.

## Raw Cache Policy

All raw/generated data remains outside the repository:

- Source/audit cache: `C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_source_audit\nflreadpy_cache\`
- Generated extended label outputs: `C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels_extended\`

No raw cache, shared-data CSV, generated label CSV, local export, or secret file is intended to be tracked.

## Scoring Status

Decision: exact first-down scoring can be computed for the pulled player-season rows.

The targeted 2012 and 2017 smokes found:

- `passing_first_downs`
- `rushing_first_downs`
- `receiving_first_downs`

The extension therefore uses scoring mode:

`exact_verified_first_downs`

No missing first-down approximation is used.

## Scope Boundaries

Allowed in this lane:

- Review-only historical target label extension.
- 5Y coverage recalculation.
- Source-policy documentation.
- Tests for label math and missing-window behavior.

Not allowed in this lane:

- Rankings changes.
- Outcome Lens changes.
- Current-player probabilities.
- Rookie/prospect probabilities.
- Model input promotion.
- Source-truth promotion.
- Market/ADP/DynastyProcess inputs.
- CFBD inputs.
- Vendor/Gmail data.
- Trade or pick valuation.

## Promotion Status

This source gate does not approve app display or model use. It only approves a historical coverage extension under review-only guardrails.

All generated rows must keep:

- `approval_status=review_only_historical_labels`
- `model_input_allowed=no`
- `training_allowed=no`
- `app_wiring_allowed=no`

## Gate Result

Phase 1 is GREEN for a narrow historical label extension.
