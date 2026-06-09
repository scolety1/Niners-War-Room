# Phase 10D Prospect Source Snapshot

Generated: 2026-05-17T21:32:54+00:00

## Scope

Phase 10D snapshots the separate rookie/prospect package into the main Model v4
source system. This is a source-governance phase only.

No formula weights, rankings, My Team, War Board, app promotion state, or
readiness gates were changed.

## Snapshot Location

- Snapshot root: `C:\Dev\niners-war-room\local_exports\model_v4\prospect_sources\latest`
- Manifest CSV: `docs/model_v4/PHASE_10D_PROSPECT_SOURCE_SNAPSHOT.csv`

## Source Groups

| Source group | Files | Bytes | Source-limited files |
| --- | ---: | ---: | ---: |
| cfbd | 9 | 26,480,318 | 9 |
| fantasypros | 2 | 21,158 | 0 |
| kaggle_nfl_draft | 15 | 108,375,371 | 15 |
| market | 4 | 15,260 | 0 |
| rotowire_cfb | 41 | 24,083,104 | 0 |
| rotowire_context | 8 | 601,102 | 0 |
| third_party_combine | 10 | 8,943,641 | 10 |

## Included Source Lanes

- CFBD processed player/team/market-share/recruiting/draft tables.
- CFBD raw extraction manifests.
- RotoWire CFB stats, targets, advanced team stats, and CFB injury tables.
- RotoWire workouts, NFL depth chart, rookie ranking, and NFL injury context tables.
- FantasyPros ADP and rookie/market ADP context.
- Kaggle NFL Draft 2026 archive and extracted files.
- Third-party combine/pro-day raw and processed files.

## Guardrails

- These files are staged as source evidence/context only.
- Market, ADP, ranking, and watchlist files remain context-only.
- RotoWire exports are local subscription exports and must not be redistributed.
- Third-party combine/pro-day files are source-limited because no license was
  found in the downloaded repository files.
- Kaggle license was user-reported as CC0 Public Domain; verify before
  redistribution.
- No prospect data is blended into Model v4 formulas in this phase.

## Source-Limited Notes

- `cfbd` / `college_market_share.csv`: source_limited_local_snapshot - CFBD API export; verify source terms before redistribution.
- `cfbd` / `college_player_category_summary.csv`: source_limited_local_snapshot - CFBD API export; verify source terms before redistribution.
- `cfbd` / `college_player_seasons_wide.csv`: source_limited_local_snapshot - CFBD API export; verify source terms before redistribution.
- `cfbd` / `college_team_seasons_wide.csv`: source_limited_local_snapshot - CFBD API export; verify source terms before redistribution.
- `cfbd` / `draft_picks.csv`: source_limited_local_snapshot - CFBD API export; verify source terms before redistribution.
- `cfbd` / `recruiting_players.csv`: source_limited_local_snapshot - CFBD API export; verify source terms before redistribution.
- `cfbd` / `roster.csv`: source_limited_local_snapshot - CFBD API export; verify source terms before redistribution.
- `cfbd` / `cfbd_manifest_20260517_031937.csv`: source_limited_local_snapshot - CFBD API export manifest; verify source terms before redistribution.
- `cfbd` / `cfbd_manifest_20260517_032307.csv`: source_limited_local_snapshot - CFBD API export manifest; verify source terms before redistribution.
- `kaggle_nfl_draft` / `nfl-draft-2026.zip`: source_limited_user_download - Kaggle page was user-reported as CC0 Public Domain; verify before redistribution.
- `kaggle_nfl_draft` / `big_board_picks.csv`: source_limited_user_download - Kaggle page was user-reported as CC0 Public Domain; verify before redistribution.
- `kaggle_nfl_draft` / `big_boards.csv`: source_limited_user_download - Kaggle page was user-reported as CC0 Public Domain; verify before redistribution.
- `kaggle_nfl_draft` / `consensus_big_board.csv`: source_limited_user_download - Kaggle page was user-reported as CC0 Public Domain; verify before redistribution.
- `kaggle_nfl_draft` / `consensus_big_board_latest_2026.csv`: source_limited_user_download - Kaggle page was user-reported as CC0 Public Domain; verify before redistribution.
- `kaggle_nfl_draft` / `draft_order.csv`: source_limited_user_download - Kaggle page was user-reported as CC0 Public Domain; verify before redistribution.
- `kaggle_nfl_draft` / `draft_results.csv`: source_limited_user_download - Kaggle page was user-reported as CC0 Public Domain; verify before redistribution.
- `kaggle_nfl_draft` / `first_round_mocks.csv`: source_limited_user_download - Kaggle page was user-reported as CC0 Public Domain; verify before redistribution.
- `kaggle_nfl_draft` / `first_round_picks.csv`: source_limited_user_download - Kaggle page was user-reported as CC0 Public Domain; verify before redistribution.
- `kaggle_nfl_draft` / `player_position_2026_mapping.csv`: source_limited_user_download - Kaggle page was user-reported as CC0 Public Domain; verify before redistribution.
- `kaggle_nfl_draft` / `players_nflverse.csv`: source_limited_user_download - Kaggle page was user-reported as CC0 Public Domain; verify before redistribution.
- `kaggle_nfl_draft` / `sample_submission.csv`: source_limited_user_download - Kaggle page was user-reported as CC0 Public Domain; verify before redistribution.
- `kaggle_nfl_draft` / `solution.csv`: source_limited_user_download - Kaggle page was user-reported as CC0 Public Domain; verify before redistribution.
- `kaggle_nfl_draft` / `team_mocks.csv`: source_limited_user_download - Kaggle page was user-reported as CC0 Public Domain; verify before redistribution.
- `kaggle_nfl_draft` / `team_picks.csv`: source_limited_user_download - Kaggle page was user-reported as CC0 Public Domain; verify before redistribution.
- `third_party_combine` / `combine_dataset_manifest.csv`: source_limited_license_unresolved - License not found in downloaded repository files; do not redistribute.
- ...and 9 more in the CSV.

## Next Step

Use this snapshot for an identity/data-health audit before any prospect feature
table or formula integration. The safe next phase is to reconcile player names
and IDs across CFBD, RotoWire, FantasyPros/ADP, Kaggle draft data, and combine
sources without scoring them.
