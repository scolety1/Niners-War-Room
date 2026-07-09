# Model v4 Replay Blockers

## Verdict

`EXACT_MODEL_V4_REPLAY_BLOCKED`

## Ranked Blockers

1. The current board artifact is stamped `candidate_review_only_not_active_rankings`,
   so the displayed Full Dynasty board is not an approved production-accuracy target.
2. The canonical runtime folder contains the final board CSV but not the upstream
   current checkpoint/component receipt files required to replay `nwr_dynasty_score`.
3. Historical season-by-season Model v4 component rows do not exist for the current
   component names and source receipts.
4. Route/TPRR/YPRR/red-zone/stats-first component evidence is not historically
   available and admitted with decision-date receipts for all positions.
5. Lifecycle, role archetype, age, confidence cap, and warning flag layers are
   current-state dependent and are not historically reproducible from V3.
6. The WR/QB v2 candidate overlay depends on current component rows, current age
   sidecars, and historical shadow metrics; it is review-only and cannot be replayed
   as production.
7. Rookie/first-NFL-season players are structurally missing from the V3 prior-season
   veteran substrate.
8. Advanced metrics remain display-only, review-only, identity unsafe, or blocked
   under current gates and must not be used to fill formula gaps.

## Safe Partial Substrate

The generated partial panel preserves component names and uses only V3 lagged factual
overlap with source/governance caveats. It is not a score replay, not training data,
not source truth, and not production accuracy.
