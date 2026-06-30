# UI Copy And Guardrails

## Existing Approved Surfaces

Existing V0 display surfaces remain the only app surfaces:

- Rankings -> Outcome Context.
- Player Compare -> Injury / Availability Context.

No new app wiring is activated by this lane.

## Required Copy

Existing V0 copy remains approved:

`Injury context is review-only. No medical recovery projection is made. Missing injury context is not clean health.`

Player Compare V0 copy remains approved:

`Review-only context. No medical projection or injury-risk score is made.`

Safe upgrade denominator copy for future activation:

`Availability denominator context is display-only/review-only. Per-game fields remain Not enough information until NFLVerse Refresh Health is green.`

Season-total caveat:

`Injury-report counts are season totals by report week, not per-game availability denominators.`

Per-game caveat:

`Per-game availability values require refreshed roster, schedule, snap, and stat coverage before display.`

## Display Rules

- Missing injury context must remain `Not enough information`.
- Missing availability context must remain `Not enough information`.
- Ambiguous identity must keep the row as `Not enough information`.
- `games_missed_while_rostered` is not a causal injury label.
- No surface may use this context for sort, rank, model input, trade value, or pick value.

## Blocked Language

Do not add:

- injury-risk score
- medical projection
- ACL or comeback projection
- recovery probability
- durability score
- clean bill / healthy by missing data wording
- source-truth promotion wording

## UI Status

The service and docs prepare the display contract. This lane does not add live
denominator values to app tables.
