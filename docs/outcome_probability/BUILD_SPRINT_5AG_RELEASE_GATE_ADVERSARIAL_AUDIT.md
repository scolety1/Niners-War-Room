# Build Sprint 5AG: Release Gate Adversarial Audit

## Scope

Sprint 5AG adversarially audits the Sprint 5AF release gate/status contract before any app integration.

This sprint did not create real app percentage values, calibrated probabilities, public/player-facing probabilities, rankings, decision automation, app-readable real probability tables, push, deploy, active app/ranking wiring, promoted model artifacts, or released model artifacts.

## Inputs

Inputs reviewed:

- `src/services/nwr_outcome_release_gate_service.py`
- `tests/test_nwr_outcome_release_gate_service.py`
- Sprint 5AF release gate/status contract documentation.
- Sprint 5AF local-only contract exports.
- App/source/test references for accidental release-gate or model-output wiring.

## Fixes Made

Two adversarial gaps were found and fixed:

1. `ready_released` with all gates true but no probability payload could return an app-readable result with a null probability. It now raises a `ValueError`; release requires an explicit numeric probability payload.
2. The contract export writer could write to any caller-provided path. It now rejects obvious app/ranking output paths such as app pages, active ranking/current-value folders, app probability paths, and player-probability paths.

Focused tests were added for:

- Missing probability payload with all gates true.
- App/ranking output path rejection.
- `ready_internal_only` remaining not app-ready.

## Local Outputs

Local-only outputs were written under:

`local_exports/outcome_probability/sprint_5ag_release_gate_adversarial_audit/`

Created files:

- `release_gate_adversarial_cases.csv`
- `release_gate_output_risk_audit.csv`
- `release_gate_target_audit.csv`
- `release_gate_monotonicity_audit.csv`
- `release_gate_app_isolation_audit.csv`
- `audit_findings.csv`
- `README_SPRINT_5AG.md`

## Adversarial Cases

Cases tested:

- One failed gate with otherwise valid model output.
- Missing gate values.
- Unknown target.
- Blocked target.
- Kicker target.
- `next_year_starter`.
- Multi-year target.
- Old/internal probability payload accidentally supplied.
- Hidden sortable value attempted.
- Confidence label attempted without release.
- `ready_internal_only` accidentally treated as app-ready.
- `ready_released` with one gate false.
- `ready_released` with missing probability payload.
- Difference-maker > Starter monotonicity violation.
- Starter > Useful monotonicity violation.
- App output path attempted.
- Player-facing payload attempted.
- Unknown release gate supplied.

All adversarial cases passed after the two hardening fixes.

## Output-Risk Audit

Result: PASS.

No app-readable real probability table, player probability export, ranking output, decision automation output, or promoted artifact was created.

The output-risk audit found no forbidden player-level output headers in the release-gate contract exports.

## Target/Status Audit

Result: PASS.

- Same-year targets can only release if every gate passes and an explicit probability payload is supplied.
- `ready_internal_only` remains status-only and not app-readable.
- `next_year_starter` remains `blocked_validation_gate`.
- Multi-year targets, hazard windows, injury-lost risk, ambiguous risk, and unknown targets remain `not_applicable`.
- Kickers return `not_applicable`.
- Non-released states return null probability payloads and no hidden sortable probability.

## Monotonicity Audit

Result: PASS.

The contract enforces:

`same_year_difference_maker <= same_year_starter <= same_year_useful`

before any future release path.

## App/Ranking Isolation

Result: PASS.

Searches found no unsafe app/ranking wiring to:

- `nwr_outcome_release_gate_service`
- Sprint 5AF release-gate exports
- Internal model package outputs
- App probability display columns
- Outcome probability sort keys

The service remains isolated from active app pages.

## Verdict

`RELEASE_GATE_AUDIT_PASS_WITH_FIXES`

Status-only app integration can be considered next if it remains non-numeric and does not consume internal model outputs as real probabilities.

Real production/app probabilities remain blocked.

## Confirmed Non-Actions

- No real app percentage values were created.
- No calibrated probabilities were created.
- No public/player-facing probabilities were created.
- No rankings were created.
- No decision automation was created.
- No app-readable real probability tables were created.
- No internal model outputs were wired into active app/ranking logic.
- No promoted or released model artifacts were created.
- No push or deploy occurred.
