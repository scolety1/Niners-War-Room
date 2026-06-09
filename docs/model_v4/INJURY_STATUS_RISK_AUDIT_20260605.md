# Injury/Status Risk Audit

Date: 2026-06-05

Mode: review-only refinement prep.

Purpose: identify current-player rows where injury/status, stale-team,
identity-join, or source-status context should be visible before any formula
work. This report is evidence only. It does not change injury penalties, model
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

This audit uses exported warning flags plus named audit-roster categories such
as `injury_status`, `volatile_profile`, and veteran/status review groups. It
does not import injury feeds, projections, ADP, market, startup, consensus, or
trade-calculator data.

## Scope Counts

- Rows reviewed here: 30.
- Rows with `capped_review_required`: 17.
- Rows with team, historical-team, or identity-review warning text: 15.
- Rows with `partial_or_quarantined_join_cap`: 15.
- Rows selected from injury/status/volatile roster categories: 5.

## Classification Labels

- `missing_or_mismatched_team`: exported warning text includes
  `team_mismatch_or_missing_model_team`.
- `historical_team_context`: exported warning text includes
  `team_mismatch_or_historical_team`.
- `identity_review_cap`: exported warning text includes `identity_review_cap`.
- `partial_or_quarantined_join`: exported warning text includes
  `partial_or_quarantined_join_cap`.
- `roster_category_status_prompt`: audit-roster category marks the player as an
  injury/status or volatile-profile review row.
- `confidence_capped`: `confidence_status` is `capped_review_required`.
- `first_down_source_gap`: exported warning text includes partial or missing
  first-down evidence.
- `route_target_snap_review`: exported warning text includes route, target, or
  snap review language.

## Reviewed Status-Risk Rows

