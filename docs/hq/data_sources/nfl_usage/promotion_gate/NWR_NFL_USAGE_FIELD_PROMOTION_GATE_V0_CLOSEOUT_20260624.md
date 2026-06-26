# NFL Usage Field Promotion Gate V0 Closeout

## Overall Verdict

YELLOW. The promotion gate is safe and complete, with display-only context approved for low-risk factual usage fields. Predictive model promotion is blocked because the gate lacks a committed multi-season leakage-safe usage panel for field-level ablation.

## Fields Approved For Display-Only Candidate/Context

- `offense_snaps`
- `offense_pct`
- `targets`
- `carries`
- `receptions`
- `touches`
- `opportunities`
- `rushing_yards`
- `receiving_yards`
- `receiving_air_yards`
- `receiving_yards_after_catch`
- `rushing_first_downs`
- `receiving_first_downs`

## Fields Blocked

- `true_routes_run`
- `true_tprr`
- `true_yprr`
- `ranks_projections_adp_market_vendor_values`

## Fields Research-Only

- `ngs_efficiency_fields`
- `participation_personnel_formation_context`
- `route_participation_proxy`
- `tprr_like_proxy`
- `yprr_like_proxy`
- `ftn_pfr_advanced_fields`

## Predictive Backtest Status

BACKTEST_BLOCKED_INSUFFICIENT_COVERAGE. Predictive backtest was not run.

## Backtest Blockers

- Approved targets are limited/conditional and local-only in prior Backtest V0 outputs.
- This lane has field summaries and 2024 live smoke, not a full historical usage feature panel.

## Model Candidate Status

No active model candidates. All model-candidate concepts remain future/manual-review only.

## App Wiring Status

No decision-page wiring. Optional hidden review page display remains read-only.

## Model Input Status

No. Every promotion artifact keeps `model_input_allowed=no`.

## Raw Data Tracked Status

No raw nflverse/shared/local/runtime payloads are tracked.

## Files Changed

- `docs\hq\data_sources\nfl_usage\promotion_gate\NWR_NFL_USAGE_FIELD_PROMOTION_GATE_V0_MASTER_PLAN_20260624.md`
- `docs\hq\data_sources\nfl_usage\promotion_gate\NWR_NFL_USAGE_PROMOTION_GATE_BACKLOG_20260624.csv`
- `docs\hq\data_sources\nfl_usage\promotion_gate\nfl_usage_field_candidate_classification_v0.csv`
- `docs\hq\data_sources\nfl_usage\promotion_gate\NWR_NFL_USAGE_FIELD_CANDIDATE_CLASSIFICATION_20260624.md`
- `docs\hq\data_sources\nfl_usage\promotion_gate\nfl_usage_backtest_target_label_audit_v0.csv`
- `docs\hq\data_sources\nfl_usage\promotion_gate\NWR_NFL_USAGE_BACKTEST_TARGET_LABEL_AUDIT_20260624.md`
- `docs\hq\data_sources\nfl_usage\promotion_gate\NWR_NFL_USAGE_FEATURE_WINDOW_AND_LEAKAGE_POLICY_20260624.md`
- `docs\hq\data_sources\nfl_usage\promotion_gate\nfl_usage_feature_window_matrix_v0.csv`
- `docs\hq\data_sources\nfl_usage\promotion_gate\nfl_usage_backtest_results_v0.csv`
- `docs\hq\data_sources\nfl_usage\promotion_gate\nfl_usage_coverage_diagnostics_v0.csv`
- `docs\hq\data_sources\nfl_usage\promotion_gate\nfl_usage_leakage_diagnostics_v0.csv`
- `docs\hq\data_sources\nfl_usage\promotion_gate\nfl_usage_display_context_sanity_v0.csv`
- `docs\hq\data_sources\nfl_usage\promotion_gate\NWR_NFL_USAGE_BACKTEST_OR_FALLBACK_RESULTS_20260624.md`
- `docs\hq\data_sources\nfl_usage\promotion_gate\nfl_usage_field_promotion_decision_matrix_v0.csv`
- `docs\hq\data_sources\nfl_usage\promotion_gate\NWR_NFL_USAGE_FIELD_PROMOTION_DECISION_MATRIX_20260624.md`
- `docs\hq\data_sources\nfl_usage\promotion_gate\NWR_NFL_USAGE_FIELD_PROMOTION_GATE_V0_CLOSEOUT_20260624.md`

## Tests And Checks

- Focused pytest: `tests/test_nfl_usage_promotion_backtest_service.py`
  and `tests/test_nfl_usage_evidence_review_page.py` passed, 7 tests.
- Ruff passed on touched Python files.
- Python compile passed on touched Python files.
- CSV load/schema validation passed for all promotion gate CSVs.
- All CSV rows with `model_input_allowed` and `app_wiring_allowed` keep `no`.
- Browser smoke passed on `/nfl-usage-evidence-review` after selecting
  `Promotion Gate`, plus `/drafting-mode`, `/rankings`, and
  `/settings-data-health`; no traceback text observed.
- `git diff --check` passed.
- No raw/shared/local/runtime paths tracked by guardrail scan.
- No CFBD/college/rookie paths changed.
- Frozen Final Draft Board V1 remains 66 rows.
- Pinned manifest hash remains
  `5780156F09FBDA61FB906715C7341DB1B6D320C8D8EFA588070F19C4C50F45CE`.
- No `latest_candidate`, `latest_approved`, frozen board, pinned, or
  source-truth paths changed.

## Commits

Pending at closeout document generation.

## Push Status

Pending at closeout document generation.

## Final Git Status

Pending final commit/push.

## Recommended Next Step

Build a separate historical usage panel lane that writes raw data only to ignored shared cache and commits only schema fingerprints, coverage summaries, target manifests, and ablation reports.
