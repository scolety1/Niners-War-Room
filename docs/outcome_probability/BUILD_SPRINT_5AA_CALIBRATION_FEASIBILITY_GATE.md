# Build Sprint 5AA: Calibration Feasibility Gate

## Scope

Sprint 5AA is a gate/audit sprint. It decides whether calibration mechanics can be explored internally after the expanded 5Z validation package.

This sprint did not create app percentage values, public/player-facing probabilities, rankings, app-readable probability tables, per-player probability exports, promoted model artifacts, push, deploy, or active app/ranking logic changes.

No calibration was run in this sprint.

## Local Outputs

Local-only outputs were written under:

`local_exports/outcome_probability/sprint_5aa_calibration_feasibility_gate/`

Created files:

- `calibration_method_feasibility.csv`
- `calibration_support_by_outcome.csv`
- `calibration_blockers.csv`
- `internal_calibration_gate_contract.csv`
- `production_display_blockers.csv`
- `README_SPRINT_5AA.md`

## Evidence Reviewed

Inputs reviewed:

- Sprint 5Y expanded support diagnostics.
- Sprint 5Z expanded internal validation package.
- 2020-2024 trainable universe.
- Train 2020-2022, validation 2023, test 2024 split.
- Same-year outcome event/non-event support.
- Aggregate validation/test metrics.
- Output-block audit and metadata gates.

Expanded same-year support:

| Outcome | Observed rows | Events | Non-events | Validation Brier | Test Brier |
| --- | ---: | ---: | ---: | ---: | ---: |
| `same_year_difference_maker` | 2,118 | 150 | 1,968 | 0.053720 | 0.049472 |
| `same_year_starter` | 2,118 | 293 | 1,825 | 0.085016 | 0.081977 |
| `same_year_useful` | 2,118 | 454 | 1,664 | 0.102262 | 0.111498 |
| `same_year_replacement_or_bust` | 2,118 | 1,664 | 454 | 0.102262 | 0.111498 |
| `next_year_starter` | 1,296 observed | 194 | 1,102 | n/a | n/a |

`next_year_starter` remains blocked because it is only partially observed and 2024 is censored.

## Calibration Method Feasibility

| Method | Classification | Scope |
| --- | --- | --- |
| No calibration | `allowed_internal_mechanics_only` | Internal baseline/validation diagnostics |
| Platt scaling | `allowed_internal_mechanics_only` | Future internal audit only |
| Outcome-specific calibration | `allowed_internal_mechanics_only` | Same-year internal audit only |
| Calibration-by-bin | `allowed_internal_mechanics_only` | Aggregate bins only |
| Isotonic calibration | `blocked_sparse_events` | Blocked |
| Position-specific calibration | `blocked_position_slice_instability` | Blocked |
| Confidence bands | `blocked_for_app_display` | Not app-facing |
| Display bands | `blocked_for_app_display` | Not app-facing |

The only calibration-adjacent path allowed after this sprint is a future internal-only audit of simple Platt or outcome-level mechanics for same-year outcomes. It must not create app/player-facing output.

## Internal Calibration Gate Contract

Any future internal-only calibration audit must include:

- Full run metadata.
- Schema versions.
- Policy IDs.
- Source manifest version.
- Train/validation/test seasons.
- Feature list.
- Code commit.
- Package timestamp.
- `player_output_block=true`
- `app_output_block=true`
- `promotion_allowed=false`
- `production_artifact=false`
- Same-year outcomes only.
- Aggregate outputs only.
- No `player_id`, `player_name`, row ID, per-player probability, app probability column, sortable model score, or model artifact.

Stop conditions:

- Leakage risk.
- App/player-output risk.
- Schema mismatch.
- Unstable holdout.
- Unsafe test failure.

## Blockers

Production/app modeling remains blocked by:

- App/player-facing probability prohibition.
- Production calibration release gate.
- Final leakage audit.
- Display/confidence gates.
- Release policy.
- HQ approval.
- `next_year_starter` censoring.
- Sparse position-specific calibration slices.

## Verdict

`CALIBRATION_FEASIBILITY_READY_FOR_INTERNAL_ONLY_AUDIT`

Sprint 5AB adversarial audit should start before any future calibration mechanics sprint. Production/app modeling remains blocked.

## Confirmed Non-Actions

- No calibration was run.
- No app percentage values created.
- No calibrated probabilities created.
- No public/player-facing probabilities created.
- No rankings created.
- No push or deploy occurred.
- No active app/ranking logic modified.
- No promoted or released model artifact.
