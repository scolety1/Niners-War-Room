# Local Data Recovery Import: Combined 2026-06-12

## Verdict

`IMPORT_COMPLETE_LOCAL_DATA_ONLY`

The combined recovery import copied useful local data from both recovery zips
into the repo without changing tracked source code, app logic, rankings logic,
model logic, app wiring, or promoted artifacts.

Canonical completed NFL 2025 `player_stats` / factual scoring data was not
found. The recovered canonical NFL `player_stats.csv` files contain weekly rows
through 2024 only.

## Inputs

| Item | Path |
| --- | --- |
| Main recovery zip | `C:\Users\smcol\Downloads\nwr_local_data_recovery_pack_20260612.zip` |
| Extra desktop zip | `C:\Users\smcol\Downloads\nwr_final_desktop_extra_files_20260612.zip` |
| Actual staging path used | `C:\nwr_stage_20260612` |
| Main staged folder | `C:\nwr_stage_20260612\main` |
| Extra staged folder | `C:\nwr_stage_20260612\extra` |

The initial PowerShell `Expand-Archive` attempt was abandoned after extraction
errors. The successful staging path was created with Python zip extraction at
`C:\nwr_stage_20260612`.

## Import Policy

- Existing destination files were preserved when contents differed.
- Tracked source code, app files, tests, and config files were not overwritten.
- Existing tracked `sample_data` files were preserved.
- `.git`, `.venv`, caches, and generated Python cache folders were not copied.
- Zip manifest, README, and sweep files were preserved under
  `local_exports/recovery_manifests/20260612/`.

## Folders Copied

| Source zip | Destination group | Copied | Existing identical | Existing different preserved |
| --- | --- | ---: | ---: | ---: |
| Main recovery | `local_exports/outcome_probability` | 360 | 0 | 0 |
| Main recovery | `local_exports/truth_set_lab` | 274 | 0 | 0 |
| Main recovery | `local_exports/model_v4` | 373 | 0 | 4 |
| Main recovery | `sample_data` | 0 | 1 | 27 |
| Main recovery | `local_exports/recovery_manifests` | 1 | 0 | 0 |
| Extra desktop | `local_exports/data_packs` | 22 | 0 | 0 |
| Extra desktop | `local_exports/merged` | 5 | 0 | 0 |
| Extra desktop | `local_exports/model_v4` | 26 | 0 | 0 |
| Extra desktop | `local_exports/nflverse` | 35 | 0 | 0 |
| Extra desktop | `local_exports/sleeper` | 6 | 0 | 0 |
| Extra desktop | `data/college_football_data` | 28 | 0 | 0 |
| Extra desktop | `local_exports/recovery_manifests` | 2 | 0 | 0 |

Detailed copy log:

`local_exports/outcome_probability/sprint_5as_feature_coverage_recovery_rerun_combined/combined_recovery_copy_log_20260612.csv`

## Preserved Existing Differences

The copy process preserved existing destination versions for:

- 4 files under `local_exports/model_v4/draft_prep/latest/`.
- 27 tracked files under `sample_data/`.

No tracked source, app, service, test, or config file was overwritten by the
recovery import.

## Key Files Now Present

| File or folder | Status | Notes |
| --- | --- | --- |
| `local_exports/truth_set_lab/v3/downloads/player_stats.csv` | Present | NFL weekly player stats, seasons 1999-2024. |
| `local_exports/nflverse/preview/sprint2_phase7_public_20260514/downloads/player_stats.csv` | Present | Same NFL weekly player stats coverage, seasons 1999-2024. |
| `local_exports/outcome_probability/sprint_5n_broader_historical_rebuild/` | Present | Restored broader historical feature/label exports. |
| `local_exports/outcome_probability/sprint_5x_2020_2022_historical_rebuild/` | Present | Restored 2020-2022 historical feature/label exports. |
| `local_exports/outcome_probability/sprint_5z_expanded_internal_validation_package/` | Present | Restored expanded internal validation package exports. |
| `local_exports/data_packs/lve_sleeper_20260505_pdf_ranks_draft_pool_20260508_213233/` | Present | Current 2026 roster, available veteran, and rookie draftable pool. |
| `local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv` | Present | 240 current board rows, app/value context only. |
| `local_exports/nflverse/preview/sprint2_phase7_public_20260514/downloads/depth_charts_2025.csv` | Present | 2025 support context, not scoring replacement. |
| `local_exports/nflverse/preview/sprint2_phase7_public_20260514/downloads/injuries_2025.csv` | Present | 2025 support context, not scoring replacement. |
| `local_exports/nflverse/preview/sprint2_phase7_public_20260514/downloads/snap_counts_2025.csv` | Present | 2025 support context, not scoring replacement. |
| `data/college_football_data/raw/csv/player_stats_season_2025_regular_passing.csv` | Present | Rookie-path candidate source only after schema audit. |
| `data/college_football_data/raw/csv/player_stats_season_2025_regular_rushing.csv` | Present | Rookie-path candidate source only after schema audit. |
| `data/college_football_data/raw/csv/player_stats_season_2025_regular_receiving.csv` | Present | Rookie-path candidate source only after schema audit. |
| `local_exports/model_v4/raw_user_exports/rotowire_manual/2025/` | Present | Quarantined support files only after field-level legality review. |

## Key Files Still Missing

| Missing item | Impact |
| --- | --- |
| Canonical completed NFL `player_stats_2025.csv` | Blocks legal 2026 veteran prior-season feature generation. |
| 2025 rows in canonical NFL `player_stats.csv` | Recovered `player_stats.csv` max season is 2024. |
| Legal 2026 veteran feature snapshot export using completed 2025 facts | Current 2026 veteran probability features remain unavailable. |
| Audited rookie threshold feature schema/head | Rookie rows remain separate-head/design-only. |
| Player-level threshold probabilities | Monotonicity, calibration, and release gates remain not evaluable. |

## Canonical 2025 NFL Factual Data

`canonical_2025_nfl_player_stats_exists = no`

Recovered NFL `player_stats.csv` profiles:

| Path | Rows | Min season | Max season | Weekly rows | 2025 rows |
| --- | ---: | ---: | ---: | --- | --- |
| `local_exports/truth_set_lab/v3/downloads/player_stats.csv` | 134,470 | 1999 | 2024 | yes | no |
| `local_exports/nflverse/preview/sprint2_phase7_public_20260514/downloads/player_stats.csv` | 134,470 | 1999 | 2024 | yes | no |

The 2025 support files restored from nflverse, CFBD, and RotoWire cannot be used
as a fake or substitute canonical 2025 NFL offensive scoring source.

## Tracked Files Modified By Import

None.

The import created or restored local data under `local_exports/` and
`data/college_football_data/`, and this report was created under
`docs/outcome_probability/` for HQ review.

## Confirmed Non-Actions

- No app probabilities were created.
- No fake probabilities were created.
- No calibrated probabilities were created.
- No app-readable probability tables were created.
- No app wiring was changed.
- No rankings or sorting were changed.
- No decision automation was created.
- No model artifacts were promoted.
- No push or deploy occurred.
