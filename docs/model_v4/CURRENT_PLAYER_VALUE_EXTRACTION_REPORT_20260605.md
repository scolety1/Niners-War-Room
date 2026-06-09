# Current-Player Value Extraction Report

Date: 2026-06-05

Mode: review-only refinement prep.

Purpose: extract current-player rows from the named audit roster into a
traceable review table before any formula work. This report is evidence only.
It does not tune formulas, change generated outputs, or make trade, cut, keep,
draft, buy, sell, defer, target, or start/sit recommendations.

## Source

- Source path:
  `local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv`
- Primary score column: `checkpoint_review_score`
- Rank/order basis: file order from the current-player checkpoint CSV.
- Allowed use: `review_only_current_value_checkpoint`
- Blocked use: `do_not_use_as_final_ranking_or_roster_recommendation`
- Checkpoint version:
  `model_v4_phase_11g_current_value_checkpoint_0.1.0`

## Scope

- Named audit roster source:
  `docs/model_v4/NAMED_PLAYER_AUDIT_ROSTER_20260605.md`
- Current-player roster subjects found in the checkpoint: 68.
- Non-current roster subjects intentionally excluded from this report: 12
  rookie/pick rows. Those belong to later rookie and pick-ladder tasks.
- Missing current-player roster subjects: none.

## Manual-Review Flag Derivation

The `Manual Review Flags` column is derived only from exported warning text. It
is a reporting aid, not a model input and not a formula change.

- `source_gap_review`: warning text includes missing, partial, no-historical, or
  source-review evidence language.
- `status_review`: warning text includes team mismatch, historical team,
  identity review, injury, or status-like join caution.
- `age_window_review`: warning text includes RB age-window or age-cliff
  guardrails.
- `format_cap_review`: warning text includes 1QB or no-premium-TE format caps.
- `none_from_warning_flags`: no derived manual-review flag from exported
  warning text.

## Extracted Current-Player Rows

