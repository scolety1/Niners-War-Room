# Historical NFL Usage Panel V0 Plan

## Purpose

Build a review-only historical NFL usage panel to evaluate the coverage blocker from the NFL Usage Promotion Gate V0: `BACKTEST_BLOCKED_INSUFFICIENT_COVERAGE`.

## Source Families

Primary source families are `player_stats`, `snap_counts`, `pbp`, `nextgen_stats`, `participation`, `ftn_charting`, `pfr_advstats`, `rosters`, `players`, and `ff_playerids`.

## Seasons Attempted By Source Family

Core player-week panels attempt `2022, 2023, 2024` for player stats, snap counts, and play-by-play. Participation is attempted for 2023-2024 because public participation coverage starts later in this project contract. Identity sources without seasons are loaded as all-ID tables.

## Raw-Cache Policy

Raw/download cache material must stay under `C:\NWR_SHARED_DATA\nfl_usage_cache\historical_panel` or its `nflreadpy_cache` child. Raw payloads are not committed.

## Normalized-Output Policy

Normalized player-week/player-season panels are written only to ignored shared cache under `C:\NWR_SHARED_DATA\nfl_usage_cache\historical_panel\panels`. Git receives only manifests, coverage summaries, schema fingerprints, validation reports, quarantine reports, and readiness docs.

## Feature Grain

- `player_week`
- `player_season`
- `player_season_rolling`

## Field Coverage Requirements

Fields need multi-season availability, stable player identity, position coverage across QB/RB/WR/TE where relevant, low missingness, and explicit caveats before future backtesting.

## Join Keys

Preferred join key is `player_id`/GSIS for player_stats and PBP. Snap counts use PFR/player-name context and are joined by normalized player name, position, team, season, and week, with caveats.

## Player ID Policy

Do not fabricate IDs. Player-week panels preserve source IDs and mark identity caveats. Rows without stable player IDs may be display coverage context but are weaker for target joins.

## Missing-Data Policy

Missing means unknown or not covered, not zero value. Derived zeroes are used only where a source row exists and an event count is absent after a left join.

## No-CFBD Boundary

CFBD, college, and rookie/prospect evidence are out of scope.

## No-Model / No-App Boundary

Every artifact keeps `model_input_allowed=no` and `app_wiring_allowed=no`. No decision page consumes usage fields.

## Stop Conditions

Fail closed if source pulls are too large/slow, schemas drift, player IDs are insufficient for target joins, raw data would be tracked, or model/app/rank/source-truth files would change.

## Validation Checklist

- Source smoke summary.
- Schema fingerprints.
- Field coverage matrix.
- Panel manifests.
- Backtest readiness matrix.
- Validation and quarantine reports.
- CSV load validation.
- No raw/shared/local/runtime files tracked.
- No CFBD changes.
- Frozen board and pinned hash unchanged.
