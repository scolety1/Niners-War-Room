# UI Copy And Guardrails

## Existing Approved Surfaces

Existing display surfaces remain:

- Rankings -> Outcome Context / Data Review visibility.
- Player Compare -> Injury / Availability Context.

The denominator follow-up uses the existing Player Compare NFLVerse
Availability Context table. No ranking, recommendation, or draft-decision
surface is added.

## Required Copy

Existing V0 copy remains approved:

`Injury context is review-only. No medical recovery projection is made. Missing injury context is not clean health.`

Player Compare copy remains approved:

`Review-only context. No medical projection or injury-risk score is made.`

Denominator context:

`Availability denominator context is display-only/review-only. Missing or gated denominator values remain Not enough information.`

Season-total caveat:

`Injury-report counts are season totals by report week, not per-game availability denominators.`

Per-game caveat:

`Per-game denominator values display only from approved tracked denominator rows. Do not infer unavailable games from report counts.`

## Display Rules

- Missing injury context must remain `Not enough information`.
- Missing availability context must remain `Not enough information`.
- Ambiguous identity must keep detailed rows as `Not enough information`.
- Identity-review rows expose no denominator detail.
- `games_missed_while_rostered` remains `Not enough information`.
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

Player Compare renders safe denominator fields in the existing NFLVerse
Availability Context table. Missing and gated values remain
`Not enough information`.