| ID | Player | Pos | CSV Rank | Checkpoint Review Score | Confidence Cap | Confidence Status | Component Weight | Warning Flags | Manual Review Flags |
|---|---|---:|---:|---:|---:|---|---:|---|---|
| A01 | Puka Nacua | WR | 1 | 83.0486 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A02 | Jaxon Smith-Njigba | WR | 2 | 82.8713 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A03 | Ja'Marr Chase | WR | 6 | 74.1258 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A04 | Amon-Ra St. Brown | WR | 8 | 68.5918 | 0.82 | capped_review_required | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; repeated_header_rows_removed=1; partial_first_down_confidence_cap; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A05 | CeeDee Lamb | WR | 21 | 56.2217 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A06 | Justin Jefferson | WR | 22 | 55.6738 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A07 | Nico Collins | WR | 15 | 59.7382 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A08 | Chris Olave | WR | 16 | 59.4933 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A09 | Drake London | WR | 20 | 57.2578 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A10 | George Pickens | WR | 10 | 62.9783 | 0.8 | capped_review_required | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; missing_or_review_route_target_snap_evidence; identity_review_cap; partial_or_quarantined_join_cap; missing_lifecycle_or_role_shape_evidence | source_gap_review, status_review |
| A11 | Jaylen Waddle | WR | 24 | 48.2068 | 0.8 | capped_review_required | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; missing_or_review_route_target_snap_evidence; identity_review_cap; partial_or_quarantined_join_cap; missing_lifecycle_or_role_shape_evidence | source_gap_review, status_review |
| A12 | Tee Higgins | WR | 26 | 45.5174 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A13 | Brian Thomas Jr. | WR | 36 | 32.3993 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A14 | Marvin Harrison Jr. | WR | 37 | 32.3831 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A15 | Malik Nabers | WR | 46 | 30.4824 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A16 | Xavier Worthy | WR | 45 | 27.9883 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A17 | Ladd McConkey | WR | 32 | 39.0177 | 0.82 | capped_review_required | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; repeated_header_rows_removed=1; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A18 | Ricky Pearsall | WR | 51 | 25.9408 | 0.82 | capped_review_required | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; repeated_header_rows_removed=1; first_down_missing_confidence_cap; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A19 | Brandon Aiyuk | WR | 53 | 25.4061 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A20 | Quentin Johnston | WR | 33 | 35.5788 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; first_down_missing_confidence_cap; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A21 | Christian McCaffrey | RB | 3 | 82.8329 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; rb_age_cliff_guardrail_active; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | age_window_review, source_gap_review |
| A22 | Jonathan Taylor | RB | 4 | 80.1465 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; rb_age_window_caution_active; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | age_window_review, source_gap_review |
| A23 | Bijan Robinson | RB | 5 | 79.9939 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A24 | Jahmyr Gibbs | RB | 7 | 73.9972 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A25 | Derrick Henry | RB | 9 | 66.2156 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; rb_age_cliff_guardrail_active; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | age_window_review, source_gap_review |
| A26 | De'Von Achane | RB | 12 | 66.6696 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A27 | James Cook | RB | 11 | 63.7724 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A28 | Kyren Williams | RB | 13 | 61.1255 | 0.82 | capped_review_required | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; repeated_header_rows_removed=1; partial_first_down_confidence_cap; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A29 | Saquon Barkley | RB | 14 | 60.8166 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; rb_age_cliff_guardrail_active; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | age_window_review, source_gap_review |
| A30 | Josh Jacobs | RB | 17 | 58.5387 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; rb_age_window_caution_active; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | age_window_review, source_gap_review |
| A31 | Breece Hall | RB | 23 | 53.4482 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A32 | Kenneth Walker III | RB | 25 | 44.6326 | 0.8 | capped_review_required | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; missing_or_review_route_target_snap_evidence; identity_review_cap; partial_or_quarantined_join_cap; missing_lifecycle_or_role_shape_evidence | source_gap_review, status_review |
| A33 | Chase Brown | RB | 18 | 58.2990 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A34 | David Montgomery | RB | 31 | 35.0486 | 0.8 | capped_review_required | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; rb_age_cliff_guardrail_active; missing_or_review_route_target_snap_evidence; identity_review_cap; partial_or_quarantined_join_cap; missing_lifecycle_or_role_shape_evidence | age_window_review, source_gap_review, status_review |
| A35 | Ashton Jeanty | RB | 29 | 44.2641 | 0.82 | capped_review_required | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; no_historical_evidence_for_component; partial_first_down_confidence_cap; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A36 | Kaleb Johnson | RB | 57 | 3.0698 | 0.82 | capped_review_required | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; no_historical_evidence_for_component; shifted_header_expected_player_header_inferred; partial_first_down_confidence_cap; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A37 | Davante Adams | WR | 19 | 57.5485 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A38 | Stefon Diggs | WR | 27 | 45.2808 | 0.8 | capped_review_required | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; missing_or_review_route_target_snap_evidence; identity_review_cap; partial_or_quarantined_join_cap; missing_lifecycle_or_role_shape_evidence | source_gap_review, status_review |
| A39 | Mike Evans | WR | 40 | 28.4015 | 0.8 | capped_review_required | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; missing_or_review_route_target_snap_evidence; identity_review_cap; partial_or_quarantined_join_cap; missing_lifecycle_or_role_shape_evidence | source_gap_review, status_review |
| A40 | Cooper Kupp | WR | 47 | 26.4622 | 0.8 | capped_review_required | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; first_down_missing_confidence_cap; missing_or_review_route_target_snap_evidence; identity_review_cap; partial_or_quarantined_join_cap; missing_lifecycle_or_role_shape_evidence | source_gap_review, status_review |
| A41 | Amari Cooper | WR | 52 | 20.7072 | 0.8 | capped_review_required | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_historical_team; first_down_missing_confidence_cap; missing_or_review_first_down_evidence; missing_or_review_route_target_snap_evidence; identity_review_cap; partial_or_quarantined_join_cap; missing_lifecycle_or_role_shape_evidence | source_gap_review, status_review |
| A42 | Tyreek Hill | WR | 42 | 31.4237 | 0.8 | capped_review_required | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; repeated_header_rows_removed=1; team_mismatch_or_historical_team; missing_or_review_route_target_snap_evidence; identity_review_cap; partial_or_quarantined_join_cap; missing_lifecycle_or_role_shape_evidence | source_gap_review, status_review |
| A43 | Keenan Allen | WR | 30 | 41.6097 | 0.8 | capped_review_required | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; missing_or_review_route_target_snap_evidence; identity_review_cap; partial_or_quarantined_join_cap; missing_lifecycle_or_role_shape_evidence | source_gap_review, status_review |
| A44 | Wan'Dale Robinson | WR | 28 | 43.4188 | 0.8 | capped_review_required | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; partial_first_down_confidence_cap; missing_or_review_route_target_snap_evidence; identity_review_cap; partial_or_quarantined_join_cap; missing_lifecycle_or_role_shape_evidence | source_gap_review, status_review |
| A45 | Romeo Doubs | WR | 35 | 31.3334 | 0.8 | capped_review_required | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; first_down_missing_confidence_cap; missing_or_review_route_target_snap_evidence; identity_review_cap; partial_or_quarantined_join_cap; missing_lifecycle_or_role_shape_evidence | source_gap_review, status_review |
| A46 | Jerry Jeudy | WR | 41 | 31.1199 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; first_down_missing_confidence_cap; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A47 | Garrett Wilson | WR | 39 | 31.5335 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; first_down_missing_confidence_cap; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A48 | Tank Dell | WR | 43 | 27.2878 | 0.82 | capped_review_required | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; repeated_header_rows_removed=1; partial_first_down_confidence_cap; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A49 | Luther Burden | WR | 44 | 31.3625 | 0.88 | usable_with_confidence_cap | 0.95 | missing_stats_first_component_evidence; missing_efficiency_context_evidence; partial_first_down_confidence_cap; missing_stats_first_confidence_cap; missing_or_review_first_down_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A50 | Jayden Higgins | WR | 50 | 25.2852 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A51 | Jalen Coker | WR | 54 | 22.2108 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A52 | Luke McCaffrey | WR | 55 | 16.2148 | 0.82 | capped_review_required | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; shifted_header_expected_player_header_inferred; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A53 | Hollywood Brown | WR | 48 | 28.4834 | 0.88 | usable_with_confidence_cap | 0.95 | missing_stats_first_component_evidence; missing_efficiency_context_evidence; first_down_missing_confidence_cap; missing_stats_first_confidence_cap; missing_or_review_first_down_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A54 | Devin Singletary | RB | 49 | 23.9309 | 0.82 | capped_review_required | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; shifted_header_expected_player_header_inferred; rb_age_window_caution_active; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | age_window_review, source_gap_review |
| A55 | Darrell Henderson | RB | 56 | 9.6644 | 0.8 | capped_review_required | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_historical_team; first_down_missing_confidence_cap; rb_age_cliff_guardrail_active; missing_or_review_first_down_evidence; missing_or_review_route_target_snap_evidence; identity_review_cap; partial_or_quarantined_join_cap; missing_lifecycle_or_role_shape_evidence | age_window_review, source_gap_review, status_review |
| A56 | Josh Allen | QB | 62 | 80.3133 | 0.88 | usable_with_confidence_cap | 1.0 | qb_rushing_age_caution_active; missing_or_review_route_target_snap_evidence | source_gap_review |
| A57 | Jalen Hurts | QB | 63 | 65.0980 | 0.88 | usable_with_confidence_cap | 1.0 | missing_or_review_route_target_snap_evidence | source_gap_review |
| A58 | Patrick Mahomes | QB | 64 | 61.5482 | 1.0 | high_confidence_metadata | 1.0 | partial_first_down_confidence_cap; qb_rushing_age_caution_active | source_gap_review |
| A59 | Lamar Jackson | QB | 68 | 40.3535 | 1.0 | high_confidence_metadata | 1.0 | one_qb_small_vorp_gap_cap; qb_rushing_age_caution_active | format_cap_review |
| A60 | Joe Burrow | QB | 77 | 11.9641 | 0.88 | usable_with_confidence_cap | 1.0 | one_qb_pocket_mid_qb_cap; missing_or_review_route_target_snap_evidence | format_cap_review, source_gap_review |
| A61 | Jayden Daniels | QB | 78 | 8.9902 | 1.0 | high_confidence_metadata | 1.0 | one_qb_replacement_level_qb_cap | format_cap_review |
| A62 | Trey McBride | TE | 61 | 87.4776 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A63 | Travis Kelce | TE | 65 | 57.1755 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A64 | Brock Bowers | TE | 66 | 50.0029 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A65 | Jake Ferguson | TE | 67 | 41.1387 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | source_gap_review |
| A66 | George Kittle | TE | 70 | 32.0994 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; first_down_missing_confidence_cap; no_premium_te_small_gap_cap; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | format_cap_review, source_gap_review |
| A67 | Sam LaPorta | TE | 71 | 24.2632 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; no_premium_te_small_gap_cap; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | format_cap_review, source_gap_review |
| A68 | Mark Andrews | TE | 73 | 23.1327 | 0.88 | usable_with_confidence_cap | 1.0 | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; no_premium_te_small_gap_cap; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | format_cap_review, source_gap_review |

