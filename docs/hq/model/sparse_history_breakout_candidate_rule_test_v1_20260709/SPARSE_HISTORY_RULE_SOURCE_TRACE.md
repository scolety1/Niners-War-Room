# Sparse-History Rule Source Trace

Prior design packet: `C:\NWR\Niners-War-Room-sparse-history-breakout-candidate-rule-test-v1-20260709\docs\hq\model\sparse_history_breakout_red_team_rookie_young_player_model_design_v1_20260709`

Prior design commit: `f493dbf751e42b1f258df14e41a20fde9274d136`

Prior red-team canonicalization addendum commit: `8e31c89aee7bc2598046206dd0ec8336dce1c248`

Source packets verified:

- Formula Red Team Canonicalization Addendum V1: `C:\NWR\Niners-War-Room-sparse-history-breakout-candidate-rule-test-v1-20260709\docs\hq\master\formula_red_team_canonicalization_addendum_v1_20260709`
- Formula Miss Taxonomy / Red Team Review V1: `C:\NWR\Niners-War-Room-sparse-history-breakout-candidate-rule-test-v1-20260709\docs\hq\model\formula_miss_taxonomy_red_team_review_v1_20260709`
- Ingredient Upgrade Phase Batch Canonicalization / Merge Review V1: `C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\master\ingredient_upgrade_phase_batch_canonicalization_merge_review_v1_20260709`
- Rookie Draft Capital Data Mart Join / Component Test V1: `C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\model\rookie_draft_capital_data_mart_join_component_test_v1_20260709`
- nflverse Snap Counts / Depth Chart Role Sidecar V1: `C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\model\nflverse_snap_depth_role_formula_mart_sidecar_v1_20260709`
- Point-in-Time Injury Availability Data Mart Gate V1: `C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\model\point_in_time_injury_availability_data_mart_gate_v1_20260709`
- Autonomous ffopportunity / NGS Ingredient Upgrade Sequence V2: `C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\model\nwr_autonomous_ingredient_upgrade_sequence_v2_20260709`
- Ingredient Scoreboard Normalization / Best Candidate Consolidation V1: `C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\master\ingredient_scoreboard_normalization_best_candidate_consolidation_v1_20260709`
- Full Review-Only Formula Gauntlet Candidate Arena V1: `C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\model\full_review_only_formula_gauntlet_candidate_arena_v1_20260709`

Sidecar/context joins used by the design loader: `{'snap_depth': 5518, 'injury': 5518, 'rookie_draft': 5518, 'ffopportunity': 1740, 'ngs': 944}`.

Source/use gate: review-only only. Production/model-use, rankings integration, app/runtime behavior, source promotion, push/merge, canonical `local_exports`, hidden sort, recommendation logic, and ranking simulation remain blocked.

Leakage/as-of gate: all test inputs are accepted lagged N-to-N+1 or static post-entry identity context. Same-season/future context remains blocked. ffopportunity/NGS are marked partial-window only.
