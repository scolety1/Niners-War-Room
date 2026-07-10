# Age / Lifecycle Source Trace

Inputs:

- Age/lifecycle sidecar: `C:\NWR\Niners-War-Room-age-lifecycle-sidecar-freeze-validation-v1-20260709\docs\hq\data_hygiene\age_lifecycle_sidecar_freeze_validation_v1_20260709\MODEL_V4_AGE_LIFECYCLE_SIDECAR_REVIEW_ONLY.csv`
- Sidecar SHA256: `623de1acd6fc1d885cf4b645be62d4bd4f9032b33de723e6547a3c8070c4573a`
- Formula Data Mart review-only panel: `C:\NWR\Niners-War-Room-formula-data-mart-feature-availability-audit-v1-20260709\docs\hq\data_hygiene\formula_data_mart_feature_availability_audit_v1_20260709\FORMULA_DATA_MART_REVIEW_ONLY.csv`
- Formula Data Mart SHA256: `705ce26c9b3649405efe42af135204e98bcad91ae718b43d55b5415fcef6159f`
- Role archetype component signal reference: `C:\NWR\Niners-War-Room-age-lifecycle-component-signal-test-v1-20260709\docs\hq\model\model_v4_role_archetype_component_signal_test_v1_20260709`
- Confidence cap component signal reference: `C:\NWR\Niners-War-Room-age-lifecycle-component-signal-test-v1-20260709\docs\hq\model\model_v4_confidence_cap_component_signal_test_v1_20260709`
- System audit reference: `C:\NWR\Niners-War-Room-age-lifecycle-component-signal-test-v1-20260709\docs\hq\master\nwr_full_system_audit_integration_map_v1_20260709`

Join:

- Exact `player_id + season + position`.
- No fuzzy name matching.
- No source promotion.
- No production/model-use approval.
- No ranking, app, runtime, or model behavior changed.
