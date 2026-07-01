# Observed-Row Full Scoring Sidecar Summary

## Verdict

`YELLOW_OBSERVED_ROW_FULL_SCORING_SIDECAR_PARTIAL_COMPONENT_BLOCKERS`

The builder created a compact review-only observed-row scoring component sidecar from the admitted local-only `player_stats_weekly` source.

## Counts

| Metric | Count |
| --- | ---: |
| Raw QB/RB/WR/TE observed source rows | 24,898 |
| Safe identity observed rows used | 12,268 |
| Safe mapped players | 232 |
| Sidecar component rows created | 90,092 |
| Nonzero component rows | 54,986 |
| Explicit zero component rows | 35,106 |
| Identity-skipped observed rows | 12,630 |

## Compact V1 boundary

The artifact emits all nonzero observed scoring components for safely mapped QB/RB/WR/TE rows. It also emits explicit zero rows for the three composite blocker components: `fumbles_lost`, `return_yards`, and `return_or_special_touchdowns`.

Direct zero expansion for every component is not emitted in compact V1. Missing player-week rows remain `Not enough information`, never zero.
