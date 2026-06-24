# League History Evidence Method

## Evidence Standard

League-history evidence is separated into hard inputs, review-only metadata, and sensitivity-only reconstruction.

## Hard Inputs

Hard inputs are direct actual sources such as:

- final draft logs,
- Sleeper accepted trade exports,
- commissioner-confirmed owner/team mapping,
- final roster/drop/cut records.

Only hard inputs can become actual event rows.

## Review-Only Inputs

Review-only inputs include:

- Gmail metadata,
- email subject/date pointers,
- attachment pointers,
- free-agent snapshots,
- unprotected or roster declaration hints.

Review-only inputs do not prove actual draft/trade/drop events without hard confirmation.

## Sensitivity-Only Inputs

Proxy, inferred, or ambiguous rows remain sensitivity-only. They may guide audit questions, but they are not training truth.

## Brian Thomas Jr. Cleanup Rule

The phrase about dropping Brian Thomas Jr. from a top 5 is ambiguous. It does not prove:

- actual roster drop,
- unprotected status,
- free-agent availability,
- draft/acquisition,
- final cut.

Therefore the row is classified as `UNKNOWN / LOW` with:

- `model_use_allowed=no`
- `training_allowed=no`
- `sensitivity_only=yes`

## Non-Equivalence Rules

- Free-agent snapshot does not equal drop proof.
- Unprotected does not equal dropped.
- Gmail metadata does not equal confirmed trade/draft event.
- Missing draft/trade exports must not be backfilled with invented rows.
