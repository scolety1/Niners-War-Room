# Outcome V2 Historical Gate Status - 2026-06-30

## Status

`YELLOW_PARTIAL_REVIEW_ONLY_APPROVAL`

The Outcome V2 2000-2024 exact-scoring historical validation/calibration gate
is persisted as documentation/status evidence only.

This status means historical review-only label fields may be used for audit,
comparison, and downstream review packets where explicitly allowed. It does not
activate current-player probabilities.

No current-player activation occurred.

## Persisted Evidence

Gate evidence is stored under:

`docs/hq/outcomes/outcome_v2_2000_validation_calibration_20260630/`

Included artifacts:

- `00_EXECUTIVE_VERDICT.md`
- `01_INPUT_COVERAGE_AND_SOURCE_POLICY.md`
- `02_2000_2024_VALIDATION_RESULTS.md`
- `03_2012_2024_VS_2000_2024_COMPARISON.md`
- `04_FIELD_LEVEL_DECISION_TABLE.csv`
- `05_BLOCKED_FIELDS_AND_REASONS.md`
- `06_GUARDRAIL_PROOF.md`

## Field Decisions

Final field-level count:

- `APPROVE_REVIEW_ONLY`: 35
- `KEEP_BLOCKED_WEAK_CALIBRATION`: 1

Required explicit decisions:

- `RB_T12_WITHIN_5Y`: `APPROVE_REVIEW_ONLY`
- `RB_T6_WITHIN_5Y`: `KEEP_BLOCKED_WEAK_CALIBRATION`

Blocked fields must remain blocked. Missing/censored data must remain
`Not enough information`.

## Non-Activation Boundaries

This gate does not approve:

- current-player probability activation
- Rankings integration
- Outcome Lens activation
- model input promotion
- source-truth promotion
- hidden sort keys
- Dynasty Rank changes
- final board rank changes
- tier changes
- protected artifact updates
- latest_candidate/latest_approved promotion

Identity bridge and current-player feature/as-of gates are still required
before any current-player use can be considered.

## Source And Data Boundary

The validated labels came from public factual nflreadpy/nflverse player stats
using exact first-down scoring:

- `passing_first_downs`
- `rushing_first_downs`
- `receiving_first_downs`

No first-down approximation was used. No raw/cache/shared/local/secret files
are persisted in this repo evidence lane.

## HEAD / Base Note

The prior 2000 coverage probe and validation lane were created from earlier
`work/hq-parallel-control` tips:

- Coverage probe final HEAD: `a71a3897b8e074ee43137839481977f9cb4a56c9`
- Validation lane final HEAD: `899e2276fc69041ef36d037cfb50c4b85e679232`
- This finalization lane base HEAD: `0bea0a9b26a69a590f524f6335f13fb86dd4bc71`

The discrepancy is expected because `origin/work/hq-parallel-control` advanced
between the probe, validation, and finalization lanes. This lane persists the
documentation evidence only and does not replay raw generation, change model
logic, or activate current-facing outputs.

## Recommended Next Lane

If Outcome V2 current-player use is desired, run a separate current-player
activation review. That lane must independently verify identity bridge status,
feature freshness, no-leakage policy, blocked-source controls, UI/display
constraints, and protected artifact boundaries.
