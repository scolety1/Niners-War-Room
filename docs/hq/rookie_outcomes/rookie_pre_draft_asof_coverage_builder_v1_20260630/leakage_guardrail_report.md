# Leakage Guardrail Report

All rows keep `experiment_ready_now=false`, `model_use_allowed=false`, `training_allowed=false`, and `source_truth_allowed=false`.

Required before future experiment design:

- prediction anchor;
- source extraction timestamp;
- feature as-of timestamp;
- point-in-time replay manifest;
- identity-safe join manifest;
- missingness policy;
- leakage audit;
- class-year split plan;
- label/feature separation proof;
- blocked-source scan.

Post-draft/current fields remain blocked as pre-draft features: rosters, weekly_rosters, injuries, depth charts, snap_counts, player_stats, schedules, contracts, current team/status, and Outcome V2 labels. Missing values remain `Not enough information`, never zero, false, clean, healthy, low-risk, or confirmed UDFA.
