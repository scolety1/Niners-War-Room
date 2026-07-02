# Data Sources Used

Only tracked repo artifacts were used. No raw `C:\NWR_SHARED_DATA`, shared-cache, local export, or secret files are read by the page or service.

## Core Usage Dataset V1

- Root: `docs/hq/data_sources/nflverse_core_usage_review_dataset_v1_20260701/`
- Summary: `core_usage_review_dataset_summary.md`
- Row counts: `nwr_nflverse_usage_row_count_report_v1.csv`
- Schema: `nwr_nflverse_usage_review_dataset_schema_v1.csv`
- Rows displayed in summary: `76804`
- Seasons displayed: `2024;2025`
- Week range displayed in docs: `1 to 22`
- Fields displayed in summary: `40`
- Use: review-only/manual display

## Red-Zone Sidecar

- Root: `docs/hq/data_sources/nflverse_core_usage_review_dataset_v1_20260701/`
- Decision: `nwr_redzone_sidecar_decision_v1.md`
- Sidecar artifact: `nwr_player_week_redzone_sidecar_v1.parquet`
- Rows displayed in summary: `6424`
- Use: sidecar-only context with semantics caveats
- Blocked: ambiguous `rz_att`

## Historical Tuning V3 Substrate

- Root: `docs/hq/experiments/historical_tuning_substrate_expansion_v3_source_semantics_audit_20260701/`
- Row counts: `feature_target_row_count_report_v3.csv`
- Safe allowlist: `safe_feature_allowlist_v3.csv`
- Rows displayed in summary: `5518`
- Feature seasons: `2012` through `2024`
- Target seasons: `2013` through `2025`
- Use: review-only/manual display

## Source Contract V1

- Root: `docs/hq/experiments/historical_tuning_source_contract_v1_20260701/`
- Allowed feature contract: `allowed_review_only_feature_contract_v1.csv`
- Null-fenced contract: `null_fenced_feature_contract_v1.csv`
- Blocked feature contract: `blocked_feature_contract_v1.csv`
- Displayed contract counts: `18 allowed / 4 null-fenced / 11 blocked`
- Use: review-only contract display; formula tuning not ready

## Candidate Evidence Packets

- Search: `docs/hq/experiments/historical_formula_candidate_search_v1_20260701/`
- Review: `docs/hq/experiments/historical_formula_candidate_review_v1_20260701/`
- Promotion gate prep: `docs/hq/experiments/historical_formula_candidate_promotion_gate_prep_v1_20260701/`
- Risk rescue: `docs/hq/experiments/historical_formula_candidate_risk_rescue_sprint_v1_20260701/`
- Cutline refinement: `docs/hq/experiments/historical_formula_candidate_cutline_safe_refinement_v1_20260701/`
- Targeted redesign: `docs/hq/experiments/historical_formula_candidate_targeted_redesign_v1_20260701/`
- Displayed current candidate: `usage_opportunity_volume`
- Displayed variants: `qb_guard_soft_blend`, `rb_wr_cutline_safe_blend`, `wr_boundary_breakout_sensitivity_guard`
- Displayed status: `HOLD`