| Audit ID | File Row | Player | Pos | Team | Score | Score Band | Confidence Cap | Confidence Status | Audit Category | Classification | Warning Preview |
|---|---:|---|---|---|---:|---|---:|---|---|---|---|
| A10 | 10 | George Pickens | WR | DAL | 62.9783 | high_50_69 | 0.8 | capped_review_required | warning_sentinel | missing_or_mismatched_team, identity_review_cap, partial_or_quarantined_join, confidence_capped, route_target_snap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; missing_or_review_route_target_snap_evidence; ... |
| A26 | 12 | De'Von Achane | RB | MIA | 66.6696 | high_50_69 | 0.88 | usable_with_confidence_cap | volatile_rb | roster_category_status_prompt, route_target_snap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence |
| A08 | 16 | Chris Olave | WR | NO | 59.4933 | high_50_69 | 0.88 | usable_with_confidence_cap | young_wr_warning | first_down_source_gap, route_target_snap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; missing_or_review_route_target_snap_evidence; ... |
| A37 | 19 | Davante Adams | WR | LA | 57.5485 | high_50_69 | 0.88 | usable_with_confidence_cap | aging_wr | route_target_snap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence |
| A09 | 20 | Drake London | WR | ATL | 57.2578 | high_50_69 | 0.88 | usable_with_confidence_cap | young_wr_warning | route_target_snap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence |
| A31 | 23 | Breece Hall | RB | NYJ | 53.4482 | high_50_69 | 0.88 | usable_with_confidence_cap | young_rb_warning | first_down_source_gap, route_target_snap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; missing_or_review_route_target_snap_evidence; ... |
| A11 | 24 | Jaylen Waddle | WR | MIA | 48.2068 | middle_30_49 | 0.8 | capped_review_required | young_wr_warning | missing_or_mismatched_team, identity_review_cap, partial_or_quarantined_join, confidence_capped, route_target_snap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; missing_or_review_route_target_snap_evidence; ... |
| A32 | 25 | Kenneth Walker III | RB | SEA | 44.6326 | middle_30_49 | 0.8 | capped_review_required | young_rb_warning | missing_or_mismatched_team, identity_review_cap, partial_or_quarantined_join, confidence_capped, route_target_snap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; missing_or_review_route_target_snap_evidence; ... |
| A12 | 26 | Tee Higgins | WR | CIN | 45.5174 | middle_30_49 | 0.88 | usable_with_confidence_cap | young_wr_warning | route_target_snap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence |
| A38 | 27 | Stefon Diggs | WR | NE | 45.2808 | middle_30_49 | 0.8 | capped_review_required | aging_wr | missing_or_mismatched_team, identity_review_cap, partial_or_quarantined_join, confidence_capped, route_target_snap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; missing_or_review_route_target_snap_evidence; ... |
| A44 | 28 | Wan'Dale Robinson | WR | TEN | 43.4188 | middle_30_49 | 0.8 | capped_review_required | low_band_wr | missing_or_mismatched_team, identity_review_cap, partial_or_quarantined_join, confidence_capped, first_down_source_gap, route_target_snap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; partial_first_down_confidence_cap; ... |
| A43 | 30 | Keenan Allen | WR | LAC | 41.6097 | middle_30_49 | 0.8 | capped_review_required | legacy_leak_sentinel | missing_or_mismatched_team, identity_review_cap, partial_or_quarantined_join, confidence_capped, route_target_snap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; missing_or_review_route_target_snap_evidence; ... |
| A34 | 31 | David Montgomery | RB | HOU | 35.0486 | middle_30_49 | 0.8 | capped_review_required | veteran_depth_rb | missing_or_mismatched_team, identity_review_cap, partial_or_quarantined_join, confidence_capped, route_target_snap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; rb_age_cliff_guardrail_active; ... |
| A17 | 32 | Ladd McConkey | WR | LAC | 39.0177 | middle_30_49 | 0.82 | capped_review_required | young_wr_warning | confidence_capped, route_target_snap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; repeated_header_rows_removed=1; missing_or_review_route_target_snap_evidence; ... |
| A20 | 33 | Quentin Johnston | WR | LAC | 35.5788 | middle_30_49 | 0.88 | usable_with_confidence_cap | volatile_profile | roster_category_status_prompt, first_down_source_gap, route_target_snap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; first_down_missing_confidence_cap; missing_or_review_route_target_snap_evidence; ... |
| A45 | 35 | Romeo Doubs | WR | NE | 31.3334 | middle_30_49 | 0.8 | capped_review_required | low_band_wr | missing_or_mismatched_team, identity_review_cap, partial_or_quarantined_join, confidence_capped, first_down_source_gap, route_target_snap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; first_down_missing_confidence_cap; ... |
| A13 | 36 | Brian Thomas Jr. | WR | JAX | 32.3993 | middle_30_49 | 0.88 | usable_with_confidence_cap | young_wr_warning | first_down_source_gap, route_target_snap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; missing_or_review_route_target_snap_evidence; ... |
| A14 | 37 | Marvin Harrison Jr. | WR | ARI | 32.3831 | middle_30_49 | 0.88 | usable_with_confidence_cap | young_wr_warning | route_target_snap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence |
| WARN | 38 | Jakobi Meyers | WR | JAX | 31.5686 | middle_30_49 | 0.8 | capped_review_required | exported_status_warning | missing_or_mismatched_team, identity_review_cap, partial_or_quarantined_join, confidence_capped, first_down_source_gap, route_target_snap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; first_down_missing_confidence_cap; ... |
| A39 | 40 | Mike Evans | WR | TB | 28.4015 | low_15_29 | 0.8 | capped_review_required | aging_wr | missing_or_mismatched_team, identity_review_cap, partial_or_quarantined_join, confidence_capped, route_target_snap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; missing_or_review_route_target_snap_evidence; ... |
| A46 | 41 | Jerry Jeudy | WR | CLE | 31.1199 | middle_30_49 | 0.88 | usable_with_confidence_cap | volatile_profile | roster_category_status_prompt, first_down_source_gap, route_target_snap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; first_down_missing_confidence_cap; missing_or_review_route_target_snap_evidence; ... |
| A42 | 42 | Tyreek Hill | WR | MIA | 31.4237 | middle_30_49 | 0.8 | capped_review_required | aging_elite_wr | historical_team_context, identity_review_cap, partial_or_quarantined_join, confidence_capped, route_target_snap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; repeated_header_rows_removed=1; team_mismatch_or_historical_team; ... |
| A48 | 43 | Tank Dell | WR | HOU | 27.2878 | low_15_29 | 0.82 | capped_review_required | injury_status | roster_category_status_prompt, confidence_capped, first_down_source_gap, route_target_snap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; repeated_header_rows_removed=1; partial_first_down_confidence_cap; ... |
| A16 | 45 | Xavier Worthy | WR | KC | 27.9883 | low_15_29 | 0.88 | usable_with_confidence_cap | young_wr_warning | route_target_snap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence |
| A15 | 46 | Malik Nabers | WR | NYG | 30.4824 | middle_30_49 | 0.88 | usable_with_confidence_cap | young_wr_warning | route_target_snap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence |
| A40 | 47 | Cooper Kupp | WR | SEA | 26.4622 | low_15_29 | 0.8 | capped_review_required | aging_wr | missing_or_mismatched_team, identity_review_cap, partial_or_quarantined_join, confidence_capped, first_down_source_gap, route_target_snap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; first_down_missing_confidence_cap; ... |
| A53 | 48 | Hollywood Brown | WR | KC | 28.4834 | low_15_29 | 0.88 | usable_with_confidence_cap | injury_status | roster_category_status_prompt, first_down_source_gap | missing_stats_first_component_evidence; missing_efficiency_context_evidence; first_down_missing_confidence_cap; missing_stats_first_confidence_cap; ... |
| A41 | 52 | Amari Cooper | WR | LV | 20.7072 | low_15_29 | 0.8 | capped_review_required | aging_wr | historical_team_context, identity_review_cap, partial_or_quarantined_join, confidence_capped, first_down_source_gap, route_target_snap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_historical_team; first_down_missing_confidence_cap; ... |
| A55 | 56 | Darrell Henderson | RB | LA | 9.6644 | bottom_under_15 | 0.8 | capped_review_required | replacement_rb | historical_team_context, identity_review_cap, partial_or_quarantined_join, confidence_capped, first_down_source_gap, route_target_snap_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_historical_team; first_down_missing_confidence_cap; ... |
| WARN | 69 | Daniel Jones | QB | IND | 31.3120 | middle_30_49 | 0.8 | capped_review_required | exported_status_warning | missing_or_mismatched_team, identity_review_cap, partial_or_quarantined_join, confidence_capped | team_mismatch_or_missing_model_team; one_qb_small_vorp_gap_cap; identity_review_cap; partial_or_quarantined_join_cap |

