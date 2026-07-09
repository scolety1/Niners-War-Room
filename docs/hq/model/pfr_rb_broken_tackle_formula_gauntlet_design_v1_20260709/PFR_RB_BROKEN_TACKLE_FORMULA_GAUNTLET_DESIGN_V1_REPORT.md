# PFR RB Broken Tackle Formula Gauntlet Design V1

Final verdict: `GREEN_PFR_RB_BROKEN_TACKLE_GAUNTLET_DESIGN_READY`

## Why This Lane Exists

The canonical readiness packet preserved `PFR_RB_BROKEN_TACKLE_CONTEXT_REVIEW_ONLY`
as a weak review-only context hypothesis. The prior locked test showed tiny
full-control lift:

- raw: `+0.001531`
- per-game: `+0.000651`

That evidence is not production-ready. This packet only defines how a future
review-only Formula Gauntlet may test the hypothesis without contaminating
production formulas, rankings, default sort, UI, source truth, or decision logic.

## What The Future Gauntlet May Test

The future Gauntlet may test RB-only safe PFR rushing rows for:

- `pfr_rush_brk_tkl__raw`
- `pfr_rush_brk_tkl__per_game`

`pfr_rush_brk_tkl__per_attempt` remains diagnostic only. Z-score, rank,
bottom-quartile, above-median, missingness, PFF-like, and elusive-rating style
variants remain blocked or parked.

## Required Design

The future Gauntlet must use source season N to target season N+1, season-based
walk-forward and leave-one-season-out splits, full controls for volume, prior
production and PFR coverage, and audits for matched cohorts, outliers,
threshold robustness, direction stability, missingness, low-games harm,
prior-production leakage, and future-info leakage.

## Promotion Wall

This design lane cannot promote the feature. A future Gauntlet also cannot
promote it by itself. Any future promotion discussion would require separate HQ
approval after Gauntlet results, model-owner review, source-governance approval,
guardrail review, a production integration lane, and a rollback plan.

The only possible positive future Gauntlet output is
`REVIEW_ONLY_FORMULA_GAUNTLET_SIGNAL`.
