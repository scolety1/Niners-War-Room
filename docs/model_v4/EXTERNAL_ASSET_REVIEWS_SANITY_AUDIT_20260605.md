# External Asset Reviews Sanity Audit

Date: 2026-06-05

Mode: review-only refinement prep.

Purpose: inspect External Asset Review rows for top context assets, warnings,
lineage disclosure, and review-only framing. This report is evidence only. It
does not change formulas, model weights, market-gap thresholds, active data
packs, generated outputs, active rankings, My Team, War Board, readiness gates,
app promotion, or recommendation logic.

## Source Status

| Layer | Path / API | Status | Notes |
|---|---|---|---|
| Repaired External Asset Reviews service | `src/services/model_v4_sprint14c_trade_review_service.py::build_trade_review_outputs()` | available in memory | Produces neutral `external_asset_rows`, `trade_away_rows`, source disclosure, lineage, allowed/blocked use, and review-only summary flags. |
| Canonical external asset context CSV | `local_exports/model_v4/external_asset_reviews/latest/external_asset_context_review_rows.csv` | missing locally | Do not generate this output in review-only refinement prep. |
| Canonical roster-pressure CSV | `local_exports/model_v4/external_asset_reviews/latest/trade_away_candidate_review_rows.csv` | missing locally | Do not generate this output in review-only refinement prep. |
| Compatibility fallback external asset CSV | `local_exports/model_v4/trade_review/latest/trade_for_candidate_review_rows.csv` | present, stale naming | Contains older `trade_for_review_band` and `elite_target_review` labels; use as compatibility evidence only. |
| Compatibility fallback roster-pressure CSV | `local_exports/model_v4/trade_review/latest/trade_away_candidate_review_rows.csv` | present, stale naming | Contains older trade-away naming; blocked use still says not a sell call. |
| Cross-asset value source | `local_exports/model_v4/dynasty_asset_value/latest/dynasty_asset_value_review_rows.csv` | present | Backing source for `dynasty_asset_value_review_score`. |

## Repaired Service Snapshot

- Review status: `review_only`.
- External asset context rows: 35.
- Roster pressure context rows: 24.
- Compatibility alias count: `trade_for_rows` = 35.
- Trade recommendations created: `False`.
- Trade packages created: `False`.
- Active rankings changed: `False`.
- Readiness unlocked: `False`.

Repaired external asset rows expose:

- `source_path`: `local_exports\model_v4\dynasty_asset_value\latest\dynasty_asset_value_review_rows.csv`.
- `source_column`: `dynasty_asset_value_review_score`.
- `lineage_class`: `review_v4_dynasty_asset`.
- `allowed_use`: `review_only_external_asset_context_not_recommendation`.
- `blocked_use`: `do_not_use_as_trade_offer_buy_call_or_acquisition_call`.

Repaired roster pressure rows expose:

- `source_path`: `local_exports\model_v4\decision_pressure\latest\cut_keep_pressure_review_rows.csv`.
- `source_column`: `pressure_score`.
- `lineage_class`: `review_v4_roster_pressure_context`.
- `allowed_use`: `review_only_trade_away_context_not_recommendation`.
- `blocked_use`: `do_not_use_as_trade_offer_or_sell_call`.

## Top External Asset Context Rows

| Asset | Pos | Team | Owner | Score | Cap | Band | Source Column | Lineage | Warning Preview |
|---|---|---|---|---:|---:|---|---|---|---|
| Trey McBride | TE | ARI | Dirt Devils | 87.4776 | 0.88 | elite_external_asset_context_review | dynasty_asset_value_review_score | review_v4_dynasty_asset | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence; ... |
| Puka Nacua | WR | LA | Rocky Mountain High | 83.0486 | 0.88 | elite_external_asset_context_review | dynasty_asset_value_review_score | review_v4_dynasty_asset | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence; ... |
| Jaxon Smith-Njigba | WR | SEA | The Mighty Canucks | 82.8713 | 0.88 | elite_external_asset_context_review | dynasty_asset_value_review_score | review_v4_dynasty_asset | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence; ... |
| Christian McCaffrey | RB | SF | Rocky Mountain High | 82.8329 | 0.88 | elite_external_asset_context_review | dynasty_asset_value_review_score | review_v4_dynasty_asset | licensed_route_metrics_not_available; not_used_in_stats_first_value; rb_age_cliff_guardrail_active; missing_or_review_route_target_snap_evidence; ... |
| Josh Allen | QB | BUF | The Mighty Canucks | 80.3133 | 0.88 | elite_external_asset_context_review | dynasty_asset_value_review_score | review_v4_dynasty_asset | qb_rushing_age_caution_active; missing_or_review_route_target_snap_evidence; review_only_no_trade_recommendation |
| Jonathan Taylor | RB | IND | Dirt Devils | 80.1465 | 0.88 | elite_external_asset_context_review | dynasty_asset_value_review_score | review_v4_dynasty_asset | licensed_route_metrics_not_available; not_used_in_stats_first_value; rb_age_window_caution_active; missing_or_review_route_target_snap_evidence; ... |
| Bijan Robinson | RB | ATL | Rocky Mountain High | 79.9939 | 0.88 | elite_external_asset_context_review | dynasty_asset_value_review_score | review_v4_dynasty_asset | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence; ... |
| Ja'Marr Chase | WR | CIN | Super Chargers | 74.1258 | 0.88 | strong_external_asset_context_review | dynasty_asset_value_review_score | review_v4_dynasty_asset | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence; ... |
| Jahmyr Gibbs | RB | DET | Shamrockettes | 73.9972 | 0.88 | strong_external_asset_context_review | dynasty_asset_value_review_score | review_v4_dynasty_asset | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence; ... |
| Amon-Ra St. Brown | WR | DET | Precise Guesswork | 68.5918 | 0.82 | strong_external_asset_context_review | dynasty_asset_value_review_score | review_v4_dynasty_asset | licensed_route_metrics_not_available; not_used_in_stats_first_value; repeated_header_rows_removed=1; partial_first_down_confidence_cap; ... |
| Derrick Henry | RB | BAL | Dirt Devils | 66.2156 | 0.88 | strong_external_asset_context_review | dynasty_asset_value_review_score | review_v4_dynasty_asset | licensed_route_metrics_not_available; not_used_in_stats_first_value; rb_age_cliff_guardrail_active; missing_or_review_route_target_snap_evidence; ... |
| Jalen Hurts | QB | PHI | Precise Guesswork | 65.0980 | 0.88 | strong_external_asset_context_review | dynasty_asset_value_review_score | review_v4_dynasty_asset | missing_or_review_route_target_snap_evidence; review_only_no_trade_recommendation |

