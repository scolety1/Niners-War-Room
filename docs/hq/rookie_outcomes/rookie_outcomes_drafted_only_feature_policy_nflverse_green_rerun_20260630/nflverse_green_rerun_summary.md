# NFLVerse Green Rerun Summary

Base HEAD: `2070a2f4ffa6b6ae83bd6ca1529880f67dd6cab0`

The required NFLVerse refresh-health artifacts are present on current `origin/work/hq-parallel-control`. The refresh-health implementation report is GREEN for dataset-level health/status reporting, and the player-context artifact is `YELLOW_PARTIAL_PLAYER_CONTEXT_ARTIFACT`.

## NFLVerse Evidence Found

- Dataset-level refresh-health folder: present.
- `src/services/nflverse_refresh_health_service.py`: present.
- `tests/test_nflverse_refresh_health_service.py`: present.
- Player-context display artifact: `294` rows.
- Safe player-context display rows: `240`.
- Identity review rows: `54`.
- Safe identity proposals: `43` proposals only.
- Needs human identity review: `4`.
- Keep identity review: `7`.

## Datasets Now Available As Review/Display Receipts

`draft_picks`, `combine`, `player_stats`, `rosters`, `weekly_rosters`, `ff_playerids`, `depth_charts`, `injuries`, `snap_counts`, `players`, `contracts`, and `teams` now have tracked receipt/status evidence through the NFLVerse player-context packet.

## Changed Versus Previous WAIT State

The first safe-upgrade lane classified NFLVerse-dependent items as `WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN`. That wait is now resolved for audit visibility: dataset receipts exist and can be referenced in review-only policy. It is not resolved for model use, training use, source truth, Gate G, or app behavior.

Depth-chart status changed materially: a populated tracked receipt exists in the player-context report, and `192` current player-context rows have a depth-chart position. This supersedes the old zero-row conclusion for review-only current opportunity context only.

## Still Blocked

- Model training/tuning/scoring.
- Active rookie probabilities.
- Gate G and Rankings/app wiring.
- UDFA modeling and UDFA confirmation from draft absence.
- CFBD model/training input.
- player_stats as label truth or input feature.
- depth chart, injury, snap, roster, and player_stats data as pre-draft/model features without explicit as-of/leakage gates.
