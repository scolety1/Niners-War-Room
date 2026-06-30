# Rankings / Outcome Lens Safe Display Upgrade - Refresh-Green Rerun Inventory

## Repo State

- Lane branch: `work/lane-rankings-outcome-upgrade-20260630`
- Lane worktree: `C:\NWR\Niners-War-Room-lane-rankings-outcome-upgrade-20260630`
- Actual fetched HQ head: `3be529f37fe931adc95883a2698d72409c0c8a2d`
- Lane start head before fast-forward: `e598249a2a9915366fc2087991bb0519be7c8403`
- Prior safe prep work: present in current HQ after fast-forward. The page already uses the safer preset names `Dynasty Review`, `Market Context`, `Outcome Context`, `Data Review`, `Statistic Analysis`, and `Draft Rankings`.

## nflverse Refresh-Health Gate

Expected dataset-level refresh-health artifacts are present after fetching and rebasing to current HQ:

- Present: `docs/hq/data_sources/nflverse_dataset_level_refresh_health_20260630/`
- Present: `src/services/nflverse_refresh_health_service.py`
- Present: `tests/test_nflverse_refresh_health_service.py`

Decision: `GREEN_TRACKED_REFRESH_HEALTH_CONTRACT_PRESENT` for dataset-level status display.

The NFLVerse player context display artifact is also present:

- Present: `docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv`
- Present: `docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_schema_manifest.csv`
- Present: `src/services/nflverse_player_context_display_service.py`

Artifact rows: `294`.

- SAFE_NOW display rows: `240`
- NEED_IDENTITY_REVIEW rows: `54`
- review-required rows: `54`

## Dataset Rows Available

Dataset-level rows available in the fetched repo artifacts: `25`.

Blocked dataset status carried forward by policy: `ff_rankings` remains `BLOCKED` / `blocked_policy` and must not become rank/model/source-truth logic.

SAFE refresh datasets available for status display include:

- `player_stats_weekly`
- `schedules`
- `players`
- `rosters`
- `weekly_rosters`
- `ff_playerids`
- `depth_charts`
- `injuries`
- `snap_counts`
- `trades`
- `teams`

Full safe refresh datasets available for status display include all SAFE datasets plus full-refresh datasets such as `player_stats_seasonal`, `play_by_play`, `team_stats`, `participation`, `draft_picks`, and other review/display rows in the registry.

## Outcome V2 Status

Outcome V2 is already available in the Rankings Outcome Context path as display-only/review-only context from the approved current-player display artifact. Missing values remain `Not enough information`.

Blocked Outcome V2 fields remain blocked:

- `RB_T6_WITHIN_5Y`
- `RB_T12_WITHIN_5Y`

## Rookie Gate F/G Status

Rookie Gate G remains blocked unless a separate explicit GREEN Gate G approval artifact exists. Current repo docs continue to say Gate G should not run yet / remains closed.

## Movement From Waiting To Implementable

Dataset-level nflverse status moved from waiting to implementable:

- refresh-health contract visibility: `SAFE_NOW`
- safe refresh dataset list: `SAFE_NOW`
- full safe refresh dataset list: `SAFE_NOW`
- `ff_rankings` blocked status: `SAFE_NOW`
- source-policy display warnings: `SAFE_NOW`

Player-level NFLVerse context moved from waiting to implementable where the tracked artifact and schema both say `SAFE_NOW_DISPLAY_ONLY`:

- roster birth-date age fallback and age source
- roster status
- weekly roster status
- injury report status/date and practice status
- depth chart context
- snap recency and sample size
- last active season/week
- draft capital
- non-financial contract context
- identity bridge health/status

SAFE_NOW items retained/implemented:

- Default Dynasty Review board remains clean.
- Market context stays localized to Market Context / Data Review.
- Outcome Context remains V2-first, display-only, and position-applicable.
- A centralized-service dataset refresh status panel reports the GREEN tracked contract.
- Data Review exposes NFLVerse player context only for `identity_join_status=SAFE_NOW_DISPLAY_ONLY` and `review_required=false`.
- Clean Board, Market Context, Outcome Context, and Draft Rankings do not show dense NFLVerse context by default.

## Still Blocked / Deferred

- NFLVerse rows with `NEED_IDENTITY_REVIEW`: deferred from player context display except review status.
- NFLVerse next game / opponent / bye context: deferred because the artifact contains `0` safe non-`Not enough information` rows.
- Rookie Outcome Gate G app wiring: `NEED_MODEL_GATE`
- Injury risk / recovery projection: `BLOCKED`
- Missing data as zero: `BLOCKED`
