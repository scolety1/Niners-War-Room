# Parity Rerun Handoff

Recommended next lane: `NFLVerse Full Scoring Parity Rerun With Zero Eligibility V1`

Use these tracked inputs:

- Observed-row full scoring sidecar: `docs/hq/outcomes/nflverse_observed_row_full_scoring_sidecar_builder_v1_20260630/observed_row_full_scoring_sidecar_artifact.csv`
- Outcome row-level label source: `docs/hq/outcomes/outcome_row_level_label_source_admission_v1_20260630/compact_outcome_row_level_label_source.csv`
- Zero eligibility matrix: `docs/hq/data_sources/nflverse_player_week_zero_eligibility_resolver_v1_20260630/player_week_zero_eligibility_matrix.csv`
- Parity subset: `docs/hq/data_sources/nflverse_player_week_zero_eligibility_resolver_v1_20260630/player_week_zero_eligibility_parity_subset.csv`

## Allowed Rows

For parity review, use rows where:

- `identity_status=SAFE_NOW_DISPLAY_ONLY`
- `stats_source_coverage_status=COVERAGE_PRESENT`
- `zero_eligibility_status` is one of `OBSERVED_NONZERO_STATS`, `OBSERVED_EXPLICIT_ZERO_STATS`, or `ROSTERED_ACTIVE_NO_STATS_SAFE_ZERO`

## Still Blocked

- Direct return touchdown field exists: `false`
- Do not use `special_teams_tds` as return touchdowns.
- Do not convert `NOT_ENOUGH_INFORMATION`, `IDENTITY_GATED`, `SOURCE_DATA_MISSING`, `BYE_WEEK_NOT_ZERO`, `INJURY_OUT_NOT_ZERO`, `ROSTERED_INACTIVE_NOT_ZERO`, or `NOT_ROSTERED_NOT_APPLICABLE` rows to zero.
- Keep every row review-only and all approval flags false.
