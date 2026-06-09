# Young-Player Evidence Audit

Date: 2026-06-05

Mode: review-only refinement prep.

Purpose: review young-player, rookie-current-bridge, volatile-profile, and
low-evidence current-player rows before any formula work. This report is
evidence only. It does not change young-player priors, rookie weights, model
weights, VORP, replacement formulas, confidence caps, generated outputs, active
rankings, app state, or recommendation logic.

## Sources

- Current-player source:
  `local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv`
- Score column: `checkpoint_review_score`
- Lineage: `review_v4_current_player`
- Audit roster source:
  `docs/model_v4/NAMED_PLAYER_AUDIT_ROSTER_20260605.md`
- Allowed use: `review_only_current_value_checkpoint`
- Blocked use: `do_not_use_as_final_ranking_or_roster_recommendation`

This audit uses exported warning flags and named audit-roster categories. It
does not import external rankings, projections, ADP, market, startup, consensus,
or trade-calculator data.

## Scope Counts

- Named current-player young/volatile/low-evidence rows from audit roster: 27.
- Additional exported low-evidence rows outside those roster categories: 8.
- Total rows reviewed here: 35.
- Rows with score at least 50: 9.
- Rows with `capped_review_required`: 13.
- Rows with exported low-evidence warning text: 11.
- Rows with blank primary score: 5.

## Classification Labels

- `high_score_young_review`: score is at least 50 on a named young or volatile
  current-player row.
- `limited_history_or_stats_first_gap`: exported warning text includes
  no-historical, missing stats-first, or missing VORP anchor language.
- `source_shape_review`: exported warning text includes shifted-header language.
- `identity_or_team_review`: exported warning text includes team mismatch,
  historical team, or identity-review language.
- `confidence_capped`: `confidence_status` is `capped_review_required`.
- `first_down_evidence_gap`: exported warning text includes partial or missing
  first-down evidence.
- `role_lifecycle_evidence_gap`: exported warning text includes route, target,
  snap, role, or lifecycle review language.
- `missing_primary_score_manual_review`: blank primary score.
- `bottom_score_low_evidence_review`: numeric score below 15 with low-evidence
  context.

## Reviewed Young/Evidence Rows

