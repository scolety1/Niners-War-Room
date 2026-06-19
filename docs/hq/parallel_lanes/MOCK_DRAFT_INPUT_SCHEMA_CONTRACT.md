# Mock Draft Input Schema Contract

## Purpose

This contract defines lane-local input schemas for Mock Draft readiness work.
It prepares future simulator intake without running simulations, wiring app UI,
promoting artifacts, or reading live ADP.

## Real Input Gate

The frozen rookie input path is:

`local_exports/rookie_framework/final_post_fill_runway_20260616/rookie_2026_mock_draft_input_20260616.csv`

That file is read-only, local-only, and never committed. Missing real inputs
block simulations but do not block schema scaffolding or fixture-only tests.
Veteran, pick, roster, team-needs, NWR private value, and market behavior inputs
are not yet confirmed and must remain YELLOW until supplied and reviewed.

## Schema Families

### Frozen Rookie Input

Required columns:

- `asset_id`
- `player`
- `position`
- `asset_type`
- `nwr_private_value`
- `source_status`

### Dropped / Available Veteran Pool

Required columns:

- `asset_id`
- `player`
- `position`
- `nfl_team`
- `availability_source`
- `review_status`

### Final Pick Order

Required columns:

- `overall_pick`
- `round`
- `round_pick`
- `pick_label`
- `current_owner`
- `original_owner`

### NWR / My Pick Numbers

Required columns:

- `overall_pick`
- `pick_label`
- `owner`
- `is_nwr_pick`

### Current Rosters / Keepers

Required columns:

- `team_id`
- `team_name`
- `player`
- `position`
- `keeper_status`

### Team Needs / Opponent Tendencies

Required columns:

- `team_id`
- `team_name`
- `position`
- `need_weight`
- `tendency_note`

### NWR Private Value Source

Required columns:

- `asset_id`
- `player`
- `position`
- `nwr_private_value`
- `value_source`
- `separation_note`

Blocked columns include ADP, market rank, market value, opponent timing, hidden
sort keys, outcome probabilities, probability bands, app routes, and promoted
artifact flags.

### ADP / Market Opponent Behavior Source

Required columns:

- `asset_id`
- `player`
- `position`
- `market_adp_pick`
- `market_source`
- `opponent_likelihood_signal`
- `allowed_use`
- `separation_note`

Allowed use is opponent behavior, likely availability, and pick timing only.
Market files must not contain NWR private value columns.

## Global Rules

- ADP/market fields are never NWR private value.
- Missing real inputs are YELLOW readiness gaps.
- Malformed fixture schemas are RED contract failures.
- No production rankings, sorting, probabilities, bands, app wiring, or
  promoted artifacts are allowed.
- Contract checks are read-only and do not write `data/`, `local_exports/`, or
  generated artifacts.
