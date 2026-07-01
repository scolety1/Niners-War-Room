# Feature Availability Timeline

## Timeline

1. Season N games occur.
2. NFLVerse/Sleeper/NFL Usage factual usage sources publish or refresh season N rows.
3. Data Hygiene creates compact receipts and source coverage summaries.
4. Season N is closed for the selected scope.
5. Core Usage Review Dataset V1 aggregates only season N factual usage.
6. Dataset row receives a review-only as-of statement proving it is known before the N+1 prediction anchor.
7. Separate future gates may evaluate experiment readiness. This packet does not approve that step.

## Core Review Families

Build-ready for review-only construction after season-close/as-of checks:

- Targets.
- Carries.
- Receptions.
- Rushing yards.
- Receiving yards.
- Air yards.
- Yards after catch.
- First downs.
- Offense snaps.
- Snap share after denominator validation.
- Touches.
- Opportunities.
- Typed red-zone opportunities after semantics checks.

## Families That Need Separate Proof

- Current roster/status/availability context.
- Schedule/current opponent/bye context.
- Injury/practice context.
- Depth chart context.
- Routes, TPRR, YPRR.
- Ambiguous `rz_att`.

## Validation/Fallback

PBP-derived red-zone counts using `yardline_100 <= 20` may be used as review-only validation/fallback artifacts for typed red-zone opportunities. They are not production model approvals and must preserve source differences.
