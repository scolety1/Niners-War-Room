# Small Formula Pilot Stop Conditions

The future pilot must stop if any of these conditions occur:

- The Formula Data Mart cannot be assembled from review-safe inputs.
- The PYF baseline cannot be reproduced.
- Leakage/as-of checks fail.
- Source/use-gate status is ambiguous or blocked for a candidate input.
- Role archetype is used as a direct production-like boost, penalty, formula weight, hidden sort, or ranking input.
- Age/lifecycle is used as a direct production-like boost, penalty, formula weight, hidden sort, or ranking input.
- Confidence cap is used as a formula feature instead of caution/coverage context.
- Candidate formulas require blocked inputs.
- Candidate formulas require current/future-only data.
- Candidate formulas require optimized weights.
- Candidate formulas require route/YPRR/TPRR, return scoring, broad PFR, PFF Elusive Rating, or `nwr_elusive_proxy_review_only`.
- Metrics cannot be calculated consistently by position.
- Outputs would imply production use, ranking integration, source promotion, or production accuracy.

If any stop condition is triggered, the future lane must report the blocker and preserve all current gates.
