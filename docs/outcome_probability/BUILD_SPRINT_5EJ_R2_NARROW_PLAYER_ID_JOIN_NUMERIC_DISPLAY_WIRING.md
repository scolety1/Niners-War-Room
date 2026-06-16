# Sprint 5EJ-R2 - Narrow Player ID Join Numeric Display Wiring

## Purpose

Sprint 5EJ-R2 resumes the stopped numeric Rankings display work by exposing `player_id` as an internal-only join key and wiring display-only numeric Outcome columns from the approved Phase 11 artifact.

## Preconditions

- Sprint 5EJ-R committed GREEN as `a60571d Amend numeric display allowlist for player id join`.
- The amended allowlist explicitly permits the narrow `src/services/player_board_score_service.py` edit needed to expose `player_id`.
- Repo path and branch were verified before implementation.
- Expected dirty state before implementation was limited to `?? data/`.

## Files Changed

- `docs/outcome_probability/BUILD_SPRINT_5EJ_R2_NARROW_PLAYER_ID_JOIN_NUMERIC_DISPLAY_WIRING.md`
- `src/services/player_board_score_service.py`
- `app/pages/05_rankings.py`
- `tests/test_dynasty_rankings_page.py`

## Player ID Exposure

`src/services/player_board_score_service.py` now includes `player_id` in the dictionaries returned by `build_player_board_score_rows(...)`.

This is an internal join key only:

- It is not part of `DEFAULT_DYNASTY_COLUMNS`.
- It is not rendered as a visible Outcome column.
- The advanced raw-row expander drops `player_id` before display.
- It is not used for ranking, sorting, filtering, player-card decisions, or hidden sort keys.

## Numeric Display Wiring

`app/pages/05_rankings.py` now loads the committed approved artifact:

- `app/generated/outcome_probability/numeric_outcome_display_v1.csv`

The Rankings display joins artifact rows by `player_id` only through the Phase 11 numeric display service. No player-name, team, position, or display-label join path was introduced.

## Display Heads Wired

Only the approved numeric display heads are available in the Rankings page outcome column group:

- `qb_t12` -> `QB T12`
- `rb_t12` -> `RB T12`
- `rb_t24` -> `RB T24`
- `wr_t12` -> `WR T12`
- `wr_t24` -> `WR T24`
- `wr_t36` -> `WR T36`
- `te_t12` -> `TE T12`

Top 6 heads and all unapproved/caution/deferred heads remain absent from the UI.

## Unavailable Row Behavior

Unavailable player/head values display as the service-provided safe unavailable marker for the player's eligible position heads. Non-position heads remain blank. The wiring does not display fake `0%` values.

## Sorting And Ranking Containment

The existing ranking logic remains unchanged:

- NWR rank is still derived from `private_score` and player-name tie-breaking only.
- Numeric Outcome display values are not used for default sort, rank calculation, league-rank movement, filters, player-card behavior, or hidden sort keys.
- Outcome columns are configured as text display columns.

## Boundaries Preserved

- No model training was performed.
- No current-player inference was created.
- No new probability generation was performed.
- No new app-readable artifact was created.
- No unapproved heads were emitted or displayed.
- No promoted artifact was created.
- No rookie files were touched.
- `data/` and `local_exports/` were not staged or committed.
- No push, deploy, release, merge, or main push occurred.

## Verdict

GREEN for narrow 5EJ-R2 display wiring, pending successful checks and exact-file commit.
