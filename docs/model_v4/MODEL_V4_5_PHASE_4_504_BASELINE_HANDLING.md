# Model v4.5 Phase 4: 2026 5.04 Baseline Handling

## Verdict

Chosen handling: `manual_only_no_exact_model_baseline`.

The admitted pick baseline table does not contain a 2026 5.04 value and does not contain enough admitted late-pick curve evidence to derive a conservative baseline without inventing precision. Model v4.5 therefore keeps the exact 5.04 value missing and quarantines it as manual-only review context.

## What Changed

- `2026 5.04` remains blank in numeric pick-value fields.
- Affected rows now explicitly show `manual_only_no_exact_model_baseline`.
- Startup Slot pick-zone rows no longer show fake above/below or nearby model assets for 5.04.
- Rookie Pick Decision Lab blocks exact trade, draft, or cut equivalence for 5.04.
- Cut Cost rows that fall below the admitted pick baseline floor now state that 5.04 has no exact model baseline.
- June 15 board pick context now marks 5.04 as `exact_model_equivalent=blocked`.

## Affected Outputs

- `local_exports/model_v4/pick_trade_defer/latest/niners_pick_inventory_review_rows.csv`
- `local_exports/model_v4/startup_slot_simulator/latest/startup_slot_pick_zone_rows.csv`
- `local_exports/model_v4/rookie_pick_decision_lab/latest/pick_decision_rows.csv`
- `local_exports/model_v4/roster_opportunity_cost/latest/roster_opportunity_cost_rows.csv`
- `local_exports/model_v4/june15_decision_board/latest/june15_decision_board_review_rows.csv`

## Safety Rules Preserved

- No market, ADP, ranking, projection, mock draft, big-board, or consensus input was used.
- Missing baseline evidence was not converted to zero, average, or a synthetic value.
- The row remains review-only and cannot produce final draft, trade, cut, or roster recommendations.
- Candidate watchlist context can still be viewed, but not as an exact pick-equivalent calculation.

## Tests

Focused tests cover:

- Missing 5.04 baseline stays blank.
- 5.04 cannot create exact startup-slot, pick lab, trade/defer, or cut-equivalent math.
- UI display labels surface the manual-only status.
- Review-only and no-final-recommendation constraints remain intact.
