# Gauntlet Failed Or Weak Candidates

Failed, weak, or blocked candidates remain review artifacts only. No production behavior changed.

- `GAUNTLET_002_PYF_PRIOR_RANK_ANCHOR` (`A_PYF_SIMPLE_BASELINE`): `WEAK_REVIEW_ONLY`; Spearman `0.742` vs PYF `0.741`; reason `roughly_matches_pyf`.
- `GAUNTLET_003_PRIOR_YEAR_PPG_BASELINE` (`A_PYF_SIMPLE_BASELINE`): `FAILED_VS_PYF`; Spearman `0.733` vs PYF `0.741`; reason `does_not_beat_pyf`.
- `GAUNTLET_004_PYF_WINSOR_05` (`A_PYF_SIMPLE_BASELINE`): `WEAK_REVIEW_ONLY`; Spearman `0.741` vs PYF `0.741`; reason `roughly_matches_pyf`.
- `GAUNTLET_005_PYF_WINSOR_10` (`A_PYF_SIMPLE_BASELINE`): `FAILED_VS_PYF`; Spearman `0.741` vs PYF `0.741`; reason `does_not_beat_pyf`.
- `GAUNTLET_024_THREE_YEAR_40_35_25` (`C_THREE_YEAR_WEIGHTED_PRODUCTION`): `FAILED_VS_PYF`; Spearman `0.740` vs PYF `0.741`; reason `does_not_beat_pyf`.
- `GAUNTLET_068_SPARSE_FALLBACK_TWO_67` (`F_SPARSE_HISTORY_GUARD`): `FAILED_VS_PYF`; Spearman `0.738` vs PYF `0.741`; reason `does_not_beat_pyf`.
- `GAUNTLET_076_LOW_GAMES_FALLBACK_TWO_75` (`G_LOW_GAMES_GUARD`): `FAILED_VS_PYF`; Spearman `0.738` vs PYF `0.741`; reason `does_not_beat_pyf`.
- `GAUNTLET_104_ROBUST_WINSOR_PYF_05` (`L_ROBUST_WINSORIZED_PRODUCTION`): `WEAK_REVIEW_ONLY`; Spearman `0.741` vs PYF `0.741`; reason `roughly_matches_pyf`.
- `GAUNTLET_107_ROBUST_WINSOR_PYF_10` (`L_ROBUST_WINSORIZED_PRODUCTION`): `FAILED_VS_PYF`; Spearman `0.741` vs PYF `0.741`; reason `does_not_beat_pyf`.
- `GAUNTLET_111_RANK_POINTS_PYF_POINTS_RANK_80_20` (`M_HYBRID_RANK_POINTS`): `WEAK_REVIEW_ONLY`; Spearman `0.742` vs PYF `0.741`; reason `roughly_matches_pyf`.
- `GAUNTLET_112_RANK_POINTS_PYF_POINTS_RANK_60_40` (`M_HYBRID_RANK_POINTS`): `WEAK_REVIEW_ONLY`; Spearman `0.742` vs PYF `0.741`; reason `roughly_matches_pyf`.
- `GAUNTLET_115_PFR_RB_BRK_TKL_RAW` (`N_RB_ONLY_BROKEN_TACKLE_CONTEXT`): `BLOCKED_OR_INVALID`; Spearman `` vs PYF ``; reason `actual_pfr_broken_tackle_values_not_in_formula_data_mart`.
- `GAUNTLET_116_PFR_RB_BRK_TKL_PER_GAME` (`N_RB_ONLY_BROKEN_TACKLE_CONTEXT`): `BLOCKED_OR_INVALID`; Spearman `` vs PYF ``; reason `actual_pfr_broken_tackle_values_not_in_formula_data_mart`.
- `GAUNTLET_117_PFR_RB_BRK_TKL_PER_ATTEMPT_DIAGNOSTIC` (`N_RB_ONLY_BROKEN_TACKLE_CONTEXT`): `BLOCKED_OR_INVALID`; Spearman `` vs PYF ``; reason `actual_pfr_broken_tackle_values_not_in_formula_data_mart`.
- `GAUNTLET_118_RED_ZONE_CARRIES_PARTIAL` (`O_PARTIAL_RED_ZONE_CONTEXT`): `BLOCKED_OR_INVALID`; Spearman `` vs PYF ``; reason `partial_2024_2025_only_not_fair_for_2013_2025_gauntlet`.
- `GAUNTLET_119_RED_ZONE_TARGETS_PARTIAL` (`O_PARTIAL_RED_ZONE_CONTEXT`): `BLOCKED_OR_INVALID`; Spearman `` vs PYF ``; reason `partial_2024_2025_only_not_fair_for_2013_2025_gauntlet`.
- `GAUNTLET_120_RED_ZONE_TD_OPPORTUNITY_PARTIAL` (`O_PARTIAL_RED_ZONE_CONTEXT`): `BLOCKED_OR_INVALID`; Spearman `` vs PYF ``; reason `partial_2024_2025_only_not_fair_for_2013_2025_gauntlet`.
