# Miss-Specific Overlay Conflict Policy

## Default Policy

Start with no stacking unless explicitly tested.

## Multiple Overlay Eligibility

A player may be eligible for multiple overlay families during analysis, but scoring overlays should not stack additively by default. The next test lane should record all eligible overlays and then apply one predeclared primary overlay according to priority.

## Positive vs Negative Overlay Conflicts

Positive breakout overlays should not automatically override negative trap overlays. Negative trap overlays should not automatically block positive overlays. When both are present, classify the case as `CONFLICT_REVIEW_ONLY` unless a future test predeclares a priority rule.

## Priority Order For Testing

For initial review-only tests, use this non-stacking priority:

1. Sparse-history / early-career role breakout benchmark
2. Availability rebound
3. Starter / depth-chart promotion
4. Snap-growth / role-promotion
5. Draft-capital-with-role
6. Low snap/depth warning
7. Injury / availability caveat
8. Veteran role-loss / prior-production trap
9. Partial-window expected opportunity
10. Position-specific overlays

## Context-Only Overlays

Veteran role-loss, injury/availability caveat, low snap/depth warning, and position-specific overlays remain context-only unless a future bounded test proves net miss reduction without unacceptable collateral damage.

## Partial-Window Overlays

Expected opportunity / NGS overlays are `PARTIAL_WINDOW_ONLY` unless full-history-safe coverage exists. They must never be used to claim a full-history plateau break.

## Never-Scoring Inputs

Current-only ADP, market data without as-of proof, same-season/future context, CFBD/prospect production without gates, inferred UDFA truth, SportsDataIO, PFF Elusive Rating, and `nwr_elusive_proxy_review_only` are never scoring overlay inputs in this lane.
