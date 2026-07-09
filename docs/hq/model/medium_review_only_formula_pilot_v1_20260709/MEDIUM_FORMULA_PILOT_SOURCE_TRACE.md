# Medium Formula Pilot Source Trace

## Inputs

- Medium Review-Only Formula Pilot Contract V1: `C:\NWR\Niners-War-Room-medium-review-only-formula-pilot-v1-20260709\docs\hq\model\medium_review_only_formula_pilot_contract_v1_20260709`
- Contract commit: `39e5def85d552fe0c0a90257eb217ea4205814ef`
- Formula Data Mart Review-Only CSV: `C:\NWR\Niners-War-Room-formula-data-mart-feature-availability-audit-v1-20260709\docs\hq\data_hygiene\formula_data_mart_feature_availability_audit_v1_20260709\FORMULA_DATA_MART_REVIEW_ONLY.csv`
- Age/Lifecycle Sidecar Review-Only CSV: `C:\NWR\Niners-War-Room-age-lifecycle-sidecar-freeze-validation-v1-20260709\docs\hq\data_hygiene\age_lifecycle_sidecar_freeze_validation_v1_20260709\MODEL_V4_AGE_LIFECYCLE_SIDECAR_REVIEW_ONLY.csv`
- Small Review-Only Formula Pilot V1: `C:\NWR\Niners-War-Room-small-review-only-formula-pilot-v1-20260709\docs\hq\model\small_review_only_formula_pilot_v1_20260709`

## Use Gate

- All rows are review-only.
- No production/model-use rows were admitted.
- No source was promoted.
- No ranking/app/runtime/model behavior changed.
- No canonical `local_exports` writes occurred.

## Leakage / As-Of

The script requires PASS leakage/as-of flags on the Formula Data Mart and rejects blocked age/lifecycle leakage rows. Missing age rows remain caveated and are not treated as production-safe age signals.
