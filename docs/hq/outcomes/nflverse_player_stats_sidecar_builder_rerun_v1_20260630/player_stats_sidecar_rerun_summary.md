# Player Stats Sidecar Builder Rerun Summary

Verdict: `YELLOW_PLAYER_STATS_SIDECAR_BLOCKED_NEEDS_DERIVATION_RUNNER`

## Executive Summary

The rerun confirms that row-level NFLVerse player_stats source admission has landed GREEN for review-only future sidecar use:

- Verdict: `GREEN_PLAYER_STATS_ROW_LEVEL_SOURCE_ADMITTED_REVIEW_ONLY`
- Approved runner: `scripts/run_nflverse_refresh_v0.ps1`
- Datasets: `player_stats_weekly`, `player_stats_seasonal`
- Receipt rows: `2`
- Weekly rows: `76,804`
- Seasonal rows: `42,419`
- Weeks covered: `22`
- Schema manifest rows: `119`
- Quarantined fields: `12`

However, the sidecar artifact was not built. The approved runner created local-only raw source snapshots and explicitly skips normalization/candidate generation. The repo does not yet contain an approved sidecar derivation runner/service that can read the admitted local snapshot and emit a compact tracked review-only sidecar.

## Build Decision

`player_stats_sidecar_artifact.csv` was not created.

Reason: compact derivation requires a new approved runner/gate. Directly reading raw `C:\NWR_SHARED_DATA` snapshot files in this lane would bypass that gate.

## Source Receipts Used

| Dataset | Receipt SHA | Rows | Seasons | Weeks | Sidecar Builder Allowed | Review Use Allowed |
|---|---|---:|---|---:|---|---|
| `player_stats_weekly` | `a38c47ea830e6929e8de31d822496862d13873d13689ff90d2e50dac854901ba` | 76,804 | 2024-2025 | 22 | true | true |
| `player_stats_seasonal` | `57f76cfeee3211885f6d05504cc61b6529d023d5eb15a60ae21cc81c21c07b59` | 42,419 | 2024-2025 | 22 | true | true |

## Approval Boundary

The admission receipt allows review-only sidecar builder input. It does not allow label truth, model input, training input, source truth, app behavior, rank logic, hidden sort, recommendations, trade value, or pick value.

All approval columns in this packet remain false:

- `label_truth_allowed=false`
- `model_use_allowed=false`
- `training_allowed=false`
- `source_truth_allowed=false`

Because no compact sidecar rows were created, `sidecar_review_allowed=false` in this rerun coverage matrix.
