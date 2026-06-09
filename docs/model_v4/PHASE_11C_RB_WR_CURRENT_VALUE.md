# Phase 11C RB/WR Current Value

## Purpose

Phase 11C builds a review-only RB/WR current value layer. It uses Phase 11A allowed fields and the Phase 11B review-only VORP core. It does not promote app surfaces, change active rankings, alter My Team or War Board, or unlock readiness gates.

## Outputs

- `local_exports\model_v4\current_value\latest\rb_wr_current_value_review_rows.csv`
- `local_exports\model_v4\current_value\latest\rb_wr_current_value_component_rows.csv`
- `local_exports\model_v4\current_value\latest\rb_wr_current_value_receipts.csv`
- `local_exports\model_v4\current_value\latest\rb_wr_current_value_warnings.csv`

## Formula Shape

RB current value uses VORP anchor, role/volume, first-down/high-value usage, receiving utility, and efficiency context.

WR current value uses VORP anchor, target/route role, first-down/yardage production, air-yard role, and efficiency context.

Missing components are not converted to zero or average. Available components are rescaled, then confidence caps reduce the review score when evidence is missing or partial.

## Safety Rules

- Review-only outputs.
- No market, projection, ADP, ranking, mock, big-board, or consensus inputs.
- First-down value comes through Phase 11B admitted first-down handling.
- Return scoring remains direct scoring context only and is not a talent or role signal.
- No active app ranking, My Team, War Board, or readiness changes.

## Summary

- Player rows: 60
- Component rows: 300
- Receipt rows: 240
- Warning rows: 193
- Market rows used: 0
- Projection rows used: 0

## Top Review Rows

| Player | Pos | Team | Review Score | Confidence |
| --- | --- | --- | ---: | --- |
| Puka Nacua | WR | LA | 90.7437 | high_review_confidence |
| Jaxon Smith-Njigba | WR | SEA | 90.5499 | high_review_confidence |
| Christian McCaffrey | RB | SF | 90.508 | high_review_confidence |
| Jonathan Taylor | RB | IND | 87.5727 | high_review_confidence |
| Bijan Robinson | RB | ATL | 87.4059 | high_review_confidence |
| Ja'Marr Chase | WR | CIN | 80.9941 | high_review_confidence |
| Jahmyr Gibbs | RB | DET | 80.8536 | high_review_confidence |
| Amon-Ra St. Brown | WR | DET | 80.4313 | high_review_confidence |
| Derrick Henry | RB | BAL | 76.005 | high_review_confidence |
| George Pickens | WR | DAL | 75.6951 | high_review_confidence |
