# Artifact Manifest

All artifacts in this packet are review-only. They do not edit source truth, do not patch the original entry-status artifact, and do not approve training or model use.

## Input Artifacts Used

- `docs/hq/rookie_model/rookie_entry_status_hygiene_v1_20260630/historical_rookie_entry_status_v1.csv`
- `docs/hq/rookie_model/rookie_entry_status_hygiene_v1_20260630/undrafted_candidate_audit.csv`
- `docs/hq/rookie_model/rookie_entry_status_hygiene_v1_20260630/identity_collision_report.csv`
- `docs/hq/rookie_model/rookie_entry_status_hygiene_qa_v1_20260630/collision_overlap_audit.csv`
- `templates/real_data_inputs/nflverse_stats_upgrade/nflverse_depth_chart_weekly.csv`
- `templates/real_data_inputs/data_pack/dim_players.csv`
- `templates/real_data_inputs/data_pack/fact_rosters.csv`
- `docs/model_v4/ROTOWIRE_DEPTH_CHART_MAY22_SNAPSHOT.md` for inventory only; no vendor/local_export rows were read or tracked.

## Source Policy Status

- Tracked nflverse depth chart template has 0 rows.
- RotoWire/local_exports depth chart data is blocked for this lane.
- Missing depth chart data remains unknown, not low opportunity.
- Candidate output is header-only because no approved populated depth-chart artifact is available.

## Output Artifacts

| Artifact | Row Count | Purpose |
|---|---:|---|
| `docs/hq/rookie_model/rookie_depth_chart_nondrafted_watchlist_v1_20260630/artifact_manifest.md` | n/a | Packet manifest and source-policy status. |
| `docs/hq/rookie_model/rookie_depth_chart_nondrafted_watchlist_v1_20260630/depth_chart_nondrafted_watchlist_policy.md` | n/a | Defines review-only depth chart watchlist policy. |
| `docs/hq/rookie_model/rookie_depth_chart_nondrafted_watchlist_v1_20260630/depth_chart_source_inventory.csv` | 5 | Inventory of available depth chart and identity sources. |
| `docs/hq/rookie_model/rookie_depth_chart_nondrafted_watchlist_v1_20260630/depth_chart_nondrafted_candidate_watchlist.csv` | 0 | Candidate watchlist; header-only because approved depth rows are unavailable. |
| `docs/hq/rookie_model/rookie_depth_chart_nondrafted_watchlist_v1_20260630/depth_chart_ignore_summary.csv` | 4 | Position-level ignored-or-blocked summary. |
| `docs/hq/rookie_model/rookie_depth_chart_nondrafted_watchlist_v1_20260630/depth_chart_identity_blockers.csv` | 0 | Candidate identity blockers; header-only because no candidates surfaced. |
| `docs/hq/rookie_model/rookie_depth_chart_nondrafted_watchlist_v1_20260630/rookie_outcome_depth_chart_handoff.md` | n/a | Outcome handoff limits. |
| `docs/hq/rookie_model/rookie_depth_chart_nondrafted_watchlist_v1_20260630/final_depth_chart_watchlist_recommendation.md` | n/a | Verdict, counts, and next branch recommendation. |
| `docs/hq/rookie_model/rookie_depth_chart_nondrafted_watchlist_v1_20260630/merge_safety_report.md` | n/a | Guardrail and command evidence report. |

## What This Packet Does Not Approve

- No conversion from `likely_udfa_needs_review` to `confirmed_udfa`.
- No training, tuning, probabilities, app wiring, Gate F release, Gate G release, or Rankings wiring.
- No fake round 8, draft round 0, draft pick 0, or missing-as-zero logic.
