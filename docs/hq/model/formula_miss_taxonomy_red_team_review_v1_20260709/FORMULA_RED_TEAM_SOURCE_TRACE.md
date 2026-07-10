# Formula Red Team Source Trace

Primary accepted source root:

`C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709`

Read artifacts:

- Formula Data Mart: `C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\data_hygiene\formula_data_mart_feature_availability_audit_v1_20260709\FORMULA_DATA_MART_REVIEW_ONLY.csv`
- Age/lifecycle sidecar: `C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\data_hygiene\age_lifecycle_sidecar_freeze_validation_v1_20260709\MODEL_V4_AGE_LIFECYCLE_SIDECAR_REVIEW_ONLY.csv`
- Gauntlet registry: `C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\model\full_review_only_formula_gauntlet_candidate_arena_v1_20260709\GAUNTLET_CANDIDATE_REGISTRY.csv`
- Cluster assignments: `C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\model\gauntlet_candidate_diversity_clustering_audit_v1_20260709\GAUNTLET_CANDIDATE_CLUSTER_ASSIGNMENTS.csv`
- Diverse refinement registry: `C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\model\diverse_champion_refinement_predeclared_execution_v1_20260709\DIVERSE_CHAMPION_REFINEMENT_CANDIDATE_REGISTRY.csv`
- Snap/depth sidecar: `C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\model\nflverse_snap_depth_role_formula_mart_sidecar_v1_20260709\NFLVERSE_SNAP_DEPTH_ROLE_REVIEW_ONLY_SIDECAR.csv`
- Injury availability sidecar: `C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\model\point_in_time_injury_availability_data_mart_gate_v1_20260709\POINT_IN_TIME_INJURY_AVAILABILITY_REVIEW_ONLY_SIDECAR.csv`
- Rookie/draft sidecar: `C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\model\rookie_draft_capital_data_mart_join_component_test_v1_20260709\ROOKIE_DRAFT_CAPITAL_REVIEW_ONLY_SIDECAR.csv`
- Receiving opportunity sidecar: `C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\model\nflverse_receiving_opportunity_formula_mart_sidecar_v1_20260709\NFLVERSE_RECEIVING_OPPORTUNITY_REVIEW_ONLY_SIDECAR.csv`
- EPA opportunity sidecar: `C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\model\nflverse_epa_opportunity_formula_mart_sidecar_v1_20260709\NFLVERSE_EPA_OPPORTUNITY_REVIEW_ONLY_SIDECAR.csv`
- Team offensive environment sidecar: `C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\model\team_offensive_environment_sidecar_v1_20260709\TEAM_OFFENSIVE_ENVIRONMENT_REVIEW_ONLY_SIDECAR.csv`
- ffopportunity sidecar: `C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\model\nwr_autonomous_ingredient_upgrade_sequence_v2_20260709\FFOPPORTUNITY_EXPECTED_FANTASY_POINTS_REVIEW_ONLY_SIDECAR.csv`
- NGS sidecar: `C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\model\nwr_autonomous_ingredient_upgrade_sequence_v2_20260709\NFLVERSE_NGS_REVIEW_ONLY_SIDECAR.csv`

Source/use gate: all inputs are accepted review-only artifacts. No production/model-use or rankings integration approval is granted here.

Leakage/as-of gate: formulas use lagged Formula Data Mart fields and accepted lagged sidecar fields. Same-season/future context remains blocked.
