# Critical Player Source Truth Audit

Generated from active stats-first preview source after source-truth patches. Rankings remain review-only; no formula weights were changed.

## Patches Applied

- Normalized feature metadata now uses the latest source period instead of the first CSV row, so source rows do not look stale by file order.
- Role/usage derivation now merges rows by player identity instead of splitting the same player when sources disagree on suffixes or display names, e.g. Luther Burden vs Luther Burden III.
- Normalization chooses the best same-ID source row for role/injury/projection context rather than blindly using first-file order.

## Audit Summary

| Player | Lifecycle | Identity | Raw latest season/weeks | Raw LVE PPG | Model Value | Rank | Confidence | Main audit flags |
|---|---|---|---:|---:|---:|---|---:|---|
| Luther Burden | year_one_nfl_player | matched via dynastyprocess_sleeper_to_gsis | none/0 | n/a | 50.23 | WR91 | 36.0 | no_nfl_scoring_history<br>missing_projection<br>missing_participation_proxy<br>no_injury_report_rows<br>low_confidence<br>patched_name_suffix_role_join |
| Brian Thomas | year_two_nfl_player | matched via dynastyprocess_sleeper_to_gsis | 2024/17 | 11.49 | 78.73 | WR8 | 79.5 | missing_participation_proxy |
| De'Von Achane | year_three_nfl_player | matched via dynastyprocess_sleeper_to_gsis | 2024/17 | 13.22 | 73.83 | RB5 | 79.5 | missing_participation_proxy<br>patched_identity_role_merge_changed_role_security |
| Lamar Jackson | established_veteran | matched via sleeper_gsis_exact | 2024/17 | 23.4 | 64.74 | QB3 | 81.5 | missing_participation_proxy |
| Chase Brown | year_three_nfl_player | matched via dynastyprocess_sleeper_to_gsis | 2024/16 | 12.86 | 56.67 | RB34 | 79.5 | missing_participation_proxy |
| Kaleb Johnson | year_one_nfl_player | matched via dynastyprocess_sleeper_to_gsis | none/0 | n/a | 58.43 | RB38 | 36.0 | no_nfl_scoring_history<br>missing_projection<br>missing_participation_proxy<br>no_injury_report_rows<br>low_confidence |
| Jayden Higgins | year_one_nfl_player | matched via dynastyprocess_sleeper_to_gsis | none/0 | n/a | 50.51 | WR89 | 36.0 | no_nfl_scoring_history<br>missing_projection<br>missing_participation_proxy<br>no_injury_report_rows<br>low_confidence |
| Brenton Strange | year_three_nfl_player | matched via dynastyprocess_sleeper_to_gsis | 2024/14 | 3.96 | 25.6 | TE41 | 79.5 | missing_participation_proxy |
| Jaxon Smith-Njigba | year_three_nfl_player | matched via dynastyprocess_sleeper_to_gsis | 2024/17 | 9.61 | 62.38 | WR40 | 79.5 | missing_participation_proxy |
| Tee Higgins | established_veteran | matched via dynastyprocess_sleeper_to_gsis | 2024/12 | 12.36 | 70.19 | WR19 | 81.5 | missing_participation_proxy |
| Bijan Robinson | year_three_nfl_player | matched via dynastyprocess_sleeper_to_gsis | 2024/17 | 17.03 | 83.85 | RB1 | 79.5 | missing_participation_proxy |
| Jahmyr Gibbs | year_three_nfl_player | matched via dynastyprocess_sleeper_to_gsis | 2024/17 | 17.82 | 80.82 | RB2 | 79.5 | missing_participation_proxy |
| Kyren Williams | established_veteran | matched via dynastyprocess_sleeper_to_gsis | 2024/16 | 15.16 | 79.32 | RB6 | 81.5 | missing_participation_proxy |

## Player Notes

### Luther Burden
- Identity: matched via dynastyprocess_sleeper_to_gsis; manual review required = false.
- Raw latest scoring: season none, 0 rows, calc LVE PPG n/a, targets 0, rush attempts 0, rush FD 0, rec FD 0, avg snap n/a.
- Normalized: recent LVE 50.0, projection 50.0, role 22.06, workload 0.0, target earning 0.0, FD/TD fit 50.0, injury 100.0, bridge prior 82.0 at weight 0.35.
- Output: Model Value 50.23, WR91, confidence 36.0, warning status blocking.
- Warnings/gaps: blocking_low_confidence|keeper_bubble|low_confidence|missing_lve_scoring_history|missing_participation_proxy|missing_projection_features|model_warning_keeper_fragility|no_injury_report_rows|route_role_fragility|weak_target_earning|wr_unstable_role|young_nfl_bridge_prior_active; review gaps: projections|market/liquidity; critical gaps: none.
- Top receipt contributions: private_lve_value:dynasty_hold_value=18.444; private_lve_value:young_nfl_bridge_prior=17.1045; dynasty_hold_value:age_curve=16.2; private_lve_value:win_now_value=14.6874; dynasty_hold_value:lve_structural_formula_adjustment=-14.0.

