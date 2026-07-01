# Guardrail Report

Verdict: `YELLOW_ZERO_ELIGIBILITY_PARTIAL_WITH_REMAINING_SOURCE_GAPS`

## Confirmed

- No raw/shared/cache files were copied into git.
- Local shared sources were read only when covered by tracked dataset/source policy and safe-runner receipts.
- `special_teams_tds` was not used as a return touchdown substitute.
- Missing player_stats rows were not converted to zero unless every safe-zero rule passed.
- Identity-gated rows have `safe_zero_allowed=false`.
- Source coverage missing rows have `safe_zero_allowed=false`.
- Bye, inactive, injury-out, and not-rostered rows have `safe_zero_allowed=false`.
- `label_truth_allowed=false` for every row.
- `model_use_allowed=false` for every row.
- `training_allowed=false` for every row.
- `source_truth_allowed=false` for every row.