## Roster Pressure Context Rows

| Player | Pos | Team | Value | Pressure | Band | Source Column | Lineage | Warning Preview |
|---|---|---|---:|---:|---|---|---|---|
| Luke McCaffrey | WR | WAS | 16.2148 | 72.2389 | pressure_shop_watch_review | pressure_score | review_v4_roster_pressure_context | licensed_route_metrics_not_available; not_used_in_stats_first_value; shifted_header_expected_player_header_inferred; missing_or_review_route_target_snap_evidence; ... |
| Kaleb Johnson | RB | PIT | 3.0698 | 53.3477 | liquidity_check_context_review | pressure_score | review_v4_roster_pressure_context | licensed_route_metrics_not_available; not_used_in_stats_first_value; no_historical_evidence_for_component; shifted_header_expected_player_header_inferred; ... |
| Devin Singletary | RB | NYG | 23.9309 | 47.7018 | hold_context_review | pressure_score | review_v4_roster_pressure_context | licensed_route_metrics_not_available; not_used_in_stats_first_value; shifted_header_expected_player_header_inferred; rb_age_window_caution_active; ... |
| T.J. Hockenson | TE | MIN | 13.7788 | 43.0159 | depth_liquidity_watch_review | pressure_score | review_v4_roster_pressure_context | licensed_route_metrics_not_available; not_used_in_stats_first_value; first_down_missing_confidence_cap; no_premium_te_replacement_level_cap; ... |
| Jalen Coker | WR | CAR | 22.2108 | 40.1919 | depth_liquidity_watch_review | pressure_score | review_v4_roster_pressure_context | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence; ... |
| Daniel Jones | QB | IND | 31.3120 | 37.2660 | hold_context_review | pressure_score | review_v4_roster_pressure_context | team_mismatch_or_missing_model_team; one_qb_small_vorp_gap_cap; identity_review_cap; partial_or_quarantined_join_cap; ... |
| Jayden Higgins | WR | HOU | 25.2852 | 32.8861 | hold_context_review | pressure_score | review_v4_roster_pressure_context | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence; ... |
| Brandon Aiyuk | WR | SF | 25.4061 | 27.7954 | hold_context_review | pressure_score | review_v4_roster_pressure_context | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence; ... |

## Framing Audit

- `app/pages/04_trade_central.py` title is `External Asset Reviews`.
- The visible tab label is `External Asset Context`.
- Page copy says context is review-only and does not create offers.
- Repaired service rows do not use `target`, `trade_for`, or `trade-for` in
  `external_asset_review_key`, `external_asset_review_band`,
  `review_rationale`, `allowed_use`, or `blocked_use`.
- Human review cards explicitly say roster-pressure rows are not sell calls.

## Carry-Forward Risks

- Canonical External Asset Review CSVs are missing locally. The app/service can
  produce repaired rows, but this queue did not write generated outputs.
- Compatibility fallback CSVs under `trade_review/latest` still contain stale
  names such as `trade_for_review_band`, `elite_target_review`, and
  `review_only_trade_for_context_not_recommendation`. Treat those as
  compatibility-only evidence until a later output refresh is allowed.
- External Asset rows are model-value context, not acquisition realism. The
  report does not estimate actual manager price, package cost, or trade market
  acceptance.

## Non-Goals

- Do not change formulas from this report.
- Do not change model weights, veteran age curves, rookie weights, pick
  baselines, VORP, replacement formulas, market-gap thresholds, confidence cap
  magnitudes, or startup-slot conversion.
- Do not mutate active rankings, My Team, War Board, readiness gates, app
  promotion, active data packs, generated model outputs, or user-entered draft
  state.
- Do not add market, ADP, rankings, projections, consensus, startup, or
  trade-calculator logic to private value.
- Do not convert review labels or external asset context into trade, cut, keep,
  draft, buy, sell, defer, target, or start/sit recommendations.
