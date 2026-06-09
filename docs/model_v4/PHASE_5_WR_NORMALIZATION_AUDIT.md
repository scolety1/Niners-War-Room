# Phase 5G WR Production And Usage Normalization Audit

This report checks whether elite WR preview values are low because of a normalization bug, missing/limited evidence, route-data gaps, or a formula balance concern. It does not change weights, promote rankings, or unlock readiness.

## Summary

- review_status: review_only
- requested_players: 9
- matched_players: 9
- missing_players: 0
- confirmed_normalization_bug_rows: 0
- formula_or_data_recency_concern_rows: 5
- route_unavailable_rows: 9
- estimated_first_down_projection_rows: 9
- latest_production_source_season: 2024
- latest_usage_source_season: 2024
- latest_snap_source_season: 2024
- rb_control_median_dynasty_asset_value: 67.12
- rb_control_median_usage_score: 60.12
- score_changes_applied: False
- active_rankings_promoted: False

## Verdict

- No confirmed production or usage normalization mismatch was patched by this audit.
- The main WR limitation is evidence quality: current structured production, usage, and snap inputs are latest-season nflverse rows from the 2022-2024 source set, while several sanity beliefs rely on newer dynasty context.
- Route participation, routes run, TPRR, and YPRR remain unavailable in the safe free-data model; snap share is proxy-only and cannot explain route quality.
- First-down projections are estimated from history for most projected WRs, not direct.
- Formula imbalance remains a review concern where strong projection evidence cannot overcome low/stale historical production or conservative usage scores.

## Player Audit

| matched_player | dynasty_asset_value | overall_preview_rank | wr_preview_rank | latest_production_season | production_normalized_score | usage_normalized_score | projection_normalized_score | route_data_effect | formula_concern | recommended_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Jaxon Smith-Njigba | 50.76 | 20 | 6 | 2024 | 46.92 | 31.17 | 73.44 | route data unavailable; usage relies on target/opportunity fields and snap share remains proxy-only | formula/data recency concern: strong projection cannot overcome low/stale latest production/usage in current weights | Document for formula/data-recency pass; do not tune until fixture-backed and fresher data are available. |
| Puka Nacua | 47.64 | 24 | 9 | 2024 | 39.87 | 31.10 | 81.88 | route data unavailable; usage relies on target/opportunity fields and snap share remains proxy-only | formula/data recency concern: strong projection cannot overcome low/stale latest production/usage in current weights | Document for formula/data-recency pass; do not tune until fixture-backed and fresher data are available. |
| CeeDee Lamb | 50.51 | 21 | 7 | 2024 | 49.80 | 32.44 | 67.25 | route data unavailable; usage relies on target/opportunity fields and snap share remains proxy-only | formula/data recency concern: strong projection cannot overcome low/stale latest production/usage in current weights | Document for formula/data-recency pass; do not tune until fixture-backed and fresher data are available. |
| Tee Higgins | 47.27 | 26 | 10 | 2024 | 43.37 | 38.78 | 49.07 | route data unavailable; usage relies on target/opportunity fields and snap share remains proxy-only | data gap concern: missing route quality limits WR confidence and separation | Keep route gap visible; use licensed structured route source or leave proxy-only. |
| Brian Thomas Jr. | 51.68 | 19 | 5 | 2024 | 57.67 | 34.79 | 41.70 | route data unavailable; usage relies on target/opportunity fields and snap share remains proxy-only | data gap concern: missing route quality limits WR confidence and separation | Keep route gap visible; use licensed structured route source or leave proxy-only. |
| Malik Nabers | 52.84 | 16 | 4 | 2024 | 49.53 | 40.85 | 57.00 | route data unavailable; usage relies on target/opportunity fields and snap share remains proxy-only | data gap concern: missing route quality limits WR confidence and separation | Keep route gap visible; use licensed structured route source or leave proxy-only. |
| Ja'Marr Chase | 67.08 | 4 | 1 | 2024 | 80.67 | 52.07 | 75.56 | route data unavailable; usage relies on target/opportunity fields and snap share remains proxy-only | data gap concern: missing route quality limits WR confidence and separation | Keep route gap visible; use licensed structured route source or leave proxy-only. |
| Justin Jefferson | 56.63 | 14 | 3 | 2024 | 64.78 | 37.25 | 65.37 | route data unavailable; usage relies on target/opportunity fields and snap share remains proxy-only | formula/data recency concern: strong projection cannot overcome low/stale latest production/usage in current weights | Document for formula/data-recency pass; do not tune until fixture-backed and fresher data are available. |
| Amon-Ra St. Brown | 57.93 | 12 | 2 | 2024 | 59.04 | 42.29 | 72.11 | route data unavailable; usage relies on target/opportunity fields and snap share remains proxy-only | formula/data recency concern: strong projection cannot overcome low/stale latest production/usage in current weights | Document for formula/data-recency pass; do not tune until fixture-backed and fresher data are available. |

## Raw And Normalized Components

| matched_player | production_lve_points_no_first_downs | first_downs | target_share | weighted_opportunities | snap_share | projection_recomputed_lve_points | age | age_bucket | young_player_prior_contribution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Jaxon Smith-Njigba | 140.77 | 56.00 | 0.21 | 163.70 | 0.86 | 220.31 | 24.00 | prime_window | 0.55 |
| Puka Nacua | 119.60 | 49.00 | 0.28 | 161.50 | 0.70 | 245.64 | 24.00 | prime_window | 0.28 |
| CeeDee Lamb | 149.40 | 58.00 | 0.25 | 191.10 | 0.80 | 201.75 | 27.00 | prime_window | 0.00 |
| Tee Higgins | 130.10 | 48.00 | 0.22 | 126.50 | 0.79 | 147.20 | 27.00 | prime_window | 0.00 |
| Brian Thomas Jr. | 173.00 | 56.00 | 0.23 | 161.25 | 0.79 | 125.09 | 23.00 | prime_window | 1.40 |
| Malik Nabers | 148.60 | 56.00 | 0.30 | 202.80 | 0.91 | 171.01 | 22.00 | prime_window | 1.50 |
| Ja'Marr Chase | 242.00 | 77.00 | 0.25 | 204.25 | 0.92 | 226.69 | 26.00 | prime_window | 0.00 |
| Justin Jefferson | 194.33 | 62.00 | 0.25 | 188.45 | 0.93 | 196.12 | 26.00 | prime_window | 0.00 |
| Amon-Ra St. Brown | 177.13 | 72.00 | 0.24 | 175.65 | 0.88 | 216.32 | 26.00 | prime_window | 0.00 |

## Review Notes

- A low WR row is not automatically a bug. This audit only treats a row as a confirmed normalization bug when the displayed normalized score does not reconcile to the displayed raw component inputs.
- Stale or incomplete evidence should be fixed with better source rows before changing weights.
