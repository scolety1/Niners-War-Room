# Outcome V2 5Y Data Coverage Inventory

## Scope

This lane investigates whether Outcome V2 can extend historical factual player-season target labels far enough backward to support better five-year outcome labels. It does not touch Rankings, Outcome Lens, app pages, current-player probabilities, model inputs, or source-truth gates.

## Base

- Branch: `work/outcome-v2-5y-data-coverage-20260630`
- Base: `origin/work/hq-parallel-control`
- Actual base HEAD: `3ee9570163b3117029de1dc4a88d4494b8e15b75`

## Existing Outcome V2 Target Window

Existing generated artifacts under `C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels\`:

| Artifact | Rows | Season coverage | Notes |
| --- | ---: | --- | --- |
| `outcome_v2_season_outcome_labels.csv` | 3,578 | target seasons `2019-2024` | Review-only historical labels. |
| `outcome_v2_anchor_horizon_labels.csv` | 3,569 | anchor seasons `2018-2023` | This-year, next-year, and within-5Y horizon labels. |
| `outcome_v2_historical_label_manifest.csv` | 3 | n/a | Review-only manifest. |
| `outcome_v2_historical_label_validation_summary.csv` | 12 | n/a | Coverage/validation summary. |

Known 5Y blocker before this lane:

- Complete 5Y rows: `296`
- Right-censored or missing 5Y rows: `3,273`
- 5Y fields remained blocked for app-facing probabilities because complete windows were too sparse.

## Older Candidate Data Sources Found

### NFL Usage Target Backtest Historical Expansion

Root:

`C:\NWR_SHARED_DATA\nfl_usage_cache\target_backtest\historical_expansion\`

| Candidate file | Rows | Seasons | Key columns | First-down status | Policy status |
| --- | ---: | --- | --- | --- | --- |
| `nfl_usage_expanded_target_labels_v0.csv` | 3,578 | target seasons `2019-2024` | `target_season`, `player_id`, `player_name`, `position`, next-season labels | labels only; no first-down columns retained | Review-only target labels; not enough to extend before 2019. |
| `nfl_usage_expanded_target_backtest_joined_panel_v0.csv` | 2,848 | feature seasons `2018-2023`; target seasons `2019-2024` | `season`, `target_season`, `player_id`, usage fields | `rushing_first_downs`, `receiving_first_downs` | Review-only joined panel; supports current window only. |
| `panels/player_season_core_usage_panel.csv` | 3,701 | `2018-2023` | `season`, `player_id`, `position`, usage fields | `rushing_first_downs`, `receiving_first_downs` | Useful usage panel, but not a full pre-2018 target label source. |
| `panels/player_week_core_usage_panel.csv` | not fully loaded in this lane | `2018-2023` by path family | player-week usage | derived usage, not direct target labels | Review-only; no model/source-truth promotion. |

### Scheduled nflverse Pulls

Representative source:

`C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\20260626_073449\season_stats.csv`

| Rows | Seasons | Key columns | First-down status | Policy status |
| ---: | --- | --- | --- | --- |
| 4,017 | `2024-2025` | `player_id`, `player_display_name`, `position`, `season`, `games`, scoring/stat fields | `passing_first_downs`, `rushing_first_downs`, `receiving_first_downs` | Factual public nflverse snapshot, but not older than the existing label window. |

### nflreadpy Raw Cache Families

Existing cache roots include:

- `C:\NWR_SHARED_DATA\nfl_usage_cache\target_backtest\historical_expansion\nflreadpy_cache\`
- `C:\NWR_SHARED_DATA\nfl_usage_cache\historical_panel\nflreadpy_cache\`
- `C:\NWR_SHARED_DATA\nfl_usage_cache\nflreadpy_cache\`

Findings:

- Existing target-backtest cache includes player_stats and pbp/parquet files for `2018-2023`.
- Existing historical-panel cache includes some NGS-style `2016-2025` files, but those are not sufficient for full fantasy target labels and do not include all required scoring fields.
- Existing local cache did not already contain a full pre-2018 player-season target-label panel.

### Targeted nflreadpy Player Stats Smoke

Using the existing shared tool environment:

`C:\NWR_SHARED_DATA\tool_envs\overnight_tune_v0\Scripts\python.exe`

with explicit cache root:

`C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_source_audit\nflreadpy_cache\`

Smoked seasons:

| Season | Rows | Required scoring fields | First-down fields |
| ---: | ---: | --- | --- |
| 2012 | 1,811 | present | `passing_first_downs`, `rushing_first_downs`, `receiving_first_downs` |
| 2017 | 1,869 | present | `passing_first_downs`, `rushing_first_downs`, `receiving_first_downs` |

The smoke confirmed older `nflreadpy.load_player_stats(summary_level="reg")` can provide factual player-season data with exact first-down fields before 2018.

## Scoring Field Availability

Required fields for the narrow extension were available in targeted `player_stats`:

- Player keys: `player_id`, `player_display_name`, `position`, `season`, `recent_team`
- Availability: `games`
- Passing: `passing_yards`, `passing_tds`, `passing_interceptions`, `passing_first_downs`, `passing_2pt_conversions`
- Rushing: `rushing_yards`, `rushing_tds`, `rushing_first_downs`, `rushing_2pt_conversions`, `rushing_fumbles_lost`
- Receiving: `receiving_yards`, `receiving_tds`, `receiving_first_downs`, `receiving_2pt_conversions`, `receiving_fumbles_lost`
- Returns: `punt_return_yards`, `kickoff_return_yards`, `special_teams_tds`
- Fumbles: `sack_fumbles_lost`, `rushing_fumbles_lost`, `receiving_fumbles_lost`

## Inventory Conclusion

A full current-player display build remains out of scope. For historical 5Y label coverage only, the inventory found a safe public factual source path: targeted `nflreadpy.load_player_stats` for older seasons, cached under `C:\NWR_SHARED_DATA`, with exact first-down scoring fields available. This supports a review-only historical label extension, not app-facing probabilities.
