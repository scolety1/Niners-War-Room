# Phase 11D QB/TE Current Value

## Purpose

Phase 11D builds a review-only QB/TE current value layer. It uses Phase 11A allowed fields and the Phase 11B review-only VORP core. It does not promote app surfaces, change active rankings, alter My Team or War Board, or unlock readiness gates.

## Outputs

- `local_exports\model_v4\current_value\latest\qb_te_current_value_review_rows.csv`
- `local_exports\model_v4\current_value\latest\qb_te_current_value_component_rows.csv`
- `local_exports\model_v4\current_value\latest\qb_te_current_value_receipts.csv`
- `local_exports\model_v4\current_value\latest\qb_te_current_value_warnings.csv`

## Formula Shape

QB current value uses VORP anchor, rushing separation, admitted passing volume/current production, and regression context. Pocket or replacement level QB profiles are capped in this 10-team 1QB format.

TE current value uses VORP anchor, route/target role, first-down/yardage production, YPRR/target efficiency, and red-zone context. No TE premium is applied.

Missing components are not converted to zero or average. Discipline multipliers cap replaceable QB and small-gap TE profiles.

## Safety Rules

- Review-only outputs.
- No market, projection, ADP, ranking, mock, big-board, or consensus inputs.
- First-down value comes through Phase 11B admitted first-down handling.
- Return scoring remains direct scoring context only and is not a talent signal.
- No active app ranking, My Team, War Board, or readiness changes.

## Summary

- Player rows: 20
- Component rows: 100
- Receipt rows: 80
- Warning rows: 62
- Market rows used: 0
- Projection rows used: 0

## Top Review Rows

| Player | Pos | Team | Review Score | Discipline | Confidence |
| --- | --- | --- | ---: | --- | --- |
| Trey McBride | TE | ARI | 95.583 | no_premium_te_real_vorp_gap | high_review_confidence |
| Josh Allen | QB | BUF | 89.4756 | one_qb_real_vorp_gap | high_review_confidence |
| Jalen Hurts | QB | PHI | 72.5245 | one_qb_real_vorp_gap | high_review_confidence |
| Patrick Mahomes | QB | KC | 62.8043 | one_qb_real_vorp_gap | high_review_confidence |
| Travis Kelce | TE | KC | 62.4732 | no_premium_te_real_vorp_gap | high_review_confidence |
| Brock Bowers | TE | LV | 54.636 | no_premium_te_real_vorp_gap | high_review_confidence |
| Jake Ferguson | TE | DAL | 49.7325 | no_premium_te_real_vorp_gap | high_review_confidence |
| Lamar Jackson | QB | BAL | 41.177 | one_qb_small_vorp_gap_cap | high_review_confidence |
| Daniel Jones | QB | IND | 39.14 | one_qb_small_vorp_gap_cap | high_review_confidence |
| George Kittle | TE | SF | 38.8049 | no_premium_te_small_gap_cap | high_review_confidence |
