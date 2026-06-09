# Top/Bottom Current-Player Sanity Scan

Date: 2026-06-05

Mode: review-only refinement prep.

Purpose: scan the highest and lowest current-player checkpoint rows for human
review before any formula tuning. This report is evidence only. `Surprise` and
`review` labels do not mean wrong and are not trade, cut, keep, draft, buy,
sell, defer, target, or start/sit recommendations.

## Source

- Source path:
  `local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv`
- Score column: `checkpoint_review_score`
- Lineage: `review_v4_current_player`
- Allowed use: `review_only_current_value_checkpoint`
- Blocked use: `do_not_use_as_final_ranking_or_roster_recommendation`
- Sort used in this report: numeric `checkpoint_review_score` descending, with
  blank scores treated as missing-score manual-review rows at the bottom.
- Original CSV order is preserved as `File Row` because the checkpoint file is
  not globally sorted by score across position modules.

## Snapshot Counts

- Total current-player checkpoint rows: 80.
- Rows with numeric primary score: 75.
- Rows with blank primary score: 5.
- Rows with `capped_review_required`: 29.
- Rows with identity/team warning text: 15.
- Rows with low-evidence warning text: 11.
- Top 50 position mix: WR 26, RB 15, TE 5, QB 4.
- Bottom 50 position mix: WR 29, TE 8, RB 7, QB 6.

## Review Reason Labels

- `top_band_with_source_or_cap_warning`: top-10 score plus source/cap warning
  text.
- `te_near_top_overall_review`: TE appears in the top 20 by current score.
- `one_qb_near_top_overall_review`: QB appears in the top 20 by current score.
- `identity_team_review`: team mismatch, historical team, or identity-review
  warning text.
- `low_evidence_review`: missing stats-first, missing VORP anchor,
  no-historical, or shifted-header warning text.
- `rb_age_window_review`: RB age-window or age-cliff warning text.
- `format_cap_review`: 1QB or no-premium-TE cap warning text.
- `missing_primary_score_manual_review`: blank primary score.
- `low_score_boundary_review`: numeric score below 15.
- `routine_warning_readback`: warning text is present, but no special scan label
  was derived.

## Top 50 By Current Score

