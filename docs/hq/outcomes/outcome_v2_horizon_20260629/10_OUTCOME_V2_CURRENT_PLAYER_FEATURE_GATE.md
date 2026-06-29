# Outcome V2 Current Player Feature Gate - 2026-06-30

## Decision

`BLOCKED_IDENTITY_JOIN`

## Why The Gate Blocked

Historical validation passed for 22 fields, but current-player display cannot be built safely from the current app data.

Primary blocker:

- Outcome V2 historical labels use GSIS-style player IDs, for example `00-0031288`.
- The current Dynasty Rankings artifact uses internal/NWR/Sleeper-style player IDs, for example `9493`.
- No approved current-player identity bridge from the current 240-row Dynasty Rankings artifact to the Outcome V2 GSIS label universe was found in this lane.

Secondary blocker:

- The current Dynasty Rankings artifact is marked `2026-pre-draft`.
- The factual Outcome V2 feature/label panel currently covers historical feature seasons through 2024.
- A current 2026 display artifact would need a clearly approved as-of feature snapshot and temporal definition before producing probabilities.

## Current Dynasty Rankings Source Observed

The app loads the approved local dynasty rankings artifact from the clean control repo:

`C:\NWR\Niners-War-Room\local_exports\model_v4\current_value\latest\full_player_board_value_review_rows.csv`

Observed:

- 240 rows
- source hash matches the existing expected hash in `draft_day_app_v1_service.py`
- includes `player_id`, `canonical_player_key`, `player_name`, `position`, `age`, `nfl_team`, `nwr_rank`, and existing Outcome V1 display fields
- does not expose an approved GSIS join key for Outcome V2 in the app-safe tracked artifact

Because this path is `local_exports`, it is not copied or committed by this lane.

## Current Feature Coverage Result

No current-player Outcome V2 display artifact was built.

Decision status:

`BLOCKED_IDENTITY_JOIN`

Related possible statuses:

- `BLOCKED_CURRENT_FEATURE_COVERAGE`
- `BLOCKED_SOURCE_POLICY`

## What Would Be Required Next

Before building `outcome_v2_current_player_display.csv`, a future lane must provide:

1. Approved compact identity bridge from current Dynasty Rankings players to GSIS/NFL player IDs.
2. Current as-of factual feature snapshot aligned with the app season context.
3. Explicit temporal definition of `This Year` and `Next Year` for the current app.
4. Missing-feature behavior that emits `Not enough information`.
5. Confirmation that DynastyProcess, ADP, market values, Dynasty Rank, NWR Dynasty Score, CFBD, and blocked NFL usage fields are not used as inputs.

## Safe Current Behavior

Outcome V2 remains historical validation only.

Rankings Outcome Lens must not display Outcome V2 probabilities yet.

Existing Outcome V1 display fields remain unchanged.
