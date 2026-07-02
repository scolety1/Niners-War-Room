# Data Sources Used

All sources are tracked repo artifacts or existing app status services. No raw shared/cache/local exports are read or tracked by this lane.

## Tracked Artifact Inputs

- `docs/hq/data_sources/nflverse_core_usage_review_dataset_v1_20260701/`
- `docs/hq/data_sources/nflverse_refresh_health_20260630/`
- `docs/hq/data_sources/nflverse_dataset_level_refresh_health_20260630/`
- `docs/hq/experiments/historical_tuning_substrate_expansion_v3_source_semantics_audit_20260701/`
- `docs/hq/experiments/historical_tuning_source_contract_v1_20260701/`
- `docs/hq/experiments/historical_formula_candidate_search_v1_20260701/`
- `docs/hq/experiments/historical_formula_candidate_review_v1_20260701/`
- `docs/hq/experiments/historical_formula_candidate_promotion_gate_prep_v1_20260701/`
- `docs/hq/experiments/historical_formula_candidate_risk_rescue_sprint_v1_20260701/`
- `docs/hq/experiments/historical_formula_candidate_cutline_safe_refinement_v1_20260701/`
- `docs/hq/experiments/historical_formula_candidate_targeted_redesign_v1_20260701/`
- `docs/hq/experiments/historical_formula_candidate_shadow_review_gate_v1_20260701/`
- `docs/hq/development_lab/development_lab_review_upgrade_v1_20260701/`
- `docs/hq/evidence_review_hub/evidence_review_hub_v1_20260701/`

## Existing Runtime Status Inputs

The existing Data Health page still uses its prior dashboard service for board, market, refresh, runtime, evidence, missing-data, and guardrail status. This upgrade adds review-only artifact summaries above those existing sections and does not mutate loader behavior.
