# Phase 4 WR Evidence Audit

This report investigates the main Phase 3 WR review finding before any formula tuning. It does not change weights, promote rankings, or unlock decision readiness.

## Summary

- review_status: review_only
- requested_players: 9
- matched_players: 9
- missing_players: 0
- route_data_unavailable_rows: 9
- projection_gap_rows: 0
- first_down_projection_gap_rows: 9
- usage_normalization_review_rows: 8
- production_normalization_review_rows: 5
- young_bridge_review_rows: 4
- true_formula_imbalance_review_rows: 0
- score_changes_applied: False
- active_rankings_promoted: False

## Interpretation

- Route participation remains unavailable/proxy-only in the free-data model.
- Missing first-down projections remain a projection-layer gap, not a WR-only bug.
- Any formula imbalance should be handled only after fixture-backed review.

## Player Evidence Table

| matched_player | dynasty_asset_value | overall_preview_rank | wr_preview_rank | confidence_label | route_data_unavailable | projection_gap | first_down_projection_gap | usage_normalization_review | production_normalization_review | young_bridge_review | true_formula_imbalance_review | recommended_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Jaxon Smith-Njigba | 49.93 | 15 | 6 | usable | True |  | True | True | True | True |  | Inspect production normalization before any weight change. |
| Puka Nacua | 46.57 | 18 | 9 | usable | True |  | True | True | True | True |  | Inspect production normalization before any weight change. |
| CeeDee Lamb | 49.64 | 16 | 7 | usable | True |  | True | True | True |  |  | Inspect production normalization before any weight change. |
| Tee Higgins | 46.62 | 17 | 8 | usable | True |  | True | True | True |  |  | Inspect production normalization before any weight change. |
| Brian Thomas Jr. | 51.12 | 14 | 5 | usable | True |  | True | True |  | True |  | Inspect derived usage normalization before any weight change. |
| Malik Nabers | 52.21 | 11 | 4 | usable | True |  | True | True | True | True |  | Inspect production normalization before any weight change. |
| Ja'Marr Chase | 66.08 | 4 | 1 | usable | True |  | True |  |  |  |  | Keep projection gap visible; do not tune around missing projection evidence. |
| Justin Jefferson | 55.65 | 10 | 3 | usable | True |  | True | True |  |  |  | Inspect derived usage normalization before any weight change. |
| Amon-Ra St. Brown | 56.86 | 8 | 2 | usable | True |  | True | True |  |  |  | Inspect derived usage normalization before any weight change. |

## Component Detail

| matched_player | production_score | production_contribution | first_down_fit_score | first_down_fit_contribution | usage_opportunity_score | usage_opportunity_contribution | snap_proxy_role_score | snap_proxy_role_contribution | projection_score | projection_contribution | age_dropoff_score | age_dropoff_contribution | young_player_prior_contribution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Jaxon Smith-Njigba | 46.92 | 12.20 | 56.00 | 6.72 | 31.17 | 7.48 | 86.41 | 5.18 | 65.13 | 6.51 | 94.00 | 11.28 | 0.55 |
| Puka Nacua | 39.87 | 10.37 | 49.00 | 5.88 | 31.10 | 7.46 | 69.73 | 4.18 | 71.20 | 7.12 | 94.00 | 11.28 | 0.28 |
| CeeDee Lamb | 49.80 | 12.95 | 58.00 | 6.96 | 32.44 | 7.79 | 80.20 | 4.81 | 58.50 | 5.85 | 94.00 | 11.28 | 0.00 |
| Tee Higgins | 43.37 | 11.28 | 48.00 | 5.76 | 38.78 | 9.31 | 79.08 | 4.75 | 42.50 | 4.25 | 94.00 | 11.28 | 0.00 |
| Brian Thomas Jr. | 57.67 | 14.99 | 56.00 | 6.72 | 34.79 | 8.35 | 79.35 | 4.76 | 36.10 | 3.61 | 94.00 | 11.28 | 1.40 |
| Malik Nabers | 49.53 | 12.88 | 56.00 | 6.72 | 40.85 | 9.80 | 90.60 | 5.44 | 50.70 | 5.07 | 90.00 | 10.80 | 1.50 |
| Ja'Marr Chase | 80.67 | 20.97 | 77.00 | 9.24 | 52.07 | 12.50 | 92.29 | 5.54 | 65.57 | 6.56 | 94.00 | 11.28 | 0.00 |
| Justin Jefferson | 64.78 | 16.84 | 62.00 | 7.44 | 37.25 | 8.94 | 93.18 | 5.59 | 55.53 | 5.55 | 94.00 | 11.28 | 0.00 |
| Amon-Ra St. Brown | 59.04 | 15.35 | 72.00 | 8.64 | 42.29 | 10.15 | 88.29 | 5.30 | 61.43 | 6.14 | 94.00 | 11.28 | 0.00 |
