# Rookie Draft Capital Source Trace

## Prior Context

- Remote HQ: `b125be9ee73f1adc3487c1fa69ae954e8e49790f`
- Prior market/ADP commit: `ee4c1505008bfead024aa326fb07155297491d91`
- Prior market/ADP artifact: `C:\NWR\Niners-War-Room-rookie-draft-capital-data-mart-join-component-test-v1-20260709\docs\hq\model\historical_market_adp_source_gate_data_mart_join_v1_20260709`
- Scoreboard normalization artifact: `C:\NWR\Niners-War-Room-rookie-draft-capital-data-mart-join-component-test-v1-20260709\docs\hq\master\ingredient_scoreboard_normalization_best_candidate_consolidation_v1_20260709`
- High-value signal locator artifact: `C:\NWR\Niners-War-Room-high-value-signal-data-locator-audit-v1-20260709\docs\hq\data_hygiene\high_value_signal_data_locator_audit_v1_20260709`
- Formula Data Mart: `C:\NWR\Niners-War-Room-formula-data-mart-feature-availability-audit-v1-20260709\docs\hq\data_hygiene\formula_data_mart_feature_availability_audit_v1_20260709\FORMULA_DATA_MART_REVIEW_ONLY.csv`
- Age/lifecycle sidecar: `C:\NWR\Niners-War-Room-age-lifecycle-sidecar-freeze-validation-v1-20260709\docs\hq\data_hygiene\age_lifecycle_sidecar_freeze_validation_v1_20260709\MODEL_V4_AGE_LIFECYCLE_SIDECAR_REVIEW_ONLY.csv`
- Gauntlet scoring script/registry: `C:\NWR\Niners-War-Room-full-review-only-formula-gauntlet-candidate-arena-v1-20260709\docs\hq\model\full_review_only_formula_gauntlet_candidate_arena_v1_20260709\run_full_review_only_formula_gauntlet_candidate_arena_v1.py`
- Gauntlet cluster assignments: `C:\NWR\Niners-War-Room-gauntlet-candidate-diversity-clustering-audit-v1-20260709\docs\hq\model\gauntlet_candidate_diversity_clustering_audit_v1_20260709\GAUNTLET_CANDIDATE_CLUSTER_ASSIGNMENTS.csv`

## Primary Draft Sources

- `C:\NWR\Niners-War-Room-rookie-draft-capital-data-mart-join-component-test-v1-20260709\docs\hq\rookie_outcomes\rookie_pre_draft_asof_coverage_builder_v1_20260630\rookie_drafted_admission_manifest.csv`
- `C:\NWR\Niners-War-Room-rookie-draft-capital-data-mart-join-component-test-v1-20260709\docs\hq\rookie_outcomes\rookie_outcomes_drafted_only_feature_policy_nflverse_green_rerun_20260630\drafted_only_admission_gate_refresh_audit.csv`
- `C:\NWR\Niners-War-Room-rookie-draft-capital-data-mart-join-component-test-v1-20260709\docs\hq\rookie_outcomes\rookie_drafted_only_nflverse_feature_gate_evidence_v1_20260630\rookie_feature_gate_matrix.csv`
- `C:\NWR\Niners-War-Room-rookie-draft-capital-data-mart-join-component-test-v1-20260709\docs\hq\rookie_outcomes\rookie_draft_capital_coverage_repair_v2_20260630\rookie_draft_capital_repair_v2_matrix.csv`
- `C:\NWR\Niners-War-Room-rookie-draft-capital-data-mart-join-component-test-v1-20260709\docs\hq\rookie_outcomes\rookie_draft_capital_coverage_repair_v2_20260630\rookie_feature_policy_draft_capital_v2_matrix.csv`
- `C:\NWR\Niners-War-Room-rookie-draft-capital-data-mart-join-component-test-v1-20260709\docs\hq\rookie_outcomes\rookie_pre_draft_asof_coverage_builder_v1_20260630\rookie_pre_draft_asof_coverage_matrix.csv`

## Safety Trace

No network fetch, paid/API/free-trial/API-key work, SportsDataIO, PFF Elusive Rating, current-only ADP, same-season/future leakage, source promotion, push, merge, canonical `local_exports` mutation, production/model-use, rankings integration, or app/runtime change occurred.
