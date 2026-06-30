# NFLVerse Outcome Context Inventory

## Current Master

- Branch inspected: `work/hq-parallel-control`
- HEAD inspected: `2070a2f4ffa6b6ae83bd6ca1529880f67dd6cab0`

## Tracked NFLVerse Artifacts Present

- `docs/hq/data_sources/nflverse_dataset_level_refresh_health_20260630/`
- `docs/hq/data_sources/nflverse_player_context_display_20260630/`
- `docs/hq/data_sources/nflverse_player_context_identity_review_20260630/`
- `docs/hq/data_sources/nflverse_player_context_schedule_audit_20260630/`
- `src/services/nflverse_refresh_health_service.py`
- `src/services/nflverse_player_context_display_service.py`

No raw `C:\NWR_SHARED_DATA` files were read or committed by this audit.

## Dataset Refresh-Health Status

The dataset-level refresh-health implementation report verdict is GREEN for
Refresh/Data Health. It split nflverse from one coarse row into a parent runner
plus `25` canonical dataset rows and added explicit false flags for model,
training, and rank logic use.

Service inventory:

- registry rows: `25`
- safe refresh dataset ids:
  `player_stats_weekly`, `schedules`, `players`, `rosters`,
  `weekly_rosters`, `ff_playerids`, `depth_charts`, `injuries`,
  `snap_counts`, `trades`, `teams`
- full safe refresh dataset ids:
  `player_stats_weekly`, `player_stats_seasonal`, `play_by_play`,
  `team_stats`, `schedules`, `players`, `rosters`, `weekly_rosters`,
  `ff_playerids`, `depth_charts`, `injuries`, `snap_counts`,
  `participation`, `ftn_charting`, `pfr_advstats`, `nextgen_stats`,
  `draft_picks`, `combine`, `contracts`, `trades`, `teams`, `officials`,
  `espn_qbr`, `ff_opportunity`
- blocked dataset id: `ff_rankings`

All dataset rows remain refresh/data-health or review/display status only.
They do not approve model, training, source-truth, rank, hidden-sort, trade, or
pick-value use.

## Player Context Artifact

Tracked artifact:

`docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv`

Tracked schema manifest:

`docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_schema_manifest.csv`

Counts:

- artifact rows: `294`
- safe display rows: `240`
- identity review rows: `54`

Safe row field coverage:

| Field family | Safe non-NEI rows |
| --- | ---: |
| roster birth-date derived age | 240 |
| roster status | 240 |
| weekly roster status | 240 |
| injury report status | 76 |
| practice status | 220 |
| depth chart role | 240 |
| snap recency | 223 |
| last active season | 240 |
| draft capital | 75 |
| non-financial contract context | 240 |
| next game context | 0 |
| opponent context | 0 |
| bye context | 0 |

Schema policy:

- fields are `SAFE_NOW_DISPLAY_ONLY`
- `display_only=true`
- `model_use_allowed=false`
- `training_allowed=false`
- `source_truth_allowed=false`
- `rank_logic_allowed=false`
- `hidden_sort_allowed=false`
- `trade_value_allowed=false`
- `pick_value_allowed=false`

## Identity Review

Identity review packet:

`docs/hq/data_sources/nflverse_player_context_identity_review_20260630/nflverse_player_context_identity_review_summary.md`

Summary:

- rows reviewed: `54`
- safe resolution proposals: `43`
- rows safely resolved/applied to artifact: `0`
- needs human review: `4`
- keep `NEED_IDENTITY_REVIEW`: `7`

Proposals are not applied. They require Data Hygiene/HQ acceptance before the
primary display artifact can be rebuilt.

## Schedule / Opponent / Bye Blocker

Schedule audit:

`docs/hq/data_sources/nflverse_player_context_schedule_audit_20260630/nflverse_schedule_context_build_report.md`

Summary:

- as-of date: `2026-06-30`
- teams audited: `34`
- teams with schedule rows: `32`
- teams with current/future game rows: `0`

Root cause: approved schedule data is present for 2024-2025 only. With the
2026-06-30 as-of date, there are no current/future games, so next
game/opponent/bye context must remain `Not enough information`.

## `ff_rankings`

`ff_rankings` remains `BLOCKED_VENDOR_OR_PRIVATE`. It is not available for
Outcome, Rookie Outcome, Rankings, model input, rank logic, hidden sort, trade
value, pick value, or source truth.

## Datasets Available As Review/Display Context

Available as review/display context when the artifact/schema gates and identity
gates are safe:

- players / rosters / weekly rosters
- injuries / practice status
- depth charts
- snap counts
- player stats weekly/seasonal
- draft picks
- combine
- contracts, non-financial context only
- ff_playerids for identity plumbing only

Not available for current display from the artifact:

- schedule/opponent/bye context

Blocked:

- `ff_rankings`
