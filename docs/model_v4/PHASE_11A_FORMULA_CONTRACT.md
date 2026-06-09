# Phase 11A Formula Contract And Allowed Field Registry

## Purpose

Phase 11A creates the review-only formula contract for Model v4. It does not calculate player scores, promote app surfaces, change active rankings, alter My Team or War Board, or unlock readiness gates.

The contract's core rule is simple: formula modules may consume only the explicit input files, lanes, and JSON paths listed in the allowed-field registry. Generic JSON slurping is forbidden.

## Outputs

- `local_exports/model_v4/formula_contract/latest/formula_allowed_field_registry.csv`
- `local_exports/model_v4/formula_contract/latest/formula_blocked_field_registry.csv`
- `local_exports/model_v4/formula_contract/latest/formula_loader_guard_report.csv`

## Required Module Coverage

- `replacement_vorp_core`: 8 allowed field rows
- `rb_current_value`: 7 allowed field rows
- `wr_current_value`: 7 allowed field rows
- `qb_current_value`: 7 allowed field rows
- `te_current_value`: 7 allowed field rows
- `lifecycle_archetype`: 6 allowed field rows
- `confidence_missingness`: 11 allowed field rows
- `first_down_scoring_evidence`: 2 allowed field rows
- `return_scoring_evidence`: 1 allowed field rows
- `prospect_prior`: 12 allowed field rows
- `rookie_context_review`: 2 allowed field rows

## Hard Rules Locked

- No private-value formula module may consume `market_context_fields_json`.
- ADP, rankings, projections, mock drafts, big boards, and consensus ranks are context only.
- Current prospect formula inputs must come from `admitted_prospect_current_feature_matrix.csv`, except for explicitly admitted factual rookie age and factual NFL draft-capital sidecars.
- Review-only prospects are not formula-admitted.
- Source-limited-not-admitted evidence cannot drive private football value.
- Missing/null evidence cannot become zero, average, or positive evidence.
- Return evidence is direct scoring only, not talent or role signal.
- First-down evidence must use admitted matched-only first-down views.
- Review-only VORP context cannot be consumed as derived evidence.

## Guard Report

- Checks run: 13
- Failed checks: 0

| Check | Status | Issues | Detail |
| --- | --- | ---: | --- |
| `required_modules_present` | pass | 0 | All required Phase 11A modules have at least one admitted field. |
| `required_input_files_exist` | pass | 0 | All formula contract input surfaces exist. |
| `generic_private_json_slurping_blocked` | pass | 0 | Allowed private-value paths are explicit; no lane-wide JSON slurping. |
| `market_projection_rank_private_value_blocked` | pass | 0 | No private-value allowed row contains market/projection/ranking tokens. |
| `current_prospect_input_admitted_only` | pass | 0 | Prospect prior private inputs are limited to the admitted prospect matrix plus explicitly admitted factual age and NFL draft-capital sidecars: local_exports/model_v4/draft_capital/latest/rookie_draft_capital_2026.csv, local_exports/model_v4/evidence_matrices/latest/admitted_prospect_current_feature_matrix.csv, local_exports/model_v4/prospect_age/latest/player_age_2026.csv. |
| `admitted_prospect_rows_require_formula_identity` | pass | 0 | 211 admitted prospect rows all have formula_identity_admitted == True. |
| `workout_zero_placeholders_remain_missing` | pass | 0 | Repaired workout zero placeholders remain null/missing, not zero (28 admitted prospect rows carry repair metadata). |
| `source_limited_not_private_value` | pass | 0 | Source-limited-not-admitted data is absent from private-value registry rows. |
| `first_down_inputs_are_admitted_views_only` | pass | 0 | First-down formula evidence uses admitted matched-only views only. |
| `return_input_is_admitted_direct_scoring_only` | pass | 0 | Return formula evidence uses admitted matched-only direct scoring view only. |
| `review_only_vorp_context_not_formula_admitted` | pass | 0 | Review-only VORP context is blocked from derived/private formula evidence. |
| `blocked_registry_covers_known_hazards` | pass | 0 | Blocked registry includes market, generic JSON, source-limited, and review-only hazards. |
| `loader_assertions_fail_closed` | pass | 0 | Programmatic guard rejects generic JSON, full prospect matrix, market private value, and non-admitted age/draft-capital fields. |

## Formula Stage Boundary

This phase is a contract and loader-guard phase only. The next phase may build review-only replacement/VORP outputs, but it must still use this registry and fail closed on any unregistered field request.
