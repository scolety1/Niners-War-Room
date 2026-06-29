# Rookie Draft Capital Review Artifact V1 Summary - 2026-06-29

## Gate B Result

`PARTIAL_DRAFT_CAPITAL_REVIEW_ARTIFACT`

A tracked review-only draft-capital artifact was created from tracked
display/review artifacts. Coverage is partial, so it is not source truth
and not usable for model/training gates.

## Coverage

- Approved Gate-A identity rows: 157
- Rows with tracked round/pick/team: 54
- Rows still missing draft capital: 103
- Rows approved for model use: 0
- Rows approved for training use: 0

## Data Quality Status

- MISSING_DRAFT_CAPITAL_REVIEW_REQUIRED: 103
- PARTIAL_REVIEW_ONLY_DRAFT_CAPITAL_AVAILABLE: 54

## Sources Audited

- Rookie HQ overlay display draft capital: PARTIAL_DRAFT_CAPITAL_REVIEW_ARTIFACT
- Rookie overlay source row count: source_context_only
- Documented 2026 draft-capital snapshot: not_used_processed_source_unavailable
- Historical rookie draft capital: blocked_missing_historical_draft_capital

## Stop/Continue Decision

Gate B is partial, so Gate C was retried as an audit only. Gate C blocks
because historical rookie labels are not available from approved sources.
