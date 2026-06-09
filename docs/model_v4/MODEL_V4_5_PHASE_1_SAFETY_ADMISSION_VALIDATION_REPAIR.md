# Model v4.5 Phase 1 - Safety And Admission Validation Repair

## Purpose

Phase 1 resolves the external-audit caution that the Phase 11A loader guard still failed `current_prospect_input_admitted_only` after factual rookie age and factual 2026 NFL draft capital were added as prospect-prior sidecar inputs.

This phase does not change formulas, scores, app promotion, active rankings, My Team, or War Board. It only tightens and documents the admission contract.

## What Changed

- The formula contract now defines explicit admitted prospect-prior private inputs:
  - `local_exports/model_v4/evidence_matrices/latest/admitted_prospect_current_feature_matrix.csv`
  - `local_exports/model_v4/prospect_age/latest/player_age_2026.csv`
  - `local_exports/model_v4/draft_capital/latest/rookie_draft_capital_2026.csv`
- The guard check now distinguishes:
  - the admitted prospect matrix for current prospect feature rows
  - factual rookie age as an admitted lifecycle sidecar
  - factual NFL draft capital as an admitted draft-result sidecar
- The guard still blocks:
  - `prospect_current_feature_matrix.csv`
  - generic factual / derived / prospect-prior JSON slurping
  - market, ADP, projection, mock draft, big-board, ranking, or consensus fields
  - non-admitted age or draft-capital fields such as source row ordering or mock-draft rank
- Required input validation now checks that the factual age and draft-capital sidecar files exist.

## Regenerated Outputs

- `local_exports/model_v4/formula_contract/latest/formula_allowed_field_registry.csv`
- `local_exports/model_v4/formula_contract/latest/formula_blocked_field_registry.csv`
- `local_exports/model_v4/formula_contract/latest/formula_loader_guard_report.csv`
- `docs/model_v4/PHASE_11A_FORMULA_CONTRACT.md`

## Guard Result

The regenerated loader guard report now passes all checks. The previously failing `current_prospect_input_admitted_only` check now reports:

`pass`

The check detail states that prospect-prior private inputs are limited to the admitted prospect matrix plus the explicitly admitted factual age and NFL draft-capital sidecars.

## Test Coverage

Updated focused tests prove:

- prospect-prior private inputs are limited to the admitted matrix plus factual sidecars
- factual rookie age is admitted only through `rookie_age_intake_csv` with `age_years_decimal|age_total_months`
- factual draft capital is admitted only through `rookie_draft_capital_csv` with `round|overall_pick|draft_day`
- non-admitted age/draft-capital fields fail closed
- full raw prospect matrix access still fails closed
- market/rank/projection fields remain blocked
- the loader guard report passes

## Verdict

Guard issue repaired. Model v4.5 can proceed to Phase 2 UI consolidation without formula repair.
