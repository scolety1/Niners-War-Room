# Build Sprint 5AJ Status-Only Player Detail Wiring

## Verdict

`STATUS_ONLY_PLAYER_DETAIL_WIRING_READY`

Sprint 5AJ wires the audited status-only outcome display adapter into the player detail
card payload and component. The integration is text-only and nonnumeric. It does not add
rankings columns, draft-room recommendations, app-readable probability tables, internal
model output consumption, or sortable outcome values.

## Files Changed

- `src/services/player_detail_card_service.py`
- `app/components/player_detail_card.py`
- `tests/test_player_detail_card_service.py`
- `tests/test_player_detail_card_component.py`

## Player Detail Payload Contract

The player detail card payload now includes:

- `outcome_status`
- `outcome_model_statuses`

Each status row is supplied by the audited status-only adapter and preserves:

- target name
- target label
- status label
- status help text
- tooltip key
- `probability_value=None`
- `probability_band=None`
- `sortable_value=None`
- `is_numeric=False`
- `is_released=False`

## Rendered App Surface

The player detail card now renders an **Outcome Model Status** section with text-only
columns:

- Outcome
- Status
- Help

The guardrail copy shown near the section is:

`Outcome model is in development. No probabilities are released yet.`

## Target Behavior

Same-year targets display `In development`:

- `same_year_difference_maker`
- `same_year_starter`
- `same_year_useful`
- `same_year_replacement_or_bust`

Blocked or unavailable paths remain nonnumeric:

- `next_year_starter`: `Blocked by release gate`
- multi-year targets: `Not applicable`
- hazard targets: `Not applicable`
- kicker rows: `Not applicable`

## Numeric Probability Leak Checks

Passed:

- no numeric probability is returned
- no probability band is returned
- no sortable value is returned
- no hidden score is created
- no app-readable probability table is created
- no internal model output path is consumed
- no local outcome export path is read
- no player-facing probability payload is created

## Sort And Ranking Safety

Passed:

- no rankings table columns were added
- rankings sorting was not changed
- player detail status rows do not expose sort keys
- no decision automation was introduced

## Local Exports

Sprint 5AJ writes local-only audit exports under:

`local_exports/outcome_probability/sprint_5aj_status_only_player_detail_wiring/`

Expected files:

- `player_detail_status_only_contract.csv`
- `app_surface_wiring_audit.csv`
- `numeric_probability_leak_check.csv`
- `sort_risk_check.csv`
- `README_SPRINT_5AJ.md`

## Remaining Blocks

Still blocked:

- real app percentage values
- calibrated probabilities
- public/player-facing probability numbers
- rankings or sort by outcome model
- decision automation
- internal logistic/calibration output consumption
- app-readable real probability tables
- promoted or released model artifacts
- push/deploy

## Recommended Next Step

Run an adversarial app-surface audit on the player detail wiring before considering any
additional app surfaces.
