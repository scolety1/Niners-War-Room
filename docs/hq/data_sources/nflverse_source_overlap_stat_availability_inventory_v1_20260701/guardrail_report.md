# Guardrail Report

Verdict: `YELLOW_STAT_AVAILABILITY_INVENTORY_PARTIAL_SOURCE_GAPS`

## Confirmed

- No model use approved.
- No training use approved.
- No source truth approved.
- No label truth approved.
- No probabilities created.
- No rankings or app behavior changed.
- No raw/shared/cache/local/private/secret files tracked.
- Local approved NFLVerse snapshot files were read only for schema and aggregate coverage inventory.
- Market, ADP, FantasyPros, DynastyProcess, imported fantasy totals, and vendor/private fields remain blocked or display/context only.
- Missing values remain `Not enough information` and are not converted to zero, healthy, clean, no-role, or low-risk.

Every CSV row has `model_use_allowed=false`, `training_allowed=false`, and `source_truth_allowed=false`.
