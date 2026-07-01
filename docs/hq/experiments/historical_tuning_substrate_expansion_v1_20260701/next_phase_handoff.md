# Next Phase Handoff

## Handoff Recommendation

Do not run another formula search next. Run Historical Tuning Substrate Expansion V2.

## V2 Goals

- Restore or install the approved local-only nflverse runtime required by the existing safe builder.
- Regenerate older safe season-level feature rows where source coverage permits.
- Join older features to Outcome V2 target labels without name-matching ambiguous players.
- Keep GSIS/nflverse IDs canonical and Sleeper IDs crosswalk-only.
- Preserve missingness semantics instead of forcing missing values to zero.
- Re-run leakage, forbidden-field, and source-governance checks before any tuning discussion.

## V1 Output To Reuse

- Canonical schema: `feature_target_substrate_schema_v1.csv`
- Full review-only substrate: `nwr_historical_tuning_feature_target_substrate_v1.parquet`
- Coverage reports: row counts, season/position, feature, target, and identity join reports
