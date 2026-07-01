# Point-In-Time / As-Of Rules Summary

Verdict: `GREEN_REVIEW_ONLY_LAGGED_USAGE_ASOF_RULES_READY`

This packet defines rules for a future review-only Core Usage Review Dataset V1 builder. It does not approve production model use, training, source truth, probabilities, rankings, hidden sort, recommendations, app wiring, or current-player activation.

## Key Principle

Season N final factual usage may be used for target season N+1 only if the feature timestamp/as-of rule proves it would have been known after season N ended and before the N+1 prediction anchor.

Display-safe context is not automatically historical-feature-safe. Current display artifacts, current roster context, and current schedule/injury/depth context must stay out of historical replay unless a later packet proves point-in-time availability.

## As-Of Ready For Future Review-Only Construction

These families may proceed to a review-only dataset builder if the builder preserves season N to season N+1 lagging, source receipts, nulls, and closed approval flags:

- Season-level factual usage aggregates.
- Weekly factual usage aggregated only through completed season N.
- Typed red-zone opportunities after source semantics and coverage checks.
- Snap/share aggregates after denominator validation.
- Draft/combine static context when the event date is before the N+1 anchor.

## Excluded Current-Only Families

These are not allowed as historical feature fields without separate point-in-time proof:

- Current roster/status/availability context.
- Current schedule, next game, opponent, bye, or game-week context.
- Current injury/practice context.
- Depth chart context.
- Routes, TPRR, and YPRR unless a rights-cleared approved upload already exists.

## Strategy Alignment

- Do not block this phase on full fantasy scoring parity.
- Do not block this phase on return touchdown subtype.
- Treat red-zone as source-admit / coverage-audit, not categorically unavailable.
- `rec_rz_tgt`, `rush_rz_att`, and `pass_rz_att` are candidate mappings if coverage and semantics are proven.
- `rz_att` remains unresolved unless player/team/component semantics are proven.
- PBP-derived red-zone counts using `yardline_100 <= 20` are acceptable as review-only validation/fallback artifacts.
- Preserve nulls. Missing is not zero unless source semantics prove explicit zero.
