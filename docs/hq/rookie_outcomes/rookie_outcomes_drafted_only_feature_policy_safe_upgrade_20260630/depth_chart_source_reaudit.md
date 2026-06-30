# Depth-Chart Source Re-Audit

Question: does approved tracked populated depth-chart data exist now?

Answer: no approved tracked populated depth-chart rows are present in the current target branch for this lane.

## Current Tracked Source Facts

| Source | Path | Row count/status | Policy |
|---|---|---:|---|
| nflverse depth chart weekly template | `templates/real_data_inputs/nflverse_stats_upgrade/nflverse_depth_chart_weekly.csv` | `0` | schema-only / pending |
| RotoWire May 22 depth-chart snapshot documentation | `docs/model_v4/ROTOWIRE_DEPTH_CHART_MAY22_SNAPSHOT.md` | `727_documented_not_tracked` | documentation-only; underlying local/vendor rows blocked |
| model_v4 depth chart snapshot service | `src/services/model_v4_depth_chart_snapshot_service.py` | code-only | blocked local/vendor source |

## Required Answers

- Teams/positions covered: `WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN` for nflverse refresh output; not available from tracked populated data here.
- Player IDs present: `WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN` for refresh output.
- Depth rank/order parseable: `WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN` for refresh output.
- Current-only or point-in-time historical: `WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN` for refresh output.
- Source policy status: review-only pending for public nflverse refresh receipts; blocked for local/vendor/RotoWire rows.
- Usable for review-only opportunity watchlist: not from current tracked populated rows; possible only after refresh-health green and source-policy review.
- Usable for historical modeling: no.
- RotoWire, local_exports, and vendor data: blocked.
- Previous zero-row conclusion superseded: no, not on this target branch.
