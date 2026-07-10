# Model v4 Red Zone Leakage / As-Of Validation

Result: `PASS_PARTIAL_LAGGED_REVIEW_ONLY_WITH_CAVEATS`

The regenerated receipts use completed source-season red-zone facts. They are decision-date safe only when used as lagged season N factual inputs for season N+1 review-only analysis or as completed-season evidence. They are leakage-unsafe for same-season prediction, exact Model v4 replay, production scoring, or ranking integration without a separate approval lane.

The source sidecar covers 2024-2025 regular-season weeks 1-18. This does not prove 2013-2025 historical coverage.

Blocked uses: same-season prediction, production/model-use, training use, source-truth use, Formula Gauntlet tournaments, hidden sort, recommendation logic, rankings integration.
