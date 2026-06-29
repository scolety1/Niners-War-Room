# Rookie Draft Capital Review V1

Gate B result: `PARTIAL_DRAFT_CAPITAL_REVIEW_ARTIFACT`

This folder now contains a partial tracked, review-only draft-capital
artifact for Gate-A-approved CFBD rookie identities.

## Files

- `rookie_draft_capital_review_artifact_v1.csv`
- `ROOKIE_DRAFT_CAPITAL_REVIEW_ARTIFACT_V1_SUMMARY.md`
- `ROOKIE_DRAFT_CAPITAL_PROVENANCE_V1.md`
- `rookie_draft_capital_missingness_matrix_v1.csv`
- `rookie_draft_capital_source_audit_v1.csv`

## Counts

- Total approved identity rows: 157
- Rows with review-only draft capital: 54
- Rows missing draft capital: 103

## Guardrails

- All rows remain `review_only=true`.
- All rows remain `model_use_allowed=false`.
- All rows remain `training_allowed=false`.
- Missing data remains `Not enough information`, never `0%`.
