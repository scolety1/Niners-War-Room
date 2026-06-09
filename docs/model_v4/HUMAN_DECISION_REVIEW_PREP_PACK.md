# Human Decision Review Prep Pack

This pack prepares the finished Model v4 review-only outputs for human final decision review. It does not create final cut, keep, trade, pick-defer, or rookie draft recommendations.

## Status

- Review status: `review_only_human_decision_prep`
- Final recommendations created: False
- My Team changed: False
- War Board changed: False
- Active rankings changed: False
- Readiness unlocked: False

## Output Files

- `local_exports\model_v4\human_decision_review_prep\latest\human_decision_review_summary.csv`
- `local_exports\model_v4\human_decision_review_prep\latest\pick_review_cards.csv`
- `local_exports\model_v4\human_decision_review_prep\latest\roster_pressure_review_cards.csv`
- `local_exports\model_v4\human_decision_review_prep\latest\trade_review_cards.csv`
- `local_exports\model_v4\human_decision_review_prep\latest\rookie_manual_scout_queue.csv`
- `local_exports\model_v4\human_decision_review_prep\latest\veteran_risk_review_cards.csv`

## Review First When You Return

1. Start with `pick_review_cards.csv`, especially `2026 1.03` and `2026 1.04`.
2. Then open `roster_pressure_review_cards.csv` and review the pressure line names.
3. Use `rookie_manual_scout_queue.csv` to scout outliers before trusting rookie scores.
4. Use `trade_review_cards.csv` for conversation targets, not offers.
5. Use `veteran_risk_review_cards.csv` for age, QB, TE, and role-window discussion.

## Pick Snapshot

- `2026 1.03`: 2026 1.03 has a review score of 93.6; same-slot defer delta is 6.4.
- `2026 1.04`: 2026 1.04 has a review score of 90.4; same-slot defer delta is 7.232.
- `2026 2.04`: 2026 2.04 has a review score of 71.4; same-slot defer delta is 5.712.
- `2026 2.08`: 2026 2.08 has a review score of 58.6; same-slot defer delta is 4.688.
- `2026 5.04`: 2026 5.04 is manual-only context with no admitted exact model baseline; exact pick equivalence is blocked.

## Roster Pressure Snapshot

- Luke McCaffrey (WR): protectable_depth_review
- Kaleb Johnson (RB): required_pressure_zone_review
- Devin Singletary (RB): protected_core_review
- T.J. Hockenson (TE): protectable_depth_review
- Jalen Coker (WR): protectable_depth_review
- Daniel Jones (QB): protected_core_review
- Jayden Higgins (WR): protected_core_review
- Brandon Aiyuk (WR): protected_core_review

## Rookie Scout Queue Snapshot

- Jeremiyah Love (RB): tier_gap_context_review
- Makai Lemon (WR): significant_pick_value_gap_review
- Skyler Bell (WR): significant_pick_value_gap_review
- Jordyn Tyson (WR): significant_pick_value_gap_review
- Chris Brazzell (WR): significant_pick_value_gap_review
- Ted Hurst (WR): significant_pick_value_gap_review
- Carnell Tate (WR): significant_pick_value_gap_review
- Antonio Williams (WR): significant_pick_value_gap_review
- Jeremiyah Love (RB): tier_gap_context_review
- Makai Lemon (WR): significant_pick_value_gap_review
- Skyler Bell (WR): significant_pick_value_gap_review
- Jordyn Tyson (WR): significant_pick_value_gap_review

## Veteran Risk Snapshot

- Trey McBride (TE): te_route_target_engine
- Puka Nacua (WR): wr_target_earner
- Jaxon Smith-Njigba (WR): wr_target_earner
- Christian McCaffrey (RB): rb_short_window_three_down_role_asset
- Josh Allen (QB): qb_hybrid_rushing_passing_engine
- Jonathan Taylor (RB): rb_short_window_three_down_role_asset
- Bijan Robinson (RB): rb_short_window_three_down_role_asset
- Ja'Marr Chase (WR): wr_target_earner
- Jahmyr Gibbs (RB): rb_short_window_three_down_role_asset
- Amon-Ra St. Brown (WR): wr_target_earner

## Guardrail

Every row in this pack is review-only. Humans still make the final decisions.
