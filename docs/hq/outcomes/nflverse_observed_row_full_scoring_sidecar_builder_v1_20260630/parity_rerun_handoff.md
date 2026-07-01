# Parity Rerun Handoff

## Handoff status

The compact observed-row full scoring sidecar is ready for review-only parity rerun with partial blockers.

## Artifact

`docs/hq/outcomes/nflverse_observed_row_full_scoring_sidecar_builder_v1_20260630/observed_row_full_scoring_sidecar_artifact.csv`

Rows: `90,092`

## What a parity rerun may test

- Component-level overlap against Outcome row-level labels.
- Observed nonzero component coverage.
- Composite fumble/return/special-team touchdown handling.
- Whether zero-expanded direct components are required for a future GREEN parity gate.

## What remains blocked

- Global scoring parity.
- Missing row zero-fill.
- Return-vs-special touchdown subtype parity.
- Label truth/model/training/source-truth approval.
