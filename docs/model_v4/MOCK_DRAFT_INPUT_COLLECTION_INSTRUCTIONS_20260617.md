# Mock Draft Input Collection Instructions - 2026-06-17

## Purpose
Use these templates to collect the remaining local review inputs needed before Mock Draft HQ can run a full post-drop-day simulation. These templates are tracked examples only; filled inputs should later be copied into ignored `local_exports/mock_draft/review_inputs/...` folders after Tim provides them.

## Template Files
- `docs/model_v4/mock_draft_input_templates_20260617/post_drop_rosters_template.csv` - required.
- `docs/model_v4/mock_draft_input_templates_20260617/post_drop_draft_order_template.csv` - required.
- `docs/model_v4/mock_draft_input_templates_20260617/team_managers_template.csv` - required.
- `docs/model_v4/mock_draft_input_templates_20260617/dropped_veterans_template.csv` - required if Tim supplies a new/updated drop list.
- `docs/model_v4/mock_draft_input_templates_20260617/behavior_only_adp_market_template.csv` - optional, behavior-only.
- `docs/model_v4/mock_draft_input_templates_20260617/nwr_veteran_value_guidance_template.csv` - optional, only for approved NWR veteran/free-agent guidance.

## What Tim Should Fill In

### Post-Drop Rosters
Fill one row per rostered player after drops.

Required columns:
- `team_name`
- `manager`
- `roster_slot`
- `player_name`
- `position`
- `nfl_team`
- `input_status`

Optional columns:
- `overall_rank`
- `source_file`
- `source_timestamp`

Accepted later destination:
- `local_exports/mock_draft/review_inputs/post_drop_rosters_20260617/post_drop_roster_rows.csv`

### Post-Drop Draft Order
Fill one row per draft pick that should be simulated.

Required columns:
- `season`
- `overall_pick`
- `round`
- `round_pick`
- `pick_label`
- `current_owner`
- `original_owner`
- `manager`
- `is_niners_pick`
- `source_status`

Accepted later destination:
- `local_exports/mock_draft/review_inputs/post_drop_draft_order_20260617/post_drop_draft_order_rows.csv`

### Team Managers
Fill one row per team. This should cover all 10 teams.

Required columns:
- `team_name`
- `manager`
- `team_key`

Optional columns:
- `team_aliases`
- `source_status`

Accepted later destination:
- `local_exports/mock_draft/review_inputs/team_managers_20260617/team_manager_rows.csv`

### Dropped Veterans
Use this only if Tim provides an updated drop list. Keep duplicate declarations as separate rows until manually resolved.

Required columns:
- `player`
- `position`
- `source_label`
- `review_flags`

Optional columns:
- `nfl_team`
- `previous_team`
- `previous_manager`
- `drop_sequence`
- `input_status`

Accepted later destination:
- `local_exports/mock_draft/review_inputs/dropped_veterans_20260617/dropped_veteran_rows.csv`

### Behavior-Only ADP/Market Timing
This file is optional. Use it only to model opponent behavior, likely pick timing, availability pressure, and expected draft-room cost.

Required columns:
- `asset_id`
- `player`
- `position`
- `source_name`
- `source_type`
- `source_timestamp`
- `market_adp`
- `sample_size`
- `identity_match_method`
- `review_flags`

Optional timing columns:
- `overall_adp`
- `expected_pick`

Accepted later destination:
- `local_exports/mock_draft/review_inputs/market_timing_20260617/market_timing_behavior_only_rows.csv`

Blocked from this file:
- `stats_model_value`
- `model_value`
- `draft_value`
- `nwr_draft_value`
- `nwr_dynasty_score`
- `nwr_quality_score`
- `quality_score`
- `war_score`
- `hidden_sort_key`
- `outcome_probability`
- `outcome_band`
- app or production wiring fields

### NWR Veteran/Free-Agent Value Guidance
This file is optional. Use it only if Tim has an approved NWR source for veteran/free-agent guidance. Do not infer this from ADP/market.

Required columns:
- `asset_id`
- `player`
- `position`
- `source_label`
- `nwr_value_status`
- `nwr_guidance_label`
- `nwr_warning`
- `draft_action`
- `source_status`

Optional column:
- `approved_numeric_nwr_value`

Accepted later destination:
- `local_exports/mock_draft/review_inputs/nwr_veteran_guidance_20260617/nwr_veteran_guidance_rows.csv`

## What Can Be Left Blank
- Optional fields can be blank.
- Unknown `overall_rank`, `source_file`, `source_timestamp`, aliases, notes, and optional numeric NWR guidance can be blank.
- Required identity fields should not be blank. Missing required identity fields become review-required.

## Separation Rules
- ADP/market is behavior-only. It can influence opponent timing, likely availability, and expected draft-room cost.
- ADP/market must never become NWR value or rookie guidance.
- NWR value/guidance is Tim-facing evaluation, fit, warnings, and draft action.
- Rookie board order remains frozen and manual-use only.
- No numeric NWR score may be invented from ADP, market rank, snapshot rank, rookie rank, or draft order.

## Gates Before Full Simulation
Full simulation stays blocked until:
- all 10 post-drop teams/managers are present,
- the post-drop draft order/pick ownership is confirmed,
- schema validation passes for required files,
- duplicate/manual-review items are preserved,
- contamination checks show ADP/market remains behavior-only,
- `local_exports/` inputs are present locally but not committed.

Optional gates:
- Real ADP/market timing is needed only for calibrated opponent market behavior.
- Approved NWR veteran/free-agent guidance is needed only for value-aware veteran comparisons.

## Codex Handling Rules For Filled Inputs
- Place filled inputs only under the accepted `local_exports/mock_draft/review_inputs/...` paths.
- Do not commit filled local input files unless Tim explicitly approves.
- Run the schema validator and inventory runner after inputs are placed.
- Do not run full simulation until all required gates are GREEN.
