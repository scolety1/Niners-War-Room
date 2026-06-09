# Veteran Age-Window Audit

Date: 2026-06-05

Mode: review-only refinement prep.

Purpose: review older productive veterans, exported age-warning coverage, and
score bands before any formula work. This report is evidence only. It does not
change veteran age curves, model weights, VORP, replacement formulas,
confidence caps, generated outputs, active rankings, app state, or any
recommendation logic.

## Sources

- Current-player source:
  `local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv`
- Score column: `checkpoint_review_score`
- Lineage: `review_v4_current_player`
- Audit roster source:
  `docs/model_v4/NAMED_PLAYER_AUDIT_ROSTER_20260605.md`
- Allowed use: `review_only_current_value_checkpoint`
- Blocked use: `do_not_use_as_final_ranking_or_roster_recommendation`

This audit uses exported warning flags and named audit-roster veteran categories.
It does not infer dates of birth or add new age data.

## Scope Counts

- Named current-player veteran/aging rows from audit roster: 15.
- Additional exported RB age-warning rows outside those roster categories: 3.
- Total rows reviewed here: 18.
- Exported RB age-warning rows reviewed here: 8.
- Capped-review rows reviewed here: 10.
- Identity/team-review rows reviewed here: 9.
- Low-score veteran review rows: 4.

## Classification Labels

- `explicit_age_guardrail`: exported warning text includes RB age-window or
  age-cliff language.
- `high_score_age_review`: score is at least 60 and the row has age-warning or
  named aging-veteran context.
- `confidence_capped`: `confidence_status` is `capped_review_required`.
- `identity_or_team_review`: exported warning text includes team mismatch,
  historical team, or identity-review language.
- `format_cap_context`: exported warning text includes no-premium TE cap
  language.
- `low_score_veteran_review`: score is below 30 and the row has named aging or
  veteran context.
- `veteran_context_review`: named veteran row without one of the more specific
  labels above.

## Reviewed Veteran/Age Rows

