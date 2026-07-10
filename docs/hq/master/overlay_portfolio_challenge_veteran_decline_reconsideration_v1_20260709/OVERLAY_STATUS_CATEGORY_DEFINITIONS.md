# Overlay Status Category Definitions

This status system separates scoring-overlay status from review value. Not primary does not mean discarded.

## Categories

- `PRIMARY_REVIEW_ONLY_SCORING_OVERLAY`: the single strongest overlay candidate that may be preserved for future review-only scoring-overlay analysis. It is not production/model-use and does not justify ranking simulation.
- `SECONDARY_REVIEW_ONLY_SCORING_CANDIDATE`: a preserved candidate that may be compared in future review-only readiness gates but is not the primary overlay.
- `CONTEXT_GUARDRAIL_OVERLAY`: a useful miss-taxonomy or reviewer warning concept that should be preserved as context, not applied as scoring logic.
- `WARNING_ONLY_OVERLAY`: a caution flag useful for manual review, especially where score changes risk suppressing true rebounds or breakouts.
- `PARTIAL_WINDOW_ONLY_OVERLAY`: a candidate backed only by modern-window or partial-window data and blocked from full-history claims.
- `FUTURE_REFINEMENT_CANDIDATE`: a concept with enough evidence to revisit only if the user explicitly authorizes a bounded future design/refinement lane.
- `STOP_TESTING`: a tested overlay or variant family that should not receive more testing under the current evidence.
- `BLOCKED`: a concept relying on blocked sources, leakage-prone inputs, source-gate failures, or forbidden logic.

## Policy

Only `PRIMARY_REVIEW_ONLY_SCORING_OVERLAY` and explicitly preserved `SECONDARY_REVIEW_ONLY_SCORING_CANDIDATE` items may be carried as review-only scoring candidates. All other statuses may still matter for manual review, caveats, miss taxonomy, and future user-authorized work.

No category approves production/model-use, rankings integration, app/runtime behavior, hidden sort, recommendation logic, source promotion, canonical `local_exports` mutation, push, merge, or review-only ranking simulation.
