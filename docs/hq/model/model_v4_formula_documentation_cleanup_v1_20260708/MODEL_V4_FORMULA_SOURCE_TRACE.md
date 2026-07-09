# Model v4 Formula Source Trace

Date: 2026-07-08

## Prior Artifacts Verified

### Production Rankings Backtest V1

Worktree:

`C:\NWR\Niners-War-Room-production-rankings-backtest-v1-20260708`

Commit verified:

`2b9710d176d529304a04ef7c5102787183efcf59`

Packet path:

`C:\NWR\Niners-War-Room-production-rankings-backtest-v1-20260708\docs\hq\model\production_rankings_backtest_v1_20260708`

Files used:

- `PRODUCTION_RANKINGS_BACKTEST_V1_REPORT.md`
- `PRODUCTION_RANKINGS_BACKTEST_V1_SCORECARD.csv`
- `PRODUCTION_RANKINGS_BACKTEST_V1_CAVEATS.md`
- `PRODUCTION_RANKINGS_BACKTEST_V1_SOURCE_TRACE.md`
- `build_production_rankings_backtest_v1.py`

Relevant findings:

- Verdict: `YELLOW_PRODUCTION_RANKINGS_ACCURACY_PARTIAL_WITH_CAVEATS`
- Current-formula-family proxy did not beat simple prior-year finish overall.
- Backtest was a proxy, not exact Model v4 historical replay.
- Current app board was traced to the hash-pinned current artifact, but exact replay was blocked by absent current component receipts and missing historical decision-date receipts.

### Historical Model v4 Replay Substrate V1

Worktree:

`C:\NWR\Niners-War-Room-historical-model-v4-replay-substrate-v1-20260708`

Commit verified:

`75b9805b64841d8b6c4e1b4e66ba7d324278e83f`

Packet path:

`C:\NWR\Niners-War-Room-historical-model-v4-replay-substrate-v1-20260708\docs\hq\model\historical_model_v4_replay_substrate_v1_20260708`

Files used:

- `HISTORICAL_MODEL_V4_REPLAY_SUBSTRATE_V1_REPORT.md`
- `MODEL_V4_FORMULA_COMPONENT_SOURCE_MAP.csv`
- `MODEL_V4_HISTORICAL_REPLAY_AVAILABILITY_MATRIX.csv`
- `MODEL_V4_REPLAY_BLOCKERS.md`
- `MODEL_V4_REPLAY_CONTRACT.md`
- `MODEL_V4_REPLAY_SOURCE_TRACE.md`
- `build_historical_model_v4_replay_substrate_v1.py`

Relevant findings:

- Verdict: `YELLOW_MODEL_V4_HISTORICAL_REPLAY_SUBSTRATE_PARTIAL_WITH_BLOCKERS`
- Exact replay rows: 0.
- Current displayed Full Dynasty board is stamped `candidate_review_only_not_active_rankings`.
- Historical proxy substrate exists, but it is not exact Model v4 score replay.
- Historical season-by-season Model v4 component receipts do not exist locally.

## Current Runtime Artifact

Primary board artifact inspected:

`C:\NWR\Niners-War-Room\local_exports\model_v4\current_value\latest\full_player_board_value_review_rows.csv`

Observed facts:

- Rows: 240.
- `allowed_use`: `candidate_review_only_not_active_rankings` for all rows.
- `candidate_mode`: `wr_qb_v2_candidate` for all rows.
- `score_status`: 232 scored, 8 not scored.
- Scored-row `model_version`: `model_v4_wr_qb_v2_old_pocket_qb_guardrail`.
- Unscored/fallback `model_version`: `model_v4_full_player_board_value_0.1.0`.
- `source_column`: `nwr_dynasty_score`.
- Scored-row `upstream_source_column`: `checkpoint_review_score`.
- Named upstream source file: `local_exports\model_v4\current_value\latest\current_player_value_full_board_review_rows.csv`.

Runtime receipt finding:

- Only the final board artifact was found in the current runtime folder.
- Expected checkpoint/component/receipt files were absent.

## Current Code Files Read

- `app/pages/20_final_board_v1.py`
- `src/services/draft_day_app_v1_service.py`
- `src/services/full_player_board_value_service.py`
- `src/services/model_v4_wr_qb_v2_candidate_service.py`
- `src/services/model_v4_current_value_checkpoint_service.py`
- `src/services/model_v4_rb_wr_current_value_service.py`
- `src/services/model_v4_qb_te_current_value_service.py`
- `src/services/model_v4_replacement_vorp_core_service.py`
- `src/services/model_v4_lifecycle_archetype_service.py`
- `src/services/model_v4_confidence_missingness_service.py`

## Formula And Ranking Docs Read

- `docs/model_v4/PHASE_11A_FORMULA_CONTRACT.md`
- `docs/model_v4/MODEL_V4_FORMULA_CONFIG.json`
- `docs/hq/rankings/statistic_analysis_v0_20260630/statistic_analysis_design.md`
- `docs/hq/rankings/statistic_analysis_v0_20260630/blocked_or_deferred_items.md`
- `docs/hq/rankings/statistic_analysis_v0_20260630/preset_cleanup_summary.md`
- `docs/hq/rankings/statistic_analysis_v0_20260630/guardrail_report.md`
- `docs/hq/rankings_view_inventory_20260630/README.md`
- `docs/hq/rankings_view_inventory_20260630/rankings_data_sources_inventory.csv`
- `docs/hq/rankings_view_inventory_20260630/rankings_presets_inventory.csv`

## Evidence Conflicts Noted

Older rankings inventory described the current dynasty source as an approved ranking input. Newer direct artifact evidence and both prior model/backtest packets classify the displayed board as candidate review-only. This lane treats the row-level artifact stamp and current replay blocker reports as controlling until a human-approved promotion or app-label correction artifact is produced.

## Source Trace Limits

- This lane did not regenerate receipts.
- This lane did not run another benchmark.
- This lane did not tune formula weights.
- This lane did not inspect or modify dirty primary checkout files.
- This lane did not promote any source to model-use.