### Brian Thomas
- Identity: matched via dynastyprocess_sleeper_to_gsis; manual review required = false.
- Raw latest scoring: season 2024, 17 rows, calc LVE PPG 11.49, targets 133.0, rush attempts 6.0, rush FD 3.0, rec FD 53.0, avg snap 79.4.
- Normalized: recent LVE 76.63, projection 73.7, role 64.84, workload 78.24, target earning 88.88, FD/TD fit 59.43, injury 80.0, bridge prior 90.0 at weight 0.2.
- Output: Model Value 78.73, WR8, confidence 79.5, warning status ready.
- Warnings/gaps: missing_participation_proxy|young_nfl_bridge_prior_active; review gaps: market/liquidity; critical gaps: none.
- Top receipt contributions: private_lve_value:dynasty_hold_value=45.849; private_lve_value:win_now_value=31.2942; dynasty_hold_value:target_earning_stability=21.3312; win_now_value:target_earning_stability=17.776; dynasty_hold_value:age_curve=16.92.

### De'Von Achane
- Identity: matched via dynastyprocess_sleeper_to_gsis; manual review required = false.
- Raw latest scoring: season 2024, 17 rows, calc LVE PPG 13.22, targets 87.0, rush attempts 203.0, rush FD 37.0, rec FD 30.0, avg snap 62.4.
- Normalized: recent LVE 85.36, projection 80.69, role 65.26, workload 62.49, target earning 75.93, FD/TD fit 62.17, injury 59.18, bridge prior 73.0 at weight 0.08.
- Output: Model Value 73.83, RB5, confidence 79.5, warning status model_warning.
- Warnings/gaps: injury_risk|missing_participation_proxy|young_nfl_bridge_prior_active; review gaps: market/liquidity; critical gaps: none.
- Top receipt contributions: private_lve_value:dynasty_hold_value=43.626; private_lve_value:win_now_value=30.24; dynasty_hold_value:age_curve=22.8; win_now_value:expected_lve_points_score=18.7792; win_now_value:weighted_recent_lve_ppg_score=15.3648.

### Lamar Jackson
- Identity: matched via sleeper_gsis_exact; manual review required = false.
- Raw latest scoring: season 2024, 17 rows, calc LVE PPG 23.4, targets 0.0, rush attempts 139.0, rush FD 46.0, rec FD 0.0, avg snap 96.5.
- Normalized: recent LVE 89.92, projection 84.34, role 75.24, workload 0.96, target earning 50.0, FD/TD fit 46.29, injury 37.22, bridge prior  at weight .
- Output: Model Value 64.74, QB3, confidence 81.5, warning status model_warning.
- Warnings/gaps: injury_risk|keeper_bubble|missing_participation_proxy|model_warning_keeper_fragility|pocket_qb_1qb_suppression|qb_below_replacement_edge|replaceable_1qb_profile; review gaps: market/liquidity; critical gaps: none.
- Top receipt contributions: private_lve_value:dynasty_hold_value=40.096; private_lve_value:win_now_value=34.6456; win_now_value:role_security=21.0672; win_now_value:expected_lve_points_score=19.7824; dynasty_hold_value:role_security=18.0576.

### Chase Brown
- Identity: matched via dynastyprocess_sleeper_to_gsis; manual review required = false.
- Raw latest scoring: season 2024, 16 rows, calc LVE PPG 12.86, targets 65.0, rush attempts 229.0, rush FD 49.0, rec FD 23.0, avg snap 62.8.
- Normalized: recent LVE 59.45, projection 59.96, role 58.06, workload 54.72, target earning 52.28, FD/TD fit 47.5, injury 50.36, bridge prior 44.0 at weight 0.08.
- Output: Model Value 56.67, RB34, confidence 79.5, warning status model_warning.
- Warnings/gaps: committee_risk|injury_risk|keeper_bubble|missing_participation_proxy|model_warning_keeper_fragility|weak_chain_or_td_role|young_nfl_bridge_prior_active; review gaps: market/liquidity; critical gaps: none.
- Top receipt contributions: private_lve_value:dynasty_hold_value=34.344; private_lve_value:win_now_value=22.948; dynasty_hold_value:age_curve=19.68; win_now_value:expected_lve_points_score=13.079; win_now_value:lve_projection_value=10.7928.