| Score Rank | File Row | Player | Pos | Team | Score | Confidence Cap | Confidence Status | Review Reason Labels | Warning Preview |
|---:|---:|---|---|---|---:|---:|---|---|---|
| 1 | 61 | Trey McBride | TE | ARI | 87.4776 | 0.88 | usable_with_confidence_cap | top_band_with_source_or_cap_warning, te_near_top_overall_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; ... |
| 2 | 1 | Puka Nacua | WR | LA | 83.0486 | 0.88 | usable_with_confidence_cap | top_band_with_source_or_cap_warning | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; ... |
| 3 | 2 | Jaxon Smith-Njigba | WR | SEA | 82.8713 | 0.88 | usable_with_confidence_cap | top_band_with_source_or_cap_warning | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; ... |
| 4 | 3 | Christian McCaffrey | RB | SF | 82.8329 | 0.88 | usable_with_confidence_cap | top_band_with_source_or_cap_warning, rb_age_window_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; rb_age_cliff_guardrail_active; ... |
| 5 | 62 | Josh Allen | QB | BUF | 80.3133 | 0.88 | usable_with_confidence_cap | top_band_with_source_or_cap_warning, one_qb_near_top_overall_review | qb_rushing_age_caution_active; missing_or_review_route_target_snap_evidence |
| 6 | 4 | Jonathan Taylor | RB | IND | 80.1465 | 0.88 | usable_with_confidence_cap | top_band_with_source_or_cap_warning, rb_age_window_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; rb_age_window_caution_active; ... |
| 7 | 5 | Bijan Robinson | RB | ATL | 79.9939 | 0.88 | usable_with_confidence_cap | top_band_with_source_or_cap_warning | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; ... |
| 8 | 6 | Ja'Marr Chase | WR | CIN | 74.1258 | 0.88 | usable_with_confidence_cap | top_band_with_source_or_cap_warning | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; ... |
| 9 | 7 | Jahmyr Gibbs | RB | DET | 73.9972 | 0.88 | usable_with_confidence_cap | top_band_with_source_or_cap_warning | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; ... |
| 10 | 8 | Amon-Ra St. Brown | WR | DET | 68.5918 | 0.82 | capped_review_required | top_band_with_source_or_cap_warning, capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; repeated_header_rows_removed=1; ... |
| 11 | 12 | De'Von Achane | RB | MIA | 66.6696 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; ... |
| 12 | 9 | Derrick Henry | RB | BAL | 66.2156 | 0.88 | usable_with_confidence_cap | rb_age_window_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; rb_age_cliff_guardrail_active; ... |
| 13 | 63 | Jalen Hurts | QB | PHI | 65.0980 | 0.88 | usable_with_confidence_cap | one_qb_near_top_overall_review | missing_or_review_route_target_snap_evidence |
| 14 | 11 | James Cook | RB | BUF | 63.7724 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; ... |
| 15 | 10 | George Pickens | WR | DAL | 62.9783 | 0.8 | capped_review_required | identity_team_review, capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; ... |
| 16 | 64 | Patrick Mahomes | QB | KC | 61.5482 | 1.0 | high_confidence_metadata | one_qb_near_top_overall_review | partial_first_down_confidence_cap; qb_rushing_age_caution_active |
| 17 | 13 | Kyren Williams | RB | LA | 61.1255 | 0.82 | capped_review_required | capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; repeated_header_rows_removed=1; ... |
| 18 | 14 | Saquon Barkley | RB | PHI | 60.8166 | 0.88 | usable_with_confidence_cap | rb_age_window_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; ... |
| 19 | 15 | Nico Collins | WR | HOU | 59.7382 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; ... |
| 20 | 16 | Chris Olave | WR | NO | 59.4933 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; ... |
| 21 | 17 | Josh Jacobs | RB | GB | 58.5387 | 0.88 | usable_with_confidence_cap | rb_age_window_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; ... |
| 22 | 18 | Chase Brown | RB | CIN | 58.2990 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; ... |
| 23 | 19 | Davante Adams | WR | LA | 57.5485 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; ... |
| 24 | 20 | Drake London | WR | ATL | 57.2578 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; ... |
| 25 | 65 | Travis Kelce | TE | KC | 57.1755 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; ... |
| 26 | 21 | CeeDee Lamb | WR | DAL | 56.2217 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; ... |
| 27 | 22 | Justin Jefferson | WR | MIN | 55.6738 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; ... |
| 28 | 23 | Breece Hall | RB | NYJ | 53.4482 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; ... |
| 29 | 66 | Brock Bowers | TE | LV | 50.0029 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; ... |
| 30 | 24 | Jaylen Waddle | WR | MIA | 48.2068 | 0.8 | capped_review_required | identity_team_review, capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; ... |
| 31 | 26 | Tee Higgins | WR | CIN | 45.5174 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; ... |
| 32 | 27 | Stefon Diggs | WR | NE | 45.2808 | 0.8 | capped_review_required | identity_team_review, capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; ... |
| 33 | 25 | Kenneth Walker III | RB | SEA | 44.6326 | 0.8 | capped_review_required | identity_team_review, capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; ... |
| 34 | 29 | Ashton Jeanty | RB | LV | 44.2641 | 0.82 | capped_review_required | low_evidence_review, capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; no_historical_evidence_for_component; ... |
| 35 | 28 | Wan'Dale Robinson | WR | TEN | 43.4188 | 0.8 | capped_review_required | identity_team_review, capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; ... |
| 36 | 30 | Keenan Allen | WR | LAC | 41.6097 | 0.8 | capped_review_required | identity_team_review, capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; ... |
| 37 | 67 | Jake Ferguson | TE | DAL | 41.1387 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; ... |
| 38 | 68 | Lamar Jackson | QB | BAL | 40.3535 | 1.0 | high_confidence_metadata | format_cap_review | one_qb_small_vorp_gap_cap; qb_rushing_age_caution_active |
| 39 | 34 | Terry McLaurin | WR | WAS | 39.3119 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; first_down_missing_confidence_cap; ... |
| 40 | 32 | Ladd McConkey | WR | LAC | 39.0177 | 0.82 | capped_review_required | capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; repeated_header_rows_removed=1; ... |
| 41 | 33 | Quentin Johnston | WR | LAC | 35.5788 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; first_down_missing_confidence_cap; ... |
| 42 | 31 | David Montgomery | RB | HOU | 35.0486 | 0.8 | capped_review_required | identity_team_review, rb_age_window_review, capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; ... |
| 43 | 36 | Brian Thomas Jr. | WR | JAX | 32.3993 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; ... |
| 44 | 37 | Marvin Harrison Jr. | WR | ARI | 32.3831 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; ... |
| 45 | 70 | George Kittle | TE | SF | 32.0994 | 0.88 | usable_with_confidence_cap | format_cap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; first_down_missing_confidence_cap; ... |
| 46 | 38 | Jakobi Meyers | WR | JAX | 31.5686 | 0.8 | capped_review_required | identity_team_review, capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; ... |
| 47 | 39 | Garrett Wilson | WR | NYJ | 31.5335 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; first_down_missing_confidence_cap; ... |
| 48 | 42 | Tyreek Hill | WR | MIA | 31.4237 | 0.8 | capped_review_required | identity_team_review, capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; repeated_header_rows_removed=1; ... |
| 49 | 44 | Luther Burden | WR | CHI | 31.3625 | 0.88 | usable_with_confidence_cap | low_evidence_review | missing_stats_first_component_evidence; missing_efficiency_context_evidence; partial_first_down_confidence_cap; ... |
| 50 | 35 | Romeo Doubs | WR | NE | 31.3334 | 0.8 | capped_review_required | identity_team_review, capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; ... |

