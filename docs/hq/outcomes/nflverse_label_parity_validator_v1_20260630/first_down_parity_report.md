# First-Down Parity Report

Verdict: `FIRST_DOWN_SIDECAR_PRESENT_LABEL_SCORING_NOT_RECOMPUTED`

## Sidecar First-Down Evidence

The sidecar contains only first-down sidecar candidates:

- `passing_first_downs`: `1,580`
- `receiving_first_downs`: `7,350`
- `rushing_first_downs`: `4,698`

No quarantined fields are used.

## What Can Be Validated Now

- The sidecar carries explicit nonzero first-down stat rows.
- Absence from the sidecar is not zero production.
- The sidecar rows are review-only substrate.
- The sidecar does not use fantasy points or EPA fields.

## What Cannot Be Validated Yet

Scoring parity against existing labels cannot be recomputed because the tracked labels are not row-level comparable. The current Outcome V2 label evidence gives field-level validation decisions, not player-season scoring rows.

## Required Future Work

Future first-down parity validation needs:

- row-level Outcome label facts;
- scoring mode per label row;
- first-down inclusion status per label row;
- player-season identity bridge;
- censoring status;
- mismatch taxonomy.

This packet does not change Outcome V2 scoring, labels, or probabilities.
