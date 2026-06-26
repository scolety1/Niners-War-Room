# CFBD Review Artifacts V1 - 2026-06-24

Run ID: `cfbd_review_artifacts_v1_20260624_20260626T075428Z`
Run timestamp: `2026-06-26T07:54:28Z`

These CFBD artifacts are review-only.

- `model_use_allowed=false`
- `training_allowed=false`
- `identity_review_required=true`
- `review_only=true`

CFBD data is not model input yet. Player identity matching must be reviewed before use.
Raw CFBD cache files are outside git under:

`C:\NWR_SHARED_DATA\public_sources\cfbd\cfbd_review_artifacts_v1_20260624_20260626T075428Z`

This lane is separate from nflverse and NFL data loader work. It does not promote CFBD
data into rankings, candidates, source-truth files, model logic, or training inputs.

## Artifacts

- `cfbd_pull_manifest.csv`
- `cfbd_player_identity_review_queue.csv`
- `cfbd_player_production_review.csv`
- `cfbd_coverage_report.csv`
- `cfbd_data_dictionary.csv`

## Coverage Summary

- Successful dataset-season pulls: 18 of 18
- Identity review rows: 31822
- Production review rows: 16938
- Optional recruiting rows cached for coverage only: 8162

## Known Limitations

- Roster identity is team-scoped because the all-roster query returned no rows in smoke.
- 2026 roster and player-production availability depends on CFBD's current-season coverage.
- V1 does not automatically match CFBD players to NWR or Sleeper identities.
- Optional recruiting data is cached and counted, but not promoted to a player-level
  tracked recruiting artifact in V1.

## Missing Endpoints Or Seasons

- cfbd_player_season_stats_passing 2026: 0 rows returned by CFBD for this season/query.
- cfbd_player_season_stats_rushing 2026: 0 rows returned by CFBD for this season/query.
- cfbd_player_season_stats_receiving 2026: 0 rows returned by CFBD for this season/query.
- cfbd_roster_player_identity 2026: 0 rows returned by CFBD for this season/query.
