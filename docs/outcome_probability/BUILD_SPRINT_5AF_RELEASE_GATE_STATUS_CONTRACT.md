# Build Sprint 5AF: Release Gate Status Contract

## Scope

Sprint 5AF creates a release-gate and probability-status contract for future app integration. It does not wire real probabilities into the app and does not create app-readable real probability tables.

This sprint did not create app percentage values, public/player-facing probabilities, rankings, decision automation, push, deploy, active app/ranking logic changes, app-readable real probability tables, promoted model artifacts, or released model artifacts.

## Files Added

- `src/services/nwr_outcome_release_gate_service.py`
- `tests/test_nwr_outcome_release_gate_service.py`

Local-only exports were written under:

`local_exports/outcome_probability/sprint_5af_release_gate_status_contract/`

Created local exports:

- `release_gate_registry.csv`
- `probability_status_codes.csv`
- `target_release_registry_draft.csv`
- `status_precedence_rules.csv`
- `app_safe_display_contract.csv`
- `blocked_probability_paths.csv`
- `README_SPRINT_5AF.md`

## Release Gates

Canonical release gates:

- `leakage_gate`
- `validation_gate`
- `calibration_gate`
- `confidence_gate`
- `documentation_gate`
- `operational_gate`
- `hq_approval_gate`

Hard rule:

`ready_released` requires every release gate to pass. If any gate fails, the first failed gate by deterministic precedence controls the status and the probability payload remains null.

## Probability Status Codes

Canonical status codes:

- `in_development`
- `model_unavailable`
- `needs_data`
- `insufficient_evidence`
- `not_applicable`
- `blocked_leakage_gate`
- `blocked_validation_gate`
- `blocked_calibration_gate`
- `blocked_confidence_gate`
- `blocked_documentation_gate`
- `blocked_operational_gate`
- `blocked_hq_approval`
- `ready_internal_only`
- `ready_released`

Every status except `ready_released` returns:

- Null numeric probability.
- No probability band.
- No hidden sortable probability value.
- No app-readable probability payload.

## Target Registry Draft

Draft same-year targets:

- `same_year_difference_maker`
- `same_year_starter`
- `same_year_useful`
- `same_year_replacement_or_bust`

These are `ready_internal_only` as a registry draft, but remain unreleased for app/player-facing use.

Blocked or not released:

- `next_year_starter`
- multi-year targets
- hazard windows
- injury-lost risk
- ambiguous risk

Kickers return `not_applicable`.

## App-Safe Display Contract

For unreleased targets, future app cells may show only explicit status text:

- `In development`
- `Model unavailable`
- `Needs data`
- `Insufficient evidence`
- `Not applicable`
- gate-specific blocked status

Unreleased targets must not show:

- Numeric probability.
- Probability band.
- Hidden sortable probability value.
- App-compatible probability payload.
- Player-facing probability text.

Future released targets must also satisfy:

- All release gates pass.
- Difference-maker <= Starter <= Useful.
- Debug fields hidden from normal app users.
- Unreleased rows sort as null, not as numeric probability.

## Isolation

The release gate service is isolated and not wired into active app pages. It does not consume internal model output paths. It writes governance/status contract exports only.

## Verdict

`RELEASE_GATE_STATUS_CONTRACT_READY`

Production/app probabilities remain blocked until all release gates pass and HQ explicitly approves release.

## Confirmed Non-Actions

- No real app percentages were created.
- No calibrated probabilities were created.
- No public/player-facing probabilities were created.
- No rankings were created.
- No decision automation was created.
- No app-readable real probability table was created.
- No internal model outputs were wired into app/ranking logic.
- No promoted or released model artifact was created.
- No push or deploy occurred.