### Kaleb Johnson
- Identity: matched via dynastyprocess_sleeper_to_gsis; manual review required = false.
- Raw latest scoring: season none, 0 rows, calc LVE PPG n/a, targets 0, rush attempts 0, rush FD 0, rec FD 0, avg snap n/a.
- Normalized: recent LVE 50.0, projection 50.0, role 10.53, workload 0.03, target earning 0.0, FD/TD fit 50.0, injury 100.0, bridge prior 73.0 at weight 0.35.
- Output: Model Value 58.43, RB38, confidence 36.0, warning status blocking.
- Warnings/gaps: blocking_low_confidence|committee_risk|keeper_bubble|low_confidence|missing_lve_scoring_history|missing_participation_proxy|missing_projection_features|model_warning_keeper_fragility|no_injury_report_rows|young_nfl_bridge_prior_active; review gaps: projections|market/liquidity; critical gaps: none.
- Top receipt contributions: private_lve_value:dynasty_hold_value=35.19; dynasty_hold_value:age_curve=22.8; dynasty_hold_value:injury_durability=18.0; private_lve_value:win_now_value=15.392; win_now_value:expected_lve_points_score=11.0.

### Jayden Higgins
- Identity: matched via dynastyprocess_sleeper_to_gsis; manual review required = false.
- Raw latest scoring: season none, 0 rows, calc LVE PPG n/a, targets 0, rush attempts 0, rush FD 0, rec FD 0, avg snap n/a.
- Normalized: recent LVE 50.0, projection 50.0, role 22.09, workload 0.0, target earning 0.0, FD/TD fit 50.0, injury 100.0, bridge prior 82.0 at weight 0.35.
- Output: Model Value 50.51, WR89, confidence 36.0, warning status blocking.
- Warnings/gaps: blocking_low_confidence|keeper_bubble|low_confidence|missing_lve_scoring_history|missing_participation_proxy|missing_projection_features|model_warning_keeper_fragility|no_injury_report_rows|route_role_fragility|weak_target_earning|wr_unstable_role|young_nfl_bridge_prior_active; review gaps: projections|market/liquidity; critical gaps: none.
- Top receipt contributions: private_lve_value:dynasty_hold_value=18.8616; private_lve_value:young_nfl_bridge_prior=16.9575; dynasty_hold_value:age_curve=16.92; private_lve_value:win_now_value=14.6916; dynasty_hold_value:lve_structural_formula_adjustment=-14.0.

### Brenton Strange
- Identity: matched via dynastyprocess_sleeper_to_gsis; manual review required = false.
- Raw latest scoring: season 2024, 14 rows, calc LVE PPG 3.96, targets 53.0, rush attempts 0.0, rush FD 0.0, rec FD 21.0, avg snap 54.2.
- Normalized: recent LVE 30.53, projection 36.82, role 39.38, workload 32.63, target earning 47.18, FD/TD fit 26.96, injury 40.95, bridge prior 77.0 at weight 0.08.
- Output: Model Value 25.6, TE41, confidence 79.5, warning status model_warning.
- Warnings/gaps: blocking_dependency_risk|drop_candidate|injury_risk|keeper_bubble|low_route_te_profile|missing_participation_proxy|model_warning_keeper_fragility|replaceable_no_premium_te|weak_te_target_earning|young_nfl_bridge_prior_active; review gaps: market/liquidity; critical gaps: none.
- Top receipt contributions: private_lve_value:dynasty_hold_value=24.6; private_lve_value:te_no_premium_suppression=-18.0; private_lve_value:win_now_value=16.464; dynasty_hold_value:route_role=15.0; win_now_value:route_role=14.0.

### Jaxon Smith-Njigba
- Identity: matched via dynastyprocess_sleeper_to_gsis; manual review required = false.
- Raw latest scoring: season 2024, 17 rows, calc LVE PPG 9.61, targets 137.0, rush attempts 5.0, rush FD 1.0, rec FD 55.0, avg snap 86.4.
- Normalized: recent LVE 49.76, projection 52.21, role 59.43, workload 67.65, target earning 70.25, FD/TD fit 42.07, injury 72.68, bridge prior 90.0 at weight 0.08.
- Output: Model Value 62.38, WR40, confidence 79.5, warning status model_warning.
- Warnings/gaps: keeper_bubble|missing_participation_proxy|model_warning_keeper_fragility|route_role_fragility|young_nfl_bridge_prior_active; review gaps: market/liquidity; critical gaps: none.
- Top receipt contributions: private_lve_value:dynasty_hold_value=37.265; private_lve_value:win_now_value=23.7594; dynasty_hold_value:age_curve=16.92; dynasty_hold_value:target_earning_stability=16.86; win_now_value:target_earning_stability=14.05.