## Review Observations

- Exported team/identity warning rows include `George Pickens`, `Jaylen Waddle`,
  `Kenneth Walker III`, `Stefon Diggs`, `Keenan Allen`, `David Montgomery`,
  `Mike Evans`, `Tyreek Hill`, `Cooper Kupp`, `Amari Cooper`, `Darrell
  Henderson`, and `Daniel Jones`.
- Named injury/status roster rows include `Tank Dell` and `Hollywood Brown`.
  Their rows show capped/source-gap context, but this report does not add or
  change injury penalties.
- Volatile/status prompt rows include `De'Von Achane`, `Quentin Johnston`, and
  `Jerry Jeudy`.
- `Keenan Allen` appears with current checkpoint score `41.6097`; this report
  does not use legacy active-pack value as primary value.
- The right question for this task is whether these risks are visible and
  traceable, not whether the model should move the scores.

## Non-Goals

- Do not change injury/status penalties from this report.
- Do not change model weights, veteran age curves, rookie weights, VORP,
  replacement formulas, confidence caps, pick baselines, or startup-slot
  conversion.
- Do not add market, ADP, rankings, projections, consensus, startup, or
  trade-calculator logic to private value.
- Do not convert any review label into a trade, cut, keep, draft, buy, sell,
  defer, target, or start/sit recommendation.