## Excluded Roster Subjects For Later Tasks

These named audit roster subjects are not current-player checkpoint rows and are
intentionally reserved for rookie-board and pick-ladder extraction tasks:

- A69 Jeremiyah Love
- A70 Makai Lemon
- A71 Skyler Bell
- A72 Jordyn Tyson
- A73 Carnell Tate
- A74 Antonio Williams
- A75 Daniel Sobkowicz
- A76 2026 1.03
- A77 2026 1.04
- A78 2026 2.04
- A79 2026 2.08
- A80 2026 5.04

## Early Human-Review Notes

- `Trey McBride` is the highest extracted checkpoint score in this current
  report and should be audited in the no-premium TE discipline task.
- `Christian McCaffrey`, `Derrick Henry`, `Saquon Barkley`, `Josh Jacobs`,
  `David Montgomery`, `Devin Singletary`, and `Darrell Henderson` expose RB age
  guardrail warnings for the later veteran age-window audit.
- `Keenan Allen` appears with current checkpoint score `41.6097`; this report
  does not expose or use the legacy active-pack `private_score` sentinel value
  as a primary score.
- `Kaleb Johnson` appears with current checkpoint score `3.0698` and
  no-historical/source-gap warnings, making him a later roster-pressure and
  low-evidence review row.

## Non-Goals

- Do not treat this table as a final ranking.
- Do not use this table as a roster recommendation.
- Do not add market, ADP, rankings, projections, consensus, startup, or
  trade-calculator data to private value.
- Do not tune formulas from this report.
