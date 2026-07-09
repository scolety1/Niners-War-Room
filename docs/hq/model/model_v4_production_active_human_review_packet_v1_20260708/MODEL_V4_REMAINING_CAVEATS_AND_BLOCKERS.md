# Model v4 Remaining Caveats And Blockers

## Highest Priority Blockers

1. The board remains stamped `candidate_review_only_not_active_rankings`.

2. No production-active formula approval or promotion receipt exists.

3. Exact historical replay remains blocked because season-by-season Model v4 component receipts and sidecars do not exist.

4. The Production Rankings Backtest V1 result remains a cold-water caveat: the review-only current-formula-family proxy had signal, but did not beat the simple prior-year finish baseline overall.

5. `shadow_model_v2_metrics.csv` remains missing. It is not needed for exact current-board hash rebuild, but remains a blocker if a future shadow/guardrail historical replay lane requires it.

6. The exact original `veteran_player_inputs.csv` age sidecar remains absent. The review-safe QB age adapter reproduced the pinned board exactly, but it is not a source promotion.

7. Source gates remain unchanged. Review-only, display-only, blocked, identity-unsafe, leakage-unsafe, or current-only fields cannot be treated as production inputs without a separate gate.

8. Future historical replay must use decision-date-safe inputs only. Current roster, injury, depth, market, source coverage, lifecycle, and confidence context cannot be reused for historical seasons without as-of receipts.

## Explicit Non-Promotion Statement

This packet does not approve the board for production-active use. It only packages the evidence needed for a human decision. No formula weights, ranking outputs, source statuses, app labels, default sorts, hidden sorts, recommendations, trade logic, draft logic, or app behavior changed.