| Audit ID | File Row | Player | Pos | Team | Score | Score Band | Confidence Cap | Confidence Status | Audit Category | Classification | Warning Preview |
|---|---:|---|---|---|---:|---|---:|---|---|---|---|
| A01 | 1 | Puka Nacua | WR | LA | 83.0486 | top_70_plus | 0.88 | usable_with_confidence_cap | elite_young_wr | high_score_young_review, role_lifecycle_evidence_gap | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence |
| A02 | 2 | Jaxon Smith-Njigba | WR | SEA | 82.8713 | top_70_plus | 0.88 | usable_with_confidence_cap | elite_young_wr | high_score_young_review, role_lifecycle_evidence_gap | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence |
| A08 | 16 | Chris Olave | WR | NO | 59.4933 | high_50_69 | 0.88 | usable_with_confidence_cap | young_wr_warning | high_score_young_review, first_down_evidence_gap, role_lifecycle_evidence_gap | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; missing_or_review_route_target_snap_evidence; ... |
| A09 | 20 | Drake London | WR | ATL | 57.2578 | high_50_69 | 0.88 | usable_with_confidence_cap | young_wr_warning | high_score_young_review, role_lifecycle_evidence_gap | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence |
| A11 | 24 | Jaylen Waddle | WR | MIA | 48.2068 | middle_30_49 | 0.8 | capped_review_required | young_wr_warning | identity_or_team_review, confidence_capped, role_lifecycle_evidence_gap | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; missing_or_review_route_target_snap_evidence; ... |
| A12 | 26 | Tee Higgins | WR | CIN | 45.5174 | middle_30_49 | 0.88 | usable_with_confidence_cap | young_wr_warning | role_lifecycle_evidence_gap | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence |
| A13 | 36 | Brian Thomas Jr. | WR | JAX | 32.3993 | middle_30_49 | 0.88 | usable_with_confidence_cap | young_wr_warning | first_down_evidence_gap, role_lifecycle_evidence_gap | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; missing_or_review_route_target_snap_evidence; ... |
| A14 | 37 | Marvin Harrison Jr. | WR | ARI | 32.3831 | middle_30_49 | 0.88 | usable_with_confidence_cap | young_wr_warning | role_lifecycle_evidence_gap | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence |
| A15 | 46 | Malik Nabers | WR | NYG | 30.4824 | middle_30_49 | 0.88 | usable_with_confidence_cap | young_wr_warning | role_lifecycle_evidence_gap | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence |
| A16 | 45 | Xavier Worthy | WR | KC | 27.9883 | low_15_29 | 0.88 | usable_with_confidence_cap | young_wr_warning | role_lifecycle_evidence_gap | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence |
| A17 | 32 | Ladd McConkey | WR | LAC | 39.0177 | middle_30_49 | 0.82 | capped_review_required | young_wr_warning | confidence_capped, role_lifecycle_evidence_gap | licensed_route_metrics_not_available; not_used_in_stats_first_value; repeated_header_rows_removed=1; missing_or_review_route_target_snap_evidence; ... |
| A18 | 51 | Ricky Pearsall | WR | SF | 25.9408 | low_15_29 | 0.82 | capped_review_required | roster_relevance | confidence_capped, first_down_evidence_gap, role_lifecycle_evidence_gap | licensed_route_metrics_not_available; not_used_in_stats_first_value; repeated_header_rows_removed=1; first_down_missing_confidence_cap; ... |
| A19 | 53 | Brandon Aiyuk | WR | SF | 25.4061 | low_15_29 | 0.88 | usable_with_confidence_cap | roster_relevance | role_lifecycle_evidence_gap | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence |
| A20 | 33 | Quentin Johnston | WR | LAC | 35.5788 | middle_30_49 | 0.88 | usable_with_confidence_cap | volatile_profile | first_down_evidence_gap, role_lifecycle_evidence_gap | licensed_route_metrics_not_available; not_used_in_stats_first_value; first_down_missing_confidence_cap; missing_or_review_route_target_snap_evidence; ... |
| A23 | 5 | Bijan Robinson | RB | ATL | 79.9939 | top_70_plus | 0.88 | usable_with_confidence_cap | elite_young_rb | high_score_young_review, role_lifecycle_evidence_gap | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence |
| A24 | 7 | Jahmyr Gibbs | RB | DET | 73.9972 | top_70_plus | 0.88 | usable_with_confidence_cap | elite_young_rb | high_score_young_review, role_lifecycle_evidence_gap | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence |
| A26 | 12 | De'Von Achane | RB | MIA | 66.6696 | high_50_69 | 0.88 | usable_with_confidence_cap | volatile_rb | high_score_young_review, role_lifecycle_evidence_gap | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence |
| A31 | 23 | Breece Hall | RB | NYJ | 53.4482 | high_50_69 | 0.88 | usable_with_confidence_cap | young_rb_warning | high_score_young_review, first_down_evidence_gap, role_lifecycle_evidence_gap | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; missing_or_review_route_target_snap_evidence; ... |
| A32 | 25 | Kenneth Walker III | RB | SEA | 44.6326 | middle_30_49 | 0.8 | capped_review_required | young_rb_warning | identity_or_team_review, confidence_capped, role_lifecycle_evidence_gap | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; missing_or_review_route_target_snap_evidence; ... |
| A33 | 18 | Chase Brown | RB | CIN | 58.2990 | high_50_69 | 0.88 | usable_with_confidence_cap | emerging_rb | high_score_young_review, role_lifecycle_evidence_gap | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence |
| A35 | 29 | Ashton Jeanty | RB | LV | 44.2641 | middle_30_49 | 0.82 | capped_review_required | rookie_current_bridge | limited_history_or_stats_first_gap, confidence_capped, first_down_evidence_gap, role_lifecycle_evidence_gap | licensed_route_metrics_not_available; not_used_in_stats_first_value; no_historical_evidence_for_component; partial_first_down_confidence_cap; ... |
| A46 | 41 | Jerry Jeudy | WR | CLE | 31.1199 | middle_30_49 | 0.88 | usable_with_confidence_cap | volatile_profile | first_down_evidence_gap, role_lifecycle_evidence_gap | licensed_route_metrics_not_available; not_used_in_stats_first_value; first_down_missing_confidence_cap; missing_or_review_route_target_snap_evidence; ... |
| A47 | 39 | Garrett Wilson | WR | NYJ | 31.5335 | middle_30_49 | 0.88 | usable_with_confidence_cap | suspicious_ranking | first_down_evidence_gap, role_lifecycle_evidence_gap | licensed_route_metrics_not_available; not_used_in_stats_first_value; first_down_missing_confidence_cap; missing_or_review_route_target_snap_evidence; ... |
| A49 | 44 | Luther Burden | WR | CHI | 31.3625 | middle_30_49 | 0.88 | usable_with_confidence_cap | low_evidence | limited_history_or_stats_first_gap, first_down_evidence_gap, role_lifecycle_evidence_gap | missing_stats_first_component_evidence; missing_efficiency_context_evidence; partial_first_down_confidence_cap; missing_stats_first_confidence_cap; ... |
| A50 | 50 | Jayden Higgins | WR | HOU | 25.2852 | low_15_29 | 0.88 | usable_with_confidence_cap | low_evidence | role_lifecycle_evidence_gap | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence |
| A51 | 54 | Jalen Coker | WR | CAR | 22.2108 | low_15_29 | 0.88 | usable_with_confidence_cap | low_evidence | role_lifecycle_evidence_gap | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence |
| A52 | 55 | Luke McCaffrey | WR | WAS | 16.2148 | low_15_29 | 0.82 | capped_review_required | low_evidence | source_shape_review, confidence_capped, role_lifecycle_evidence_gap | licensed_route_metrics_not_available; not_used_in_stats_first_value; shifted_header_expected_player_header_inferred; missing_or_review_route_target_snap_evidence; ... |
| WARN | 48 | Hollywood Brown | WR | KC | 28.4834 | low_15_29 | 0.88 | usable_with_confidence_cap | exported_low_evidence_warning | limited_history_or_stats_first_gap, first_down_evidence_gap, role_lifecycle_evidence_gap | missing_stats_first_component_evidence; missing_efficiency_context_evidence; first_down_missing_confidence_cap; missing_stats_first_confidence_cap; ... |
| WARN | 49 | Devin Singletary | RB | NYG | 23.9309 | low_15_29 | 0.82 | capped_review_required | exported_low_evidence_warning | source_shape_review, confidence_capped, role_lifecycle_evidence_gap | licensed_route_metrics_not_available; not_used_in_stats_first_value; shifted_header_expected_player_header_inferred; rb_age_window_caution_active; ... |
| WARN | 57 | Kaleb Johnson | RB | PIT | 3.0698 | bottom_under_15 | 0.82 | capped_review_required | exported_low_evidence_warning | limited_history_or_stats_first_gap, source_shape_review, confidence_capped, first_down_evidence_gap, role_lifecycle_evidence_gap, bottom_score_low_evidence_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; no_historical_evidence_for_component; shifted_header_expected_player_header_inferred; ... |
| WARN | 58 | Jeremiyah Love | RB | ARI | blank | blank | 0.82 | capped_review_required | exported_low_evidence_warning | missing_primary_score_manual_review, limited_history_or_stats_first_gap, confidence_capped, role_lifecycle_evidence_gap | missing_rotowire_player_stats; missing_stats_first_component_evidence; missing_vorp_anchor; missing_role_volume_evidence; ... |
| WARN | 59 | Carnell Tate | WR | TEN | blank | blank | 0.82 | capped_review_required | exported_low_evidence_warning | missing_primary_score_manual_review, limited_history_or_stats_first_gap, confidence_capped, role_lifecycle_evidence_gap | missing_rotowire_player_stats; missing_stats_first_component_evidence; missing_vorp_anchor; missing_target_route_role_evidence; ... |
| WARN | 60 | Jordyn Tyson | WR | NOR | blank | blank | 0.82 | capped_review_required | exported_low_evidence_warning | missing_primary_score_manual_review, limited_history_or_stats_first_gap, confidence_capped, role_lifecycle_evidence_gap | missing_rotowire_player_stats; missing_stats_first_component_evidence; missing_vorp_anchor; missing_target_route_role_evidence; ... |
| WARN | 79 | Fernando Mendoza | QB | LVR | blank | blank | 0.82 | capped_review_required | exported_low_evidence_warning | missing_primary_score_manual_review, limited_history_or_stats_first_gap, confidence_capped, role_lifecycle_evidence_gap | missing_rotowire_player_stats; missing_stats_first_component_evidence; missing_vorp_anchor; missing_qb_rushing_separation_evidence; ... |
| WARN | 80 | Kenyon Sadiq | TE | NYJ | blank | blank | 0.82 | capped_review_required | exported_low_evidence_warning | missing_primary_score_manual_review, limited_history_or_stats_first_gap, confidence_capped, role_lifecycle_evidence_gap | missing_rotowire_player_stats; missing_stats_first_component_evidence; missing_vorp_anchor; missing_te_route_target_role_evidence; ... |

