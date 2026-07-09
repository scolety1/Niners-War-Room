# Model v4 Label Correction Source Trace

## Base Verification

- Canonical remote: `origin/work/hq-parallel-control`.
- Expected and verified HQ HEAD: `e1c2359f492b03e35d0ba1853ffebaf8a011b232`.
- Fresh worktree: `C:\NWR\Niners-War-Room-model-v4-formula-app-label-correction-packet-v1-20260708`.
- Branch: `work/lane-model-v4-formula-app-label-correction-packet-v1-20260708`.
- Primary dirty DynastyProcess docs were not touched.

## Prior Commits Verified

- Exact rebuild commit: `1624202ebbc1a86c1d91da3397c2952d3c7f20f7`.
- Human review commit: `973302f738bf03f3ee10e00c00eb64ffd45ff135`.

## Prior Artifacts Read

- `C:\NWR\Niners-War-Room-current-board-deterministic-rebuild-with-recovery-inputs-v1-20260708\docs\hq\model\current_board_deterministic_rebuild_with_recovery_inputs_v1_20260708`
- `C:\NWR\Niners-War-Room-model-v4-production-active-human-review-packet-v1-20260708\docs\hq\model\model_v4_production_active_human_review_packet_v1_20260708`
- `C:\NWR\Niners-War-Room-model-v4-formula-documentation-cleanup-v1-20260708\docs\hq\model\model_v4_formula_documentation_cleanup_v1_20260708`
- `C:\NWR\Niners-War-Room-production-rankings-backtest-v1-20260708\docs\hq\model\production_rankings_backtest_v1_20260708`

## Repo Files Inspected

- `app/pages/20_final_board_v1.py`
- `src/services/draft_day_app_v1_service.py`
- `src/services/full_player_board_value_service.py`
- `src/services/model_v4_current_value_checkpoint_service.py`
- `src/services/model_v4_wr_qb_v2_candidate_service.py`
- `docs/hq/rankings/statistic_analysis_v0_20260630/statistic_analysis_design.md`
- `docs/hq/rankings/statistic_analysis_v0_20260630/statistic_analysis_column_inventory.csv`
- `docs/hq/rankings/statistic_analysis_v0_20260630/score_component_inventory.csv`
- `docs/hq/rankings/statistic_analysis_v0_20260630/blocked_or_deferred_items.md`

## Control Board Read-Only Facts

Read-only board path:

`C:\NWR\Niners-War-Room\local_exports\model_v4\current_value\latest\full_player_board_value_review_rows.csv`

Observed:

- Rows: `240`.
- SHA256: `263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4`.
- Position mix: `WR=93`, `RB=79`, `TE=32`, `QB=28`, `K=8`.
- `allowed_use`: `candidate_review_only_not_active_rankings`.
- `candidate_mode`: `wr_qb_v2_candidate`.
- `score_type`: `nwr_dynasty_score`.
- `candidate_model_version`: `model_v4_wr_qb_v2_old_pocket_qb_guardrail`.
- `blocked_use`: `do_not_use_as_final_trade_cut_keep_draft_buy_sell_defer_target_or_start_sit_recommendation`.

## Guardrails Preserved

- No app code edited.
- No labels changed in runtime files.
- No artifact status fields changed.
- No ranking output changed.
- No model weights changed.
- No source promoted.
- No benchmark run.
- No tuning run.
- No push or merge performed.
