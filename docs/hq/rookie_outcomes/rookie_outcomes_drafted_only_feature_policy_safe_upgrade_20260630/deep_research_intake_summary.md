# Deep Research Intake Summary

The handoff report concludes that Rookie Outcomes is not production-ready but may continue as drafted-only, review-only policy and readiness work. This lane implements safe policy artifacts and tests only.

## Accepted Safe-Now Changes

- RO-001: drafted-only admission is defined as positive `draft_picks` evidence only.
- RO-002: synthetic round/pseudo draft capital is quarantined outside drafted-only buckets.
- RO-004: Gate E feature-policy manifest now names the replay-service feature contract and the six Gate E features.
- RO-006: Gate F is restated as partial display-only/review-only.
- RO-010: Gate G remains closed.

## WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN Items

- RO-003: nflverse `player_stats` sidecar labels.
- RO-009: dataset-level nflverse receipts for `draft_picks`, `combine`, `player_stats`, `rosters`, `weekly_rosters`, `ff_playerids`, `depth_charts`, `snap_counts`, and `injuries`.
- Depth-chart row counts, teams, positions, and parseable rank/order from refreshed nflverse data.

The target branch contains older refresh machinery, but no tracked merged refresh-health packet proving dataset-level receipts for this lane. Therefore refresh-dependent implementation is held.

## NEED_MODEL_GATE Items

- Gate E model R&D refresh, tuning, calibration promotion, or current-player scoring.
- Any expansion beyond the six named Gate E features.
- Any promotion of labels from evaluation targets to training truth.
- Any use of combine/depth/roster/snap/injury fields as model inputs.

## BLOCKED Items

- UDFA/non-drafted modeling.
- CFBD model input or training truth.
- Gate G, Rankings wiring, app-facing rookie columns, or hidden sort behavior.
- FootballDB/vendor/Gmail/RotoWire/FantasyPros/private source ingestion.

## Repo-State Conflicts Resolved

- Label-source split is resolved by naming Outcome V2 as review-only historical target/evaluation, model_v4 RotoWire-derived labels as local display-only comparison, and nflverse player_stats as a future sidecar only.
- Feature-policy split is resolved by treating the replay service's nine fields as review-only/replay-contract fields unless a later model gate approves them; only six Gate E names are marked as part of the current cap.
- Source-policy split is resolved by defaulting all new nflverse refresh outputs to review-only receipts until a later gate.

## Stale-Source Conclusions

The tracked source reconciliation still reports no approved populated tracked depth-chart data: the nflverse depth-chart item is schema-only with zero rows, and RotoWire depth-chart material remains local/vendor-blocked. Because the refresh-health lane is not landed as a tracked packet here, the prior populated-depth conclusion is not superseded.