## Review Observations

- High-score young review rows include `Puka Nacua`, `Jaxon Smith-Njigba`,
  `Bijan Robinson`, `Jahmyr Gibbs`, `De'Von Achane`, `Chris Olave`,
  `Drake London`, `Breece Hall`, and `Chase Brown`.
- Every high-score young row still carries role, lifecycle, route, target, snap,
  or source-review language. That is a presentation and human-review prompt, not
  a formula verdict.
- `Ashton Jeanty`, `Luther Burden`, `Hollywood Brown`, `Kaleb Johnson`,
  `Jeremiyah Love`, `Carnell Tate`, `Jordyn Tyson`, `Fernando Mendoza`, and
  `Kenyon Sadiq` expose limited-history, missing stats-first, missing VORP, or
  blank-score evidence gaps.
- `Jeremiyah Love`, `Carnell Tate`, `Jordyn Tyson`, `Fernando Mendoza`, and
  `Kenyon Sadiq` have blank primary scores and must remain manual-review rows.
- `Garrett Wilson`, `Malik Nabers`, `Brian Thomas Jr.`, and `Marvin Harrison Jr.`
  are named young WR sanity rows where the human reviewer should compare the
  model score to their football prior before any formula proposal.

## Non-Goals

- Do not change young-player priors from this report.
- Do not change rookie weights, model weights, VORP, replacement formulas,
  confidence caps, pick baselines, age curves, or startup-slot conversion.
- Do not add market, ADP, rankings, projections, consensus, startup, or
  trade-calculator logic to private value.
- Do not convert any review label into a trade, cut, keep, draft, buy, sell,
  defer, target, or start/sit recommendation.
