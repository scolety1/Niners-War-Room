# QB/TE Shadow Formula Candidate Handoff - 2026-06-09

## What Ran
A shadow-only QB/TE experiment compared three candidate variants against the current full-board Rankings baseline.

## What Changed Only In Shadow Outputs
- QB/TE candidate scores and ranks under the formula-candidate experiment folder.
- Movement, distribution, My Team, and suspicious-row readbacks.

## What Did Not Change
- Active Rankings baseline files.
- Production formula files.
- Decision Board.
- Active data packs.
- Market/league/display-only source routing.

## Variant List
- `qb_1qb_spread_compression_v1`
- `te_no_premium_ceiling_v1`
- `qb_te_context_balance_v1`

## Guardrails
- Baseline hashes unchanged: True
- Sentinels safe: True
- Contamination safe: True

## Top Concerns
- QB 1QB compression still needs human judgment because improving top-QB dominance can also lift low-QB rows.
- TE no-premium ceiling behavior changes top TE placement but may create rank displacement that needs RB/WR review.
- No variant should be promoted without a separate controlled formula patch and fresh external audit.

## Best-Looking Candidate
`qb_te_context_balance_v1` is the best-looking human-review-only candidate because it tests both QB and TE context together while leaving RB/WR scores unchanged.

## Worst-Breaking Candidate
`qb_1qb_spread_compression_v1` leaves the most top-heavy QB/TE pressure in the top 25 and should be inspected carefully.

## Inspect First
- `docs/model_v4/QB_TE_SHADOW_FORMULA_CANDIDATE_RESULTS_20260609.md`
- `local_exports/model_v4/formula_candidates/qb_te_shadow_20260609/shadow_suspicious_rows_qb_te_context_balance_v1.csv`

## Decision Board
Decision Board remains blocked.

## Recommended Next Task
Human-review the shadow results, then choose one candidate lane for a source-preserving, test-gated production proposal. Do not promote directly from this experiment.