| Audit ID | File Row | Player | Pos | Team | Score | Score Band | Confidence Cap | Confidence Status | Audit Category | Classification | Warning Preview |
|---|---:|---|---|---|---:|---|---:|---|---|---|---|
| A21 | 3 | Christian McCaffrey | RB | SF | 82.8329 | top_70_plus | 0.88 | usable_with_confidence_cap | elite_aging_rb | explicit_age_guardrail, high_score_age_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; rb_age_cliff_guardrail_active; missing_or_review_route_target_snap_evidence; ... |
| A25 | 9 | Derrick Henry | RB | BAL | 66.2156 | high_50_69 | 0.88 | usable_with_confidence_cap | aging_rb | explicit_age_guardrail, high_score_age_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; rb_age_cliff_guardrail_active; missing_or_review_route_target_snap_evidence; ... |
| A29 | 14 | Saquon Barkley | RB | PHI | 60.8166 | high_50_69 | 0.88 | usable_with_confidence_cap | aging_rb | explicit_age_guardrail, high_score_age_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; rb_age_cliff_guardrail_active; ... |
| A30 | 17 | Josh Jacobs | RB | GB | 58.5387 | high_50_69 | 0.88 | usable_with_confidence_cap | aging_rb | explicit_age_guardrail | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; rb_age_window_caution_active; ... |
| A34 | 31 | David Montgomery | RB | HOU | 35.0486 | middle_30_49 | 0.8 | capped_review_required | veteran_depth_rb | explicit_age_guardrail, confidence_capped, identity_or_team_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; rb_age_cliff_guardrail_active; ... |
| A37 | 19 | Davante Adams | WR | LA | 57.5485 | high_50_69 | 0.88 | usable_with_confidence_cap | aging_wr | veteran_context_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence |
| A38 | 27 | Stefon Diggs | WR | NE | 45.2808 | middle_30_49 | 0.8 | capped_review_required | aging_wr | confidence_capped, identity_or_team_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; missing_or_review_route_target_snap_evidence; ... |
| A39 | 40 | Mike Evans | WR | TB | 28.4015 | low_15_29 | 0.8 | capped_review_required | aging_wr | confidence_capped, identity_or_team_review, low_score_veteran_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; missing_or_review_route_target_snap_evidence; ... |
| A40 | 47 | Cooper Kupp | WR | SEA | 26.4622 | low_15_29 | 0.8 | capped_review_required | aging_wr | confidence_capped, identity_or_team_review, low_score_veteran_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; first_down_missing_confidence_cap; ... |
| A41 | 52 | Amari Cooper | WR | LV | 20.7072 | low_15_29 | 0.8 | capped_review_required | aging_wr | confidence_capped, identity_or_team_review, low_score_veteran_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_historical_team; first_down_missing_confidence_cap; ... |
| A42 | 42 | Tyreek Hill | WR | MIA | 31.4237 | middle_30_49 | 0.8 | capped_review_required | aging_elite_wr | confidence_capped, identity_or_team_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; repeated_header_rows_removed=1; team_mismatch_or_historical_team; ... |
| A43 | 30 | Keenan Allen | WR | LAC | 41.6097 | middle_30_49 | 0.8 | capped_review_required | legacy_leak_sentinel | confidence_capped, identity_or_team_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_missing_model_team; missing_or_review_route_target_snap_evidence; ... |
| A63 | 65 | Travis Kelce | TE | KC | 57.1755 | high_50_69 | 0.88 | usable_with_confidence_cap | aging_te | veteran_context_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; missing_or_review_route_target_snap_evidence; ... |
| A66 | 70 | George Kittle | TE | SF | 32.0994 | middle_30_49 | 0.88 | usable_with_confidence_cap | aging_te | format_cap_context | licensed_route_metrics_not_available; not_used_in_stats_first_value; first_down_missing_confidence_cap; no_premium_te_small_gap_cap; ... |
| A68 | 73 | Mark Andrews | TE | BAL | 23.1327 | low_15_29 | 0.88 | usable_with_confidence_cap | aging_te | format_cap_context, low_score_veteran_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; no_premium_te_small_gap_cap; ... |
| WARN | 4 | Jonathan Taylor | RB | IND | 80.1465 | top_70_plus | 0.88 | usable_with_confidence_cap | exported_rb_age_warning | explicit_age_guardrail, high_score_age_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; rb_age_window_caution_active; missing_or_review_route_target_snap_evidence; ... |
| WARN | 49 | Devin Singletary | RB | NYG | 23.9309 | low_15_29 | 0.82 | capped_review_required | exported_rb_age_warning | explicit_age_guardrail, confidence_capped | licensed_route_metrics_not_available; not_used_in_stats_first_value; shifted_header_expected_player_header_inferred; rb_age_window_caution_active; ... |
| WARN | 56 | Darrell Henderson | RB | LA | 9.6644 | bottom_under_15 | 0.8 | capped_review_required | exported_rb_age_warning | explicit_age_guardrail, confidence_capped, identity_or_team_review | licensed_route_metrics_not_available; not_used_in_stats_first_value; team_mismatch_or_historical_team; first_down_missing_confidence_cap; ... |

## Review Observations

- High-score age-review RB rows include `Christian McCaffrey`, `Jonathan Taylor`,
  `Derrick Henry`, and `Saquon Barkley`. These are human-review prompts for age
  warning visibility, not evidence that the age curve is wrong.
- Middle/low veteran WR rows with confidence and identity/team warnings include
  `Stefon Diggs`, `Mike Evans`, `Cooper Kupp`, `Amari Cooper`, `Tyreek Hill`,
  and `Keenan Allen`.
- Aging TE rows are mostly governed by TE context rather than exported age text:
  `Travis Kelce`, `George Kittle`, and `Mark Andrews` should remain tied to the
  no-premium TE discipline review.
- `Keenan Allen` appears with current checkpoint score `41.6097`; this report
  does not use legacy active-pack value as primary value.
- `Darrell Henderson` and `Devin Singletary` are low-score RB age-warning rows
  with capped or source-warning context.

## Non-Goals

- Do not change veteran age curves from this report.
- Do not change model weights, VORP, replacement formulas, confidence caps, pick
  baselines, or startup-slot conversion from this report.
- Do not add market, ADP, rankings, projections, consensus, startup, or
  trade-calculator logic to private value.
- Do not convert any review label into a trade, cut, keep, draft, buy, sell,
  defer, target, or start/sit recommendation.
