# Veteran Outcome V2 NFLVerse Context Audit

## Current Status

Veteran Outcome V2 already has a display-only Rankings integration through the
Outcome Lens. The current-player artifact remains display/review only and
explicitly disallows model, training, source-truth, rank, hidden-sort, trade,
and pick-value use.

NFLVerse player context now adds useful supporting caveats for safe rows, but it
does not change Outcome V2 probabilities.

## Safe Display / Review Context Now

For rows where the tracked player-context artifact has
`identity_join_status=SAFE_NOW_DISPLAY_ONLY` and `review_required=false`, these
families can support display/review context:

- roster birth-date-derived age and age source
- roster status and weekly roster status
- injury report status/date and practice status
- depth chart context
- snap recency and sample size
- last active season/week
- draft capital when present
- non-financial contract context
- identity bridge health

These fields are context, not probability inputs.

## Future Model Feature Candidates Only After Gates

Potential future feature candidates include roster/weekly roster status,
availability context, last active season, snap recency, depth chart context,
and player_stats season/weekly summaries. They require explicit future gates:

- source-policy gate for the exact feature family
- deterministic identity coverage gate
- as-of/leakage gate
- missingness policy gate
- calibration/validation gate
- explicit user approval for model/training use

Until then, `model_use_allowed=false` and `training_allowed=false`.

## Fields That Cannot Be Used Now

- `ff_rankings`: blocked.
- schedule/opponent/bye: no current/future rows in the tracked schedule audit.
- injury context as injury risk, medical risk, recovery projection, or comeback
  probability.
- depth chart as a pre-draft historical model feature without an as-of leakage
  gate.
- snap counts, production, awards, games, or career length from the future of
  an anchor date.
- market, ADP, DynastyProcess, vendor, Gmail, CFBD, or projections as Outcome
  inputs.

## Missing Data Policy

Missing NFLVerse or Outcome data remains:

`Not enough information`

It is never `0%`, false, healthy, clean, low-risk, no-role, no-usage, or a
confirmed miss.

## Injury / Availability Effect

Injury and availability fields do not change current probabilities. They are
review-only caveats. Missing injury context is not clean health.

## Depth / Snap Effect

Depth and snap fields do not change Dynasty Rank, tiers, hidden sort, model
logic, trade value, or pick value. They may explain context in Data Review or a
future review-only Outcome cleanup, but they cannot activate new probabilities.

## New Outcome Lens Columns?

This audit does not approve new probability columns. Additional display context
columns are allowed only if they are already present in a safe tracked artifact,
field-level schema status is safe, identity is safe, and the UI keeps them
display-only. Probability columns need a separate approved Outcome gate.
