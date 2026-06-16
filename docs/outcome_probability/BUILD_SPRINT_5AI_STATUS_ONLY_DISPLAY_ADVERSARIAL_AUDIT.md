# Build Sprint 5AI Status-Only Display Adversarial Audit

## Verdict

`STATUS_ONLY_DISPLAY_AUDIT_PASS`

Sprint 5AI adversarially audited the Sprint 5AH status-only display adapter before any
active app page imports it. The adapter remains service-contract only. No active app
surface was wired.

## Files Audited

- `src/services/nwr_outcome_status_display_service.py`
- `tests/test_nwr_outcome_status_display_service.py`
- `src/services/nwr_outcome_release_gate_service.py`
- app/ranking code import references

## Adversarial Cases Tested

The audit tested:

- same-year target
- `next_year_starter`
- multi-year target
- hazard target
- kicker position
- unknown target
- missing target
- supplied numeric probability
- supplied probability band
- supplied sortable value
- supplied player ID/name
- supplied internal model output path
- supplied local export path
- `ready_internal_only`
- `ready_released`
- failed release gate
- missing release gate
- monotonicity violation
- rank/sort attempt

All cases either returned status-only null fields or were rejected before a display payload
could be created.

## Probability Leak Audit

Result: pass.

For unreleased/default app configuration, the adapter returns:

- `probability_value=None`
- `probability_band=None`
- `sortable_value=None`
- `is_released=False`
- `is_numeric=False`

`ready_internal_only` remains text-only and unreleased. `ready_released` is explicitly
rejected by the status-only adapter and is not reachable from default app status
configuration.

## Sort And Ranking Risk Audit

Result: pass.

`outcome_status_sort_value()` returns `None`. No hidden score, model score, probability
sort key, ranking output, or decision automation field is produced.

## App And Ranking Isolation

Result: pass.

Searches found no active app/ranking imports of:

- `nwr_outcome_status_display_service`
- `nwr_outcome_release_gate_service`
- Sprint 5T internal logistic package outputs
- Sprint 5AH or 5AI local export directories

The app/ranking surfaces remain isolated from status display and internal model outputs.

## Fixes Made

No fixes were required. No code or tests were changed in Sprint 5AI.

## Local Exports

Sprint 5AI wrote local-only audit exports under:

`local_exports/outcome_probability/sprint_5ai_status_only_display_adversarial_audit/`

Expected files:

- `status_display_adversarial_cases.csv`
- `status_display_output_risk_audit.csv`
- `status_display_sort_risk_audit.csv`
- `status_display_app_isolation_audit.csv`
- `status_display_findings.csv`
- `README_SPRINT_5AI.md`

## Blocked Paths

Still blocked:

- real app percentage values
- calibrated probabilities
- public/player-facing probability numbers
- probability bands
- hidden sortable values
- rankings or sort by model output
- decision automation
- internal logistic/calibration output consumption
- app-readable real probability tables
- promoted or released model artifacts
- push/deploy

## Recommended Next Step

Status-only app wiring can be considered next, but the first active integration should be
minimal, explicitly nonnumeric, and covered by focused app-surface tests.
