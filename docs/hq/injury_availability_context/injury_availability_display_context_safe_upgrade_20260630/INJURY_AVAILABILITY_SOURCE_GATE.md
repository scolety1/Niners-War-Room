# Injury Availability Source Gate

## Approved Sources In Use

Existing injury-report source:

`nflreadpy.load_injuries`

Approved use:

- Factual injury report context.
- Distinct report-week counts.
- Distinct out/doubtful report-week counts.
- Review-only display caveats.

Tracked NFLVerse artifacts:

- `docs/hq/data_sources/nflverse_player_context_display_20260630/`
- `docs/hq/data_sources/nflverse_availability_denominator_display_v1_20260630/`

Approved use:

- Direct display for safe identity rows.
- Direct denominator display for rows with `denominator_status=SAFE_NOW_DISPLAY_ONLY`.
- Missing and gated values as `Not enough information`.

## Still Gated Sources Or Uses

- Raw `C:\NWR_SHARED_DATA` reads from app pages.
- Identity-review rows as approved joins.
- Identity recommendations as approved joins.
- `games_missed_while_rostered`.
- Schedule next-game, opponent, bye, health, or availability inference.
- Any model, rank, source-truth, trade-value, pick-value, recommendation, or hidden-sort use.

## Source Rules

Allowed:

- Public NFLVerse factual injury/status data through approved source gates.
- Factual roster, schedule, snap, and stat context through tracked artifacts only.
- Display-only/review-only labels and caveats.

Blocked:

- Injury-risk score.
- Medical projection.
- ACL/comeback projection.
- Durability score.
- Scraped, vendor, Gmail, or rumor sources.
- Missing-data-as-healthy logic.
- Model, rank, source-truth, trade-value, or pick-value promotion.

## Missing Data Rule

Missing injury or availability context must stay `Not enough information`.

It must not be interpreted as a positive availability status.

## Per-Game Caveat

Existing injury-report counts are season totals by report week. They are not
per-game availability denominators.

Per-game denominator values display only from the tracked denominator artifact
after identity and denominator gates pass. They do not infer missed games,
injury status, health status, recovery, role, or recommendations.
