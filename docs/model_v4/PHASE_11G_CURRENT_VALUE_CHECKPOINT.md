# Phase 11G Current Value Integration Checkpoint

## Purpose

Phase 11G combines the review-only RB/WR, QB/TE, lifecycle, and confidence layers into one current player checkpoint. This is not a final dynasty ranking and is not promoted to the active app.

## Outputs

- `local_exports\model_v4\current_value\latest\current_player_value_review_rows.csv`
- `local_exports\model_v4\current_value\latest\current_player_value_component_rows.csv`
- `local_exports\model_v4\current_value\latest\current_player_value_receipts.csv`
- `local_exports\model_v4\current_value\latest\current_player_value_warnings.csv`

## Formula Visibility

- `position_specific_review_score` stays separate from position module details.
- `discipline_status` keeps QB/TE replacement discipline visible.
- `lifecycle_modifier_review` and `role_archetype` stay visible.
- `confidence_cap` is applied openly to produce `checkpoint_review_score`.
- Market, projection, ADP, and ranking fields are not consumed.

## Summary

- Review rows: 80
- Component rows: 880
- Receipt rows: 1040
- Warning rows: 514
- Market rows used: 0
- Projection rows used: 0

## Sample Rows Sorted For Review

| Player | Pos | Module | Base | Lifecycle | Confidence | Checkpoint |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Trey McBride | TE | qb_te_current_value | 95.583 | 1.04 | 0.88 | 87.4776 |
| Puka Nacua | WR | rb_wr_current_value | 90.7437 | 1.04 | 0.88 | 83.0486 |
| Jaxon Smith-Njigba | WR | rb_wr_current_value | 90.5499 | 1.04 | 0.88 | 82.8713 |
| Christian McCaffrey | RB | rb_wr_current_value | 90.508 | 1.04 | 0.88 | 82.8329 |
| Josh Allen | QB | qb_te_current_value | 89.4756 | 1.02 | 0.88 | 80.3133 |
| Jonathan Taylor | RB | rb_wr_current_value | 87.5727 | 1.04 | 0.88 | 80.1465 |
| Bijan Robinson | RB | rb_wr_current_value | 87.4059 | 1.04 | 0.88 | 79.9939 |
| Ja'Marr Chase | WR | rb_wr_current_value | 80.9941 | 1.04 | 0.88 | 74.1258 |
| Jahmyr Gibbs | RB | rb_wr_current_value | 80.8536 | 1.04 | 0.88 | 73.9972 |
| Amon-Ra St. Brown | WR | rb_wr_current_value | 80.4313 | 1.04 | 0.82 | 68.5918 |
| De'Von Achane | RB | rb_wr_current_value | 72.847 | 1.04 | 0.88 | 66.6696 |
| Derrick Henry | RB | rb_wr_current_value | 76.005 | 0.99 | 0.88 | 66.2156 |
| Jalen Hurts | QB | qb_te_current_value | 72.5245 | 1.02 | 0.88 | 65.098 |
| James Cook | RB | rb_wr_current_value | 73.2007 | 0.99 | 0.88 | 63.7724 |
| George Pickens | WR | rb_wr_current_value | 75.6951 | 1.04 | 0.8 | 62.9783 |
