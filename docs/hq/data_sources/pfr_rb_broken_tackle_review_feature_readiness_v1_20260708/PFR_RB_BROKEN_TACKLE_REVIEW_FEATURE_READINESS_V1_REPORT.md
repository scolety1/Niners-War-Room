# PFR RB Broken Tackle Review Feature Readiness V1

Final verdict: `GREEN_PFR_RB_BROKEN_TACKLE_REVIEW_FEATURE_READY_FOR_GAUNTLET_DESIGN`

## What Survived

The RB broken-tackle evidence chain preserved two weak review-only variants:

- `pfr_rush_brk_tkl__raw`
- `pfr_rush_brk_tkl__per_game`

The locked shadow-feature lane found tiny positive full-control MAE deltas:

- raw: `+0.001531`
- per-game: `+0.000651`

That is enough to keep the hypothesis alive for a tightly bounded review-only
Formula Gauntlet design, but it is not enough for production, rankings, UI,
source-truth, or model approval.

## What Is Parked Or Blocked

`pfr_rush_brk_tkl__per_attempt` is diagnostic only and parked after the locked
full-control diagnostic result was negative. Z-score, rank, bottom-quartile,
above-median, and missingness variants remain parked or blocked.

This is not PFF Elusive Rating, not an elusive-rating replacement, and not
`nwr_elusive_proxy_review_only`.

## Future Feature Name

Allowed future review-only name:

`PFR_RB_BROKEN_TACKLE_CONTEXT_REVIEW_ONLY`

## Formula Gauntlet Readiness

A future Formula Gauntlet lane may test only RB rows, only safe PFR rushing bridge
rows, and only raw/per-game broken tackles as weak additive context. It must
include volume, prior production, coverage, historically valid age/draft capital
where available, season holdouts, matched cohorts, and outlier checks.

Promotion is impossible from that future lane alone.
