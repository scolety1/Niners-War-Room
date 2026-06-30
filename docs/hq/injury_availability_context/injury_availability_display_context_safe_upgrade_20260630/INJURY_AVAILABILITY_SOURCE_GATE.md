# Injury Availability Source Gate

## Approved Source Already In Use

`nflreadpy.load_injuries`

Approved use:

- Factual injury report context.
- Distinct report-week counts.
- Distinct out/doubtful report-week counts.
- Review-only display caveats.

Current source-gate doc:

`docs/hq/outcomes/injury_context_20260630/INJURY_CONTEXT_SOURCE_GATE.md`

Current app-display doc:

`docs/hq/outcomes/injury_context_20260630/INJURY_CONTEXT_APP_DISPLAY_V0.md`

## Waiting Sources

The following sources are not activated for availability denominator computation in
this lane:

- `weekly_rosters`
- `rosters`
- `schedules`
- `snap_counts`
- `player_stats`
- refresh metadata for dynamic season anchors

Reason:

The current completion gate lists `nflverse pull/status` as `YELLOW`, so these
implementation items remain `WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN`.

## Source Rules

Allowed:

- Public NFLVerse factual injury/status data through approved source gates.
- Factual roster, schedule, snap, and stat context only after refresh health is green.
- Display-only/review-only labels and caveats.

Blocked:

- Injury-risk score.
- Medical projection.
- ACL/comeback projection.
- Scraped, vendor, Gmail, or rumor sources.
- Missing-data-as-healthy logic.
- Model, rank, source-truth, trade-value, or pick-value promotion.

## Missing Data Rule

Missing injury or availability context must stay `Not enough information`.

It must not be interpreted as a positive availability status.

## Per-Game Caveat

Existing injury-report counts are season totals by report week. They are not
per-game availability denominators.

Per-game fields require refreshed roster, schedule, snap, and stat coverage before
values can be populated.
