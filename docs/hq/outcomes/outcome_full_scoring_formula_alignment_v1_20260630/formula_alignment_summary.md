# Formula Alignment Summary

## Executive verdict

`GREEN_FORMULA_ALIGNMENT_READY_FOR_OBSERVED_ROW_BUILDER`

The NWR/Outcome scoring formula can be aligned to safe NFLVerse `player_stats` component fields for a future observed-row full sidecar builder, with explicit composite rules.

## Formula source

The canonical config is `config/nwr_scoring_rules_nwr_1qb_nonppr_fd_v1.json`, implemented by `src/services/nwr_outcome_scoring_service.py` and corroborated by `scripts/build_backtest_dataset_v0.py`.

Core scoring roles:

- passing yards, touchdowns, interceptions, and two-point conversions;
- rushing yards, touchdowns, first downs, and two-point conversions;
- receiving yards, touchdowns, first downs, and two-point conversions;
- lost fumbles;
- return yards;
- special/return touchdowns;
- fumble recovery touchdowns;
- misc yards and zero-weight context fields where present.

## Decision

A future observed-row builder may include safe direct component fields and the approved composite rules in this packet. It must not use quarantined fantasy totals, EPA/CPOE/share-style fields, headshot/display fields, market, ADP, projections, or model/rank fields.

## Remaining boundary

This packet does not solve zero-row completeness. Missing component rows remain `Not enough information` unless a later zero-row gate proves explicit player-week zeros.