### Tee Higgins
- Identity: matched via dynastyprocess_sleeper_to_gsis; manual review required = false.
- Raw latest scoring: season 2024, 12 rows, calc LVE PPG 12.36, targets 109.0, rush attempts 0.0, rush FD 0.0, rec FD 48.0, avg snap 79.1.
- Normalized: recent LVE 68.64, projection 67.31, role 59.42, workload 77.08, target earning 82.23, FD/TD fit 57.63, injury 0.0, bridge prior  at weight .
- Output: Model Value 70.19, WR19, confidence 81.5, warning status model_warning.
- Warnings/gaps: injury_risk|missing_participation_proxy|route_role_fragility; review gaps: market/liquidity; critical gaps: none.
- Top receipt contributions: private_lve_value:dynasty_hold_value=41.441; private_lve_value:win_now_value=28.749; dynasty_hold_value:target_earning_stability=19.7352; dynasty_hold_value:age_curve=16.92; win_now_value:target_earning_stability=16.446.

### Bijan Robinson
- Identity: matched via dynastyprocess_sleeper_to_gsis; manual review required = false.
- Raw latest scoring: season 2024, 17 rows, calc LVE PPG 17.03, targets 72.0, rush attempts 304.0, rush FD 82.0, rec FD 20.0, avg snap 75.4.
- Normalized: recent LVE 90.33, projection 84.66, role 71.53, workload 80.25, target earning 82.05, FD/TD fit 75.54, injury 86.36, bridge prior 97.0 at weight 0.08.
- Output: Model Value 83.85, RB1, confidence 79.5, warning status ready.
- Warnings/gaps: missing_participation_proxy|young_nfl_bridge_prior_active; review gaps: market/liquidity; critical gaps: none.
- Top receipt contributions: private_lve_value:dynasty_hold_value=50.364; private_lve_value:win_now_value=32.84; dynasty_hold_value:age_curve=22.8; win_now_value:expected_lve_points_score=19.8726; win_now_value:weighted_recent_lve_ppg_score=16.2594.

### Jahmyr Gibbs
- Identity: matched via dynastyprocess_sleeper_to_gsis; manual review required = false.
- Raw latest scoring: season 2024, 17 rows, calc LVE PPG 17.82, targets 63.0, rush attempts 250.0, rush FD 70.0, rec FD 25.0, avg snap 55.3.
- Normalized: recent LVE 96.84, projection 89.87, role 48.29, workload 71.41, target earning 71.68, FD/TD fit 75.43, injury 69.04, bridge prior 91.0 at weight 0.08.
- Output: Model Value 80.82, RB2, confidence 79.5, warning status model_warning.
- Warnings/gaps: committee_risk|missing_participation_proxy|young_nfl_bridge_prior_active; review gaps: market/liquidity; critical gaps: none.
- Top receipt contributions: private_lve_value:dynasty_hold_value=47.736; private_lve_value:win_now_value=32.588; dynasty_hold_value:age_curve=22.8; win_now_value:expected_lve_points_score=21.3048; win_now_value:weighted_recent_lve_ppg_score=17.4312.

### Kyren Williams
- Identity: matched via dynastyprocess_sleeper_to_gsis; manual review required = false.
- Raw latest scoring: season 2024, 16 rows, calc LVE PPG 15.16, targets 40.0, rush attempts 316.0, rush FD 85.0, rec FD 6.0, avg snap 86.4.
- Normalized: recent LVE 100.0, projection 92.4, role 70.54, workload 89.85, target earning 56.21, FD/TD fit 85.53, injury 43.22, bridge prior  at weight .
- Output: Model Value 79.32, RB6, confidence 81.5, warning status model_warning.
- Warnings/gaps: injury_risk|missing_participation_proxy|rb_workload_injury_fragility; review gaps: market/liquidity; critical gaps: none.
- Top receipt contributions: private_lve_value:dynasty_hold_value=44.088; private_lve_value:win_now_value=35.228; dynasty_hold_value:age_curve=22.8; win_now_value:expected_lve_points_score=22.0; win_now_value:weighted_recent_lve_ppg_score=18.0.

## Bottom Line

- No identity mismatches were found among the named players after suffix handling.
- The largest unresolved source limitation is missing participation/route proxy coverage; this appears broadly across the public nflverse import and should keep rankings review-only.
- First-year NFL players without NFL production or projections, especially Luther Burden, Kaleb Johnson, and Jayden Higgins, are correctly low-confidence bridge assets rather than clean veteran reads.
- JSN vs Tee remains a source/data question, not a proven formula bug: the active raw import gives Tee stronger 2024 LVE PPG and target-earning normalization, while JSN remains lower on normalized production/efficiency. This should be revisited when fuller/current projection and participation data are imported.
- No formula-weight changes were made.
