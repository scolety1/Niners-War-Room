# Schedule Context Join Rules

## Source Artifact

Read only:

`docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv`

App pages must not read raw `C:\NWR_SHARED_DATA` or any local schedule snapshot directly.

## Required Join

Where a lane joins schedule context to an app row, join by `nwr_player_id`.

Do not join by player name alone. Do not consume pending identity approval proposals as safe joins.

## Required Row Filters

Rows are eligible for schedule display only when all are true:

- `identity_join_status=SAFE_NOW_DISPLAY_ONLY`
- `review_required=false`
- the requested schedule field is not `Not enough information`
- `display_only=true`
- `model_use_allowed=false`
- `training_allowed=false`
- `source_truth_allowed=false`
- `rank_logic_allowed=false`
- `hidden_sort_allowed=false`
- `trade_value_allowed=false`
- `pick_value_allowed=false`

## Schema / Status Gates

The consuming lane must verify that the artifact contains:

- `nwr_player_id`
- `identity_join_status`
- `review_required`
- `next_game_context`
- `opponent_context`
- `bye_context`
- all guardrail flag columns listed above

If any required column is missing, schedule context must remain `Not enough information`.

## Team Aliases

The tracked artifact already carries the approved schedule context. Lanes should prefer the artifact values and avoid recomputing schedule joins.

If a lane must compare team labels for display consistency, use these aliases only:

- NWR `LAR` maps to nflverse schedule `LA`
- NWR `JAC` maps to nflverse schedule `JAX`

No additional alias or fuzzy team matching is approved in app pages.

## Stale / Missing Schedules

If a schedule field is missing, stale, blank, or `Not enough information`, display `Not enough information`. Do not infer opponent, bye, home/away, schedule difficulty, rest advantage, or health from missing schedule data.

## Identity-Review Rows

Rows with `NEED_IDENTITY_REVIEW`, `review_required=true`, missing `nwr_player_id`, or pending identity proposal evidence must not expose schedule detail. Display `Not enough information` or the lane's existing unavailable/missing-evidence copy.
