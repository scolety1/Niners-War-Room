# Model v4 Historical Receipt Locator and Ledger V1

## Verdict

`YELLOW_MODEL_V4_HISTORICAL_RECEIPT_LEDGER_PARTIAL_WITH_BLOCKERS`

## Clear Answer

This lane located and ledgered existing candidate receipt artifacts, but it did not prove exact Model v4 historical replay. The ledger finds current-board equivalents, partial historical/proxy receipt artifacts, and source/coverage sidecars that can feed a later freeze/schema-validation lane. Exact historical replay remains blocked until season-by-season checkpoint/component/transform receipts are frozen, admitted, and validated.

## Locator Summary

- Receipt families searched: `13`
- Candidate artifacts/folders found: `1898`
- Likely-equivalent artifacts found: `0`
- Partial/current-equivalent artifacts found: `927`
- Highest-value artifact found: `C:\NWR\_manual_recovery_dropzone\current_board_rebuild_inputs_v1\z1\recovered_from_final_laptop_handoff\local_exports\model_v4\current_value\latest\current_player_value_full_board_review_rows.csv`

## Readiness Impact

- Exact Model v4 replay remains blocked.
- Formula Gauntlet tournaments remain blocked.
- 100-candidate Gauntlet remains blocked.
- Champion refinement remains blocked.
- Rankings integration remains blocked.
- No source was promoted.

## Highest-Value Finding

`C:\NWR\_manual_recovery_dropzone\current_board_rebuild_inputs_v1\z1\recovered_from_final_laptop_handoff\local_exports\model_v4\current_value\latest\current_player_value_full_board_review_rows.csv`

This is high value because it is the closest recovered current-board source row file for the already proven current-board rebuild chain. It is not a season-by-season historical equivalent. It can help validate current-board receipt semantics, but exact historical replay still needs historical rows or a Master HQ-approved regeneration/replacement contract.

## Family Coverage Summary

| Receipt Family | Coverage Status | Candidate Count | Replay Impact |
| --- | --- | ---: | --- |
| `checkpoint_review_score` | current-board equivalent only | 43 | Exact replay still blocked. |
| `position_specific_review_score` | partial equivalent | 61 | Needs freeze/schema validation; not exact yet. |
| `lifecycle_age_receipts` | partial equivalent | 429 | Recoverable/regeneratable only with as-of review. |
| `role_archetype_receipts` | partial equivalent | 132 | Review-only regeneration contract needed. |
| `confidence_cap_receipts` | partial equivalent | 600 | Missingness/coverage semantics need validation. |
| `WR_QB_v2_candidate_overlay` | partial equivalent | 98 | Requires human review. |
| `exact_nwr_dynasty_score_and_rank` | partial equivalent | 456 | Historical exact score/rank still not proven. |
| `route_yprr_tprr_exact_receipts` | blocked by source gate | 287 | Route Recovery/source admission required. |
| `red_zone_exact_receipts` | partial equivalent | 154 | Semantic/source gate needed before regeneration. |
| `shadow_model_v2_metrics` | not found | 0 | Missing source or scope-removal decision needed. |
| `return_scoring_receipts` | blocked by source gate | 4 | Source admission required. |
| `source_coverage_matrix_history` | partial equivalent | 65 | Can feed freeze/schema validation. |
| `exact_transform_weight_receipts` | partial equivalent | 594 | Formula/spec decision still required. |

## Freeze / Regeneration Candidates

Potential freeze-next candidates, subject to Master HQ approval and schema validation:

- `checkpoint_review_score` current-board equivalents
- `position_specific_review_score` partial/component artifacts
- `lifecycle_age_receipts` partial artifacts
- `WR_QB_v2_candidate_overlay` partial artifacts, human review required
- `exact_nwr_dynasty_score_and_rank` partial/current-board artifacts, human review required
- `source_coverage_matrix_history` partial/current-board matrices
- `exact_transform_weight_receipts` partial docs/config traces, Master HQ formula/spec decision required

Potential review-only regeneration candidates, subject to a bounded Master HQ contract:

- `role_archetype_receipts`
- `confidence_cap_receipts`
- `red_zone_exact_receipts`

Still blocked or absent:

- `route_yprr_tprr_exact_receipts`
- `return_scoring_receipts`
- `shadow_model_v2_metrics`

## Next Data Hygiene Lane

`Model v4 Historical Receipt Freeze and Schema Validation V1`

That lane should freeze only review-safe derived candidates approved by Master HQ, validate keys/seasons/positions/schema, and decide whether any candidate can close exact replay gaps.
