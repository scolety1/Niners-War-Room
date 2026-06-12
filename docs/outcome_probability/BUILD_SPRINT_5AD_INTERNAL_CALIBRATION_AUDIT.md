# Build Sprint 5AD: Internal Calibration Audit

## Scope

Sprint 5AD is a tightly scoped internal-only calibration audit using the Sprint 5AA gate contract. It audits whether calibration mechanics could be explored later from the expanded internal validation package. It does not fit or release a calibration layer.

This sprint did not create app percentage values, public/player-facing probabilities, app-readable probability tables, rankings, decision automation, push, deploy, active app/ranking logic changes, or promoted model artifacts.

## Inputs

Inputs reviewed:

- Sprint 5Z expanded internal validation package.
- Sprint 5AA calibration feasibility gate.
- Sprint 5AB expanded package adversarial audit.
- Sprint 5AC overnight handoff.

Known internal-only state:

- Expanded historical universe: 2,118 trainable rows across 2020-2024.
- Train seasons: 2020-2022.
- Validation season: 2023.
- Test season: 2024.
- Allowed outcomes: same-year outcomes only.
- Blocked outcomes: `next_year_starter`, multi-year outcomes, and hazard windows.

## Local Outputs

Local-only outputs were written under:

`local_exports/outcome_probability/sprint_5ad_internal_calibration_audit/`

Created files:

- `internal_calibration_method_audit.csv`
- `internal_calibration_bin_stability.csv`
- `internal_calibration_support_by_outcome.csv`
- `internal_calibration_output_block_audit.csv`
- `internal_calibration_blockers.csv`
- `README_SPRINT_5AD.md`

## Calibration Methods Audited

| Method | 5AD status | Notes |
| --- | --- | --- |
| No calibration | `allowed_internal_reference_only` | Remains the internal baseline/reference from Sprint 5Z. |
| Platt scaling | `feasible_internal_outcome_level_audit_only` | Feasible for a future internal-only mechanics audit; not fit or released here. |
| Outcome-specific calibration | `feasible_internal_outcome_level_audit_only` | Same-year outcomes have aggregate validation/test support. |
| Calibration-by-bin | `aggregate_bins_allowed_for_audit_only` | Diagnostic bins only; not a calibrator. |
| Isotonic calibration | `blocked_by_unstable_sparse_bins` | Validation/test bins contain zero-event cells. |
| Position-specific calibration | `blocked_by_position_slice_instability` | Position/outcome slices remain too thin. |
| Confidence/display bands | `blocked_for_app_display_or_release` | App/player-facing display remains red blocked. |
| Next-year or multi-year calibration | `blocked_outcome_not_in_scope` | `next_year_starter` remains censored/blocked. |

## Aggregate Findings

Same-year outcomes have enough aggregate validation/test support for internal audit discussion, but not production/app release.

Supported internal audit outcomes:

- `same_year_difference_maker`
- `same_year_starter`
- `same_year_useful`
- `same_year_replacement_or_bust`

Blocked:

- `next_year_starter`
- multi-year outcomes
- hazard windows
- position-specific calibration
- isotonic calibration
- any app/player-facing output

## Bin Stability

The bin audit found sparse or zero-event bins in validation/test summaries. That is acceptable for aggregate diagnostics, but it blocks flexible or bin-derived calibration release.

Decision:

- Aggregate bins may be inspected.
- Do not use bins as a calibration layer.
- Do not run isotonic calibration.
- Do not run position-specific calibration.

## Output-Block Audit

Sprint 5AD exports are aggregate-only. The output-block audit passed.

Confirmed absent from 5AD outputs:

- Player IDs.
- Player names.
- Row IDs.
- Per-player probabilities.
- Sortable model scores.
- App probability columns.
- App-readable probability tables.
- Production artifacts.
- Promoted model artifacts.

## Blockers

Production/app modeling remains blocked by:

- App/player-facing probability prohibition.
- Production calibration release gate.
- Final leakage audit.
- Confidence/display gates.
- Release/model-card policy.
- HQ approval.
- `next_year_starter` maturity/censoring policy.
- Sparse bins and position-specific slice instability.

## Verdict

`INTERNAL_CALIBRATION_AUDIT_PASS_WITH_WARNINGS`

Internal work may continue only inside the Sprint 5AA/5AC gate: aggregate-only, same-year outcomes only, no player output, no app output, no rankings, no model promotion.

Production/app modeling remains blocked.

## Confirmed Non-Actions

- No calibrated probabilities were created.
- No app percentage values were created.
- No public/player-facing probabilities were created.
- No rankings were created.
- No decision automation was created.
- No app-readable probability table was created.
- No promoted or released model artifact was created.
- No push or deploy occurred.
- No active app/ranking logic was modified.
