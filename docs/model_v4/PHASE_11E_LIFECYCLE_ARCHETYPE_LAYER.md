# Phase 11E Lifecycle And Archetype Layer

## Purpose

Phase 11E creates review-only lifecycle and role-archetype labels. These labels explain role shape, age guardrails, and fragility; they do not overwrite current-value evidence or active app rankings.

## Outputs

- `local_exports\model_v4\current_value\latest\lifecycle_archetype_review_rows.csv`
- `local_exports\model_v4\current_value\latest\lifecycle_archetype_component_rows.csv`
- `local_exports\model_v4\current_value\latest\lifecycle_archetype_receipts.csv`
- `local_exports\model_v4\current_value\latest\lifecycle_archetype_warnings.csv`

## Source Rules

- Uses only Phase 11A lifecycle fields plus the admitted player-age sidecar.
- Missing age remains missing; matched ages carry sidecar receipts.
- No injury, athletic, route, market, projection, ADP, ranking, mock, or big-board fields are fabricated or consumed.

## Summary

- Player rows: 80
- Component rows: 400
- Receipt rows: 320
- Warning rows: 51
- Age rows used: 80
- Market rows used: 0

## Sample Review Rows

| Player | Pos | Archetype | Modifier | Confidence |
| --- | --- | --- | ---: | ---: |
| De'Von Achane | RB | rb_short_window_three_down_role_asset | 1.04 | 1.0 |
| Lamar Jackson | QB | qb_rushing_dependent | 0.98 | 0.96 |
| Chase Brown | RB | rb_short_window_three_down_role_asset | 1.04 | 1.0 |
| Luther Burden | WR | wr_target_earner | 1.04 | 1.0 |
| Brian Thomas Jr. | WR | wr_role_fragility_review | 0.93 | 1.0 |
| Ricky Pearsall | WR | wr_target_earner | 1.04 | 1.0 |
| Quentin Johnston | WR | wr_role_fragility_review | 0.93 | 1.0 |
| Jakobi Meyers | WR | wr_possession_chain_mover | 1.01 | 1.0 |
| David Montgomery | RB | rb_role_fragility_review | 0.92 | 0.96 |
| Brandon Aiyuk | WR | wr_target_earner | 1.04 | 1.0 |
| Oronde Gadsden II | TE | te_route_target_engine | 1.04 | 1.0 |
| Jake Ferguson | TE | te_receiving_role_fragility_review | 0.94 | 1.0 |
