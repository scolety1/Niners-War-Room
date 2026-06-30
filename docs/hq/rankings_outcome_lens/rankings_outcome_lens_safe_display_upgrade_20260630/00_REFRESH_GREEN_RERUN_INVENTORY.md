# Rankings / Outcome Lens Safe Display Upgrade - Refresh-Green Rerun Inventory

## Repo State

- Lane branch: `work/lane-rankings-outcome-upgrade-20260630`
- Lane worktree: `C:\NWR\Niners-War-Room-lane-rankings-outcome-upgrade-20260630`
- Actual fetched HQ head: `c1aa6c3a76aed86b48ae377135df5151d00b0f83`
- Lane start head before fast-forward: `e598249a2a9915366fc2087991bb0519be7c8403`
- Prior safe prep work: present in current HQ after fast-forward. The page already uses the safer preset names `Dynasty Review`, `Market Context`, `Outcome Context`, `Data Review`, `Statistic Analysis`, and `Draft Rankings`.

## nflverse Refresh-Health Gate

Expected dataset-level refresh-health artifacts are present after fetching and rebasing to current HQ:

- Present: `docs/hq/data_sources/nflverse_dataset_level_refresh_health_20260630/`
- Present: `src/services/nflverse_refresh_health_service.py`
- Present: `tests/test_nflverse_refresh_health_service.py`

Decision: `GREEN_TRACKED_REFRESH_HEALTH_CONTRACT_PRESENT` for dataset-level status display.

Because the contract is dataset-level and does not provide a row-level Rankings display artifact or approved join output, the lane did not implement roster age fallback, roster status, injury report status, next game / bye context, depth chart role context, snap-share recency, draft capital display, or identity bridge health as player-table columns.

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

SAFE_NOW items retained/implemented:

- Default Dynasty Review board remains clean.
- Market context stays localized to Market Context / Data Review.
- Outcome Context remains V2-first, display-only, and position-applicable.
- A centralized-service dataset refresh status panel was added so the UI reports the GREEN tracked contract without implying unsupported player-level dataset fields.

## Still Blocked / Deferred

- nflverse roster age fallback: `NEED_DATASET_REFRESH` for an approved row-level display artifact or join gate
- nflverse roster status: `NEED_DATASET_REFRESH` for an approved row-level display artifact or join gate
- nflverse injury report status: `NEED_DATASET_REFRESH` for an approved row-level display artifact or join gate
- nflverse next game / bye context: `NEED_DATASET_REFRESH` for an approved row-level display artifact or join gate
- nflverse depth chart role context: `NEED_DATASET_REFRESH` for an approved row-level display artifact or join gate
- nflverse snap-share recency / last active season: `NEED_DATASET_REFRESH` for an approved row-level display artifact or join gate
- nflverse draft capital display: `NEED_DATASET_REFRESH` for an approved row-level display artifact or join gate
- nflverse identity bridge health: `NEED_DATASET_REFRESH` for an approved row-level display artifact or join gate
- Rookie Outcome Gate G app wiring: `NEED_MODEL_GATE`
- Injury risk / recovery projection: `BLOCKED`
- Missing data as zero: `BLOCKED`
