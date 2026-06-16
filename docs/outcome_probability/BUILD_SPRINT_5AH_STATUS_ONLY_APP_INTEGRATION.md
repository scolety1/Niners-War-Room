# Build Sprint 5AH Status-Only App Integration

## Verdict

`STATUS_ONLY_SERVICE_READY_APP_WIRING_DEFERRED`

Sprint 5AH adds a status-only display adapter for NWR outcome-probability readiness.
It does not wire real probabilities into active app pages, does not create app-readable
probability tables, and does not consume internal model package outputs.

## Scope

This sprint is app-adjacent only. The allowed display payload is nonnumeric status text:

- `status_code`
- `status_label`
- `tooltip_key`
- `status_help`
- `probability_value = None`
- `probability_band = None`
- `sortable_value = None`
- `is_released = False`
- `is_numeric = False`

Active app page wiring was deferred because rankings, player-detail, and draft-room
surfaces are decision-sensitive. The service contract can be adversarially audited before
any component consumes it.

## Files Added

- `src/services/nwr_outcome_status_display_service.py`
- `tests/test_nwr_outcome_status_display_service.py`

## Targets Supported

Status-only display is available for draft same-year targets:

- `same_year_difference_maker`
- `same_year_starter`
- `same_year_useful`
- `same_year_replacement_or_bust`

Blocked or unavailable paths remain nonnumeric:

- `next_year_starter`: `blocked_validation_gate`
- `multi_year_targets`: `not_applicable`
- `hazard_windows`: `not_applicable`
- kicker rows: `not_applicable`

## Status Copy

The app-safe status labels are text only:

- `In development`
- `Model unavailable`
- `Needs data`
- `Insufficient evidence`
- `Not applicable`
- `Blocked by release gate`
- `Internal only - not released`

## Numeric Probability Safety

The adapter cannot request `ready_released`. Its default registry does not pass release
gates or requested probability payloads into the release-gate service. Every default app
display row returns:

- null probability value
- null probability band
- null sortable value
- `is_released=false`
- `is_numeric=false`

The adapter also does not import the internal model package service, does not read local
model exports, and does not write app-compatible probability tables.

## Sort and Ranking Safety

`outcome_status_sort_value()` always returns `None`. Status display must not create a
hidden model score, outcome sort key, ranking value, decision automation field, or player
card percentage.

## App Wiring Decision

Active app wiring is deferred.

Audited candidate surfaces:

- rankings page
- player detail card/panel
- live draft room
- future player-card outcome fields

No app or Streamlit files were modified in this sprint. The next safe step is an
adversarial audit of the status-only adapter and export contract before considering a
minimal component-level integration.

## Local Exports

Sprint 5AH writes local-only audit exports under:

`local_exports/outcome_probability/sprint_5ah_status_only_app_integration/`

Expected files:

- `status_only_app_contract.csv`
- `status_only_target_display_registry.csv`
- `app_surface_integration_audit.csv`
- `blocked_numeric_probability_paths.csv`
- `README_SPRINT_5AH.md`

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

Run Sprint 5AI as an adversarial status-only app integration audit before any active app
surface imports the adapter.
