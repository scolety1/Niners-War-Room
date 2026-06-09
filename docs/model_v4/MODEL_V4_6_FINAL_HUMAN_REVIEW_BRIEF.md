# Model v4.6 Final Human Review Brief

## Status

Model v4.6 is ready for human final decision review as a review-only system.

The latest audit found no critical blockers. The v4.6 patches only improved usability and audit clarity: guided review paths, one-row Evidence Risk summaries, cleaner pick-equivalent fields, and a warning-code dictionary.

## Review First

1. Draft Room -> Internal Slot
   Compare rookies, picks, roster players, and context assets on the model's own value scale.

2. Draft Room -> Pick Decision Lab
   Review 1.03, 1.04, 2.04, 2.08, and the manual-only 5.04 row.

3. Draft Room -> Prospect Board
   Check production, College Team Share, NFL Draft Pick Signal, Trust, and warning groups.

4. Draft Room -> Why This Rank
   Open this when a player looks too high, too low, or weird.

5. Draft Room -> Evidence & Risk
   Use the player summary first. Raw module rows remain available for receipts.

6. June 15 Review -> Top-Five Drop Decision
   Confirm the special deadline slot before normal roster-pressure thinking.

7. June 15 Review -> Cut Cost
   Review what model value would leave the roster if a player is dropped.

## Surfaces To Trust Most

- Internal Slot: best cross-asset value view.
- Pick Decision Lab: best owned-pick review view.
- Prospect Board: best rookie component view.
- Cut Cost: best roster deadline opportunity-cost view.
- Why This Rank: best plain-English explanation layer.

These are still review tools, not instructions.

## Context-Only Surfaces

- Historical Comps
- Outcome Buckets
- Model Edges
- Evidence Risk
- Warning Dictionary
- Receipts / Warnings
- Trade and defer context

These explain uncertainty and opportunity cost. They do not feed final decisions by themselves.

## Known Cautions

- 2026 5.04 is `manual_only_no_exact_model_baseline`; no exact model equivalent exists.
- High Evidence Risk means inspect receipts before trusting the score.
- Model Edge rows are not bugs by default; decide whether the edge is real or source-driven.
- No-premium TE and 1QB QB discipline are intentional format constraints.
- Weird rookie rankings should be reviewed through production, draft signal, landing context, and source risk.
- Raw warning codes are preserved for audit; use the warning dictionary for plain-English decoding.

## Specific Attention List

- 5.04: manual-only, no exact pick baseline.
- Top-five drop slot: review before normal cut logic.
- Skyler Bell-style profiles: high production with weak draft signal needs manual scouting.
- Carnell Tate-style profiles: strong draft signal with weaker college share needs context review.
- TEs near RB/WR values: confirm no-premium discipline.
- QBs near early rookie zones: confirm 1QB replacement discipline.
- Any red/manual Evidence Risk player: open receipts before relying on the row.

## Do Not Do From This Brief

- Do not treat any row as a final cut, keep, trade, defer, or draft recommendation.
- Do not promote outputs into active rankings.
- Do not mutate My Team, War Board, readiness gates, or app promotion.
- Do not use ADP, market ranks, projections, mocks, big boards, or consensus as private value.

## Helpful Files

- `local_exports/model_v4/final_human_review/latest/final_human_review_checklist.csv`
- `local_exports/model_v4/rookie_pick_decision_lab/latest/pick_decision_rows.csv`
- `local_exports/model_v4/roster_opportunity_cost/latest/roster_opportunity_cost_rows.csv`
- `local_exports/model_v4/source_risk_heatmap/latest/source_risk_player_summary_rows.csv`
- `local_exports/model_v4/warning_dictionary/latest/warning_code_dictionary.csv`
- `docs/model_v4/MODEL_V4_6_WARNING_CODE_DICTIONARY.md`

## Bottom Line

Use Model v4.6 tonight as a decision-review workbench. It is ready to inspect, but the final calls still belong to the human reviewer.