## Bottom 50 By Current Score

| Score Rank | File Row | Player | Pos | Team | Score | Confidence Cap | Confidence Status | Review Reason Labels | Warning Preview |
|---:|---:|---|---|---|---:|---:|---|---|---|
| 31 | 26 | Tee Higgins | WR | CIN | 45.5174 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; ... |
| 32 | 27 | Stefon Diggs | WR | NE | 45.2808 | 0.8 | capped_review_required | identity_team_review, capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; ... |
| 33 | 25 | Kenneth Walker III | RB | SEA | 44.6326 | 0.8 | capped_review_required | identity_team_review, capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; ... |
| 34 | 29 | Ashton Jeanty | RB | LV | 44.2641 | 0.82 | capped_review_required | low_evidence_review, capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; no_historical_evidence_for_component; ... |
| 35 | 28 | Wan'Dale Robinson | WR | TEN | 43.4188 | 0.8 | capped_review_required | identity_team_review, capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; ... |
| 36 | 30 | Keenan Allen | WR | LAC | 41.6097 | 0.8 | capped_review_required | identity_team_review, capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; ... |
| 37 | 67 | Jake Ferguson | TE | DAL | 41.1387 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; ... |
| 38 | 68 | Lamar Jackson | QB | BAL | 40.3535 | 1.0 | high_confidence_metadata | format_cap_review | one_qb_small_vorp_gap_cap; qb_rushing_age_caution_active |
| 39 | 34 | Terry McLaurin | WR | WAS | 39.3119 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; first_down_missing_confidence_cap; ... |
| 40 | 32 | Ladd McConkey | WR | LAC | 39.0177 | 0.82 | capped_review_required | capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; repeated_header_rows_removed=1; ... |
| 41 | 33 | Quentin Johnston | WR | LAC | 35.5788 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; first_down_missing_confidence_cap; ... |
| 42 | 31 | David Montgomery | RB | HOU | 35.0486 | 0.8 | capped_review_required | identity_team_review, rb_age_window_review, capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; ... |
| 43 | 36 | Brian Thomas Jr. | WR | JAX | 32.3993 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; ... |
| 44 | 37 | Marvin Harrison Jr. | WR | ARI | 32.3831 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; ... |
| 45 | 70 | George Kittle | TE | SF | 32.0994 | 0.88 | usable_with_confidence_cap | format_cap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; first_down_missing_confidence_cap; ... |
| 46 | 38 | Jakobi Meyers | WR | JAX | 31.5686 | 0.8 | capped_review_required | identity_team_review, capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; ... |
| 47 | 39 | Garrett Wilson | WR | NYJ | 31.5335 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; first_down_missing_confidence_cap; ... |
| 48 | 42 | Tyreek Hill | WR | MIA | 31.4237 | 0.8 | capped_review_required | identity_team_review, capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; repeated_header_rows_removed=1; ... |
| 49 | 44 | Luther Burden | WR | CHI | 31.3625 | 0.88 | usable_with_confidence_cap | low_evidence_review | missing_stats_first_component_evidence; missing_efficiency_context_evidence; partial_first_down_confidence_cap; ... |
| 50 | 35 | Romeo Doubs | WR | NE | 31.3334 | 0.8 | capped_review_required | identity_team_review, capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; ... |
| 51 | 69 | Daniel Jones | QB | IND | 31.3120 | 0.8 | capped_review_required | identity_team_review, format_cap_review, capped_review_required | team_mismatch_or_missing_model_team; one_qb_small_vorp_gap_cap; identity_review_cap; ... |
| 52 | 41 | Jerry Jeudy | WR | CLE | 31.1199 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; first_down_missing_confidence_cap; ... |
| 53 | 46 | Malik Nabers | WR | NYG | 30.4824 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; ... |
| 54 | 48 | Hollywood Brown | WR | KC | 28.4834 | 0.88 | usable_with_confidence_cap | low_evidence_review | missing_stats_first_component_evidence; missing_efficiency_context_evidence; first_down_missing_confidence_cap; ... |
| 55 | 40 | Mike Evans | WR | TB | 28.4015 | 0.8 | capped_review_required | identity_team_review, capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; ... |
| 56 | 45 | Xavier Worthy | WR | KC | 27.9883 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; ... |
| 57 | 43 | Tank Dell | WR | HOU | 27.2878 | 0.82 | capped_review_required | capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; repeated_header_rows_removed=1; ... |
| 58 | 47 | Cooper Kupp | WR | SEA | 26.4622 | 0.8 | capped_review_required | identity_team_review, capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; ... |
| 59 | 51 | Ricky Pearsall | WR | SF | 25.9408 | 0.82 | capped_review_required | capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; repeated_header_rows_removed=1; ... |
| 60 | 53 | Brandon Aiyuk | WR | SF | 25.4061 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; ... |
| 61 | 50 | Jayden Higgins | WR | HOU | 25.2852 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; ... |
| 62 | 71 | Sam LaPorta | TE | DET | 24.2632 | 0.88 | usable_with_confidence_cap | format_cap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; no_premium_te_small_gap_cap; ... |
| 63 | 74 | Oronde Gadsden II | TE | LAC | 24.0072 | 0.88 | usable_with_confidence_cap | format_cap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; first_down_missing_confidence_cap; ... |
| 64 | 49 | Devin Singletary | RB | NYG | 23.9309 | 0.82 | capped_review_required | low_evidence_review, rb_age_window_review, capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; shifted_header_expected_player_header_inferred; ... |
| 65 | 72 | Brenton Strange | TE | JAX | 23.1507 | 0.88 | usable_with_confidence_cap | format_cap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; no_premium_te_small_gap_cap; ... |
| 66 | 73 | Mark Andrews | TE | BAL | 23.1327 | 0.88 | usable_with_confidence_cap | format_cap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; ... |
| 67 | 54 | Jalen Coker | WR | CAR | 22.2108 | 0.88 | usable_with_confidence_cap | routine_warning_readback | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; ... |
| 68 | 75 | Brock Purdy | QB | SF | 21.3779 | 0.88 | usable_with_confidence_cap | format_cap_review | one_qb_pocket_mid_qb_cap; missing_or_review_route_target_snap_evidence |
| 69 | 52 | Amari Cooper | WR | LV | 20.7072 | 0.8 | capped_review_required | identity_team_review, capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_historical_team; ... |
| 70 | 55 | Luke McCaffrey | WR | WAS | 16.2148 | 0.82 | capped_review_required | low_evidence_review, capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; shifted_header_expected_player_header_inferred; ... |
| 71 | 76 | T.J. Hockenson | TE | MIN | 13.7788 | 0.88 | usable_with_confidence_cap | low_score_boundary_review, format_cap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; first_down_missing_confidence_cap; ... |
| 72 | 77 | Joe Burrow | QB | CIN | 11.9641 | 0.88 | usable_with_confidence_cap | low_score_boundary_review, format_cap_review | one_qb_pocket_mid_qb_cap; missing_or_review_route_target_snap_evidence |
| 73 | 56 | Darrell Henderson | RB | LA | 9.6644 | 0.8 | capped_review_required | low_score_boundary_review, identity_team_review, rb_age_window_review, capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_historical_team; ... |
| 74 | 78 | Jayden Daniels | QB | WAS | 8.9902 | 1.0 | high_confidence_metadata | low_score_boundary_review, format_cap_review | one_qb_replacement_level_qb_cap |
| 75 | 57 | Kaleb Johnson | RB | PIT | 3.0698 | 0.82 | capped_review_required | low_score_boundary_review, low_evidence_review, capped_review_required | licensed_route_metrics_not_available; not_used_in_stats_first_value; no_historical_evidence_for_component; ... |
| 76 | 58 | Jeremiyah Love | RB | ARI | blank | 0.82 | capped_review_required | missing_primary_score_manual_review, low_evidence_review, capped_review_required | missing_rotowire_player_stats; missing_stats_first_component_evidence; missing_vorp_anchor; ... |
| 77 | 59 | Carnell Tate | WR | TEN | blank | 0.82 | capped_review_required | missing_primary_score_manual_review, low_evidence_review, capped_review_required | missing_rotowire_player_stats; missing_stats_first_component_evidence; missing_vorp_anchor; ... |
| 78 | 60 | Jordyn Tyson | WR | NOR | blank | 0.82 | capped_review_required | missing_primary_score_manual_review, low_evidence_review, capped_review_required | missing_rotowire_player_stats; missing_stats_first_component_evidence; missing_vorp_anchor; ... |
| 79 | 79 | Fernando Mendoza | QB | LVR | blank | 0.82 | capped_review_required | missing_primary_score_manual_review, low_evidence_review, format_cap_review, capped_review_required | missing_rotowire_player_stats; missing_stats_first_component_evidence; missing_vorp_anchor; ... |
| 80 | 80 | Kenyon Sadiq | TE | NYJ | blank | 0.82 | capped_review_required | missing_primary_score_manual_review, low_evidence_review, format_cap_review, capped_review_required | missing_rotowire_player_stats; missing_stats_first_component_evidence; missing_vorp_anchor; ... |

## Human Review Prompts

- `Trey McBride` appears as the highest numeric score overall. That is a
  no-premium TE context review prompt, not a conclusion.
- `Josh Allen`, `Jalen Hurts`, and `Patrick Mahomes` appear inside the top 20 by
  numeric score. That should be reviewed under the 1QB discipline task.
- `Joe Burrow` and `Jayden Daniels` appear in the bottom score band with explicit
  1QB cap warnings. That is a format-context prompt, not a recommendation.
- `Jeremiyah Love`, `Carnell Tate`, `Jordyn Tyson`, `Fernando Mendoza`, and
  `Kenyon Sadiq` have blank primary scores and must remain manual-review rows
  until their source gaps are resolved by the appropriate later task.
- `Keenan Allen` remains a current checkpoint row at `41.6097`; this report does
  not expose or use legacy active-pack `private_score` as primary value.

## Non-Goals

- Do not tune formulas from this scan.
- Do not change QB caps, TE caps, age curves, rookie priors, VORP, replacement
  formulas, confidence cap magnitudes, or startup-slot conversion.
- Do not use this table as a final ranking, roster recommendation, or default
  sort change.
- Do not add market, ADP, rankings, projections, consensus, startup, or
  trade-calculator data to private value.
