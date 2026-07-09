# Small Formula Pilot Source Trace

## Inputs

- Contract: `C:\NWR\Niners-War-Room-small-review-only-formula-pilot-v1-20260709\docs\hq\model\small_review_only_formula_pilot_contract_v1_20260709`
- Contract commit: `9758b7272aa6be6beb8cd0ee3d89bbe80b049277`
- Formula Data Mart: `C:\NWR\Niners-War-Room-formula-data-mart-feature-availability-audit-v1-20260709\docs\hq\data_hygiene\formula_data_mart_feature_availability_audit_v1_20260709\FORMULA_DATA_MART_REVIEW_ONLY.csv`
- Age/Lifecycle Sidecar: `C:\NWR\Niners-War-Room-age-lifecycle-sidecar-freeze-validation-v1-20260709\docs\hq\data_hygiene\age_lifecycle_sidecar_freeze_validation_v1_20260709\MODEL_V4_AGE_LIFECYCLE_SIDECAR_REVIEW_ONLY.csv`
- Canonical remote expected at lane start: `b125be9ee73f1adc3487c1fa69ae954e8e49790f`

## Use-Gate Summary

- PYF / prior-year points: mandatory anchor baseline.
- Two-year and three-year production: review-only fixed-weight comparisons, no tuning.
- Role archetype: review-only guardrail/miss taxonomy context only.
- Age/lifecycle: review-only formula-family and guardrail context only.
- Confidence cap: caution/coverage context only.

## Guardrails

- No source promotion.
- No Formula Gauntlet.
- No 100-candidate run.
- No champion refinement.
- No ranking/app/runtime/model behavior change.
- No production/model-use.
- No exact Model v4 replay claim.

## Validation Notes

- Candidate count enforced by script: `15`.
- Data mart row count: `5518`.
- Leakage fail rows in mart: `0`.
- As-of fail rows in mart: `0`.
- Age/lifecycle leakage caveat rows: `8`.
- Age/lifecycle identity caveat rows: `11`.
- Age/lifecycle leakage blocked rows: `0`.
- Age/lifecycle identity blocked rows: `0`.
