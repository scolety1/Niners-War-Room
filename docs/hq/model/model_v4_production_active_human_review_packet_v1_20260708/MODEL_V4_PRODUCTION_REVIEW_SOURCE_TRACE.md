# Model v4 Production Review Source Trace

## Base Verification

- Prior expected HQ HEAD: `4aced300c917d952ae08afcaf927268402423834`.
- Current remote HQ HEAD used for this packet: `e1c2359f492b03e35d0ba1853ffebaf8a011b232`.
- Remote movement from `4aced300c917d952ae08afcaf927268402423834` to `e1c2359f492b03e35d0ba1853ffebaf8a011b232` was inspected.
- The new commit was docs-only HQ1 source receipt-chain standard work under `docs/hq/deep_research_upgrades/`.
- No protected formula, ranking, app/runtime, source-gate, current-board build, or `local_exports` path was touched by the remote movement.
- Fresh worktree path: `C:\NWR\Niners-War-Room-model-v4-production-active-human-review-packet-v1-20260708`.
- Primary checkout dirty DynastyProcess docs were not touched.

## Prior Artifacts Read

- `C:\NWR\Niners-War-Room-production-rankings-backtest-v1-20260708\docs\hq\model\production_rankings_backtest_v1_20260708`
- `C:\NWR\Niners-War-Room-historical-model-v4-replay-substrate-v1-20260708\docs\hq\model\historical_model_v4_replay_substrate_v1_20260708`
- `C:\NWR\Niners-War-Room-model-v4-formula-documentation-cleanup-v1-20260708\docs\hq\model\model_v4_formula_documentation_cleanup_v1_20260708`
- `C:\NWR\Niners-War-Room-model-v4-component-receipt-backfill-v1-20260708\docs\hq\model\model_v4_component_receipt_backfill_v1_20260708`
- `C:\NWR\Niners-War-Room-current-board-deterministic-rebuild-with-recovery-inputs-v1-20260708\docs\hq\model\current_board_deterministic_rebuild_with_recovery_inputs_v1_20260708`

## Prior Commits Verified

- Exact rebuild commit verified: `1624202ebbc1a86c1d91da3397c2952d3c7f20f7`.

## Evidence Facts Preserved

- Exact current-board rebuild verdict: `GREEN_CURRENT_BOARD_DETERMINISTIC_REBUILD_EXACT_MATCH`.
- Rebuilt board hash: `263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4`.
- Pinned final board hash: `263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4`.
- Rows reconciled: `240 / 240`.
- Unique player IDs reconciled: `240 / 240`.
- Position mix: `WR=93`, `RB=79`, `TE=32`, `QB=28`, `K=8`.
- Field diffs: `0`.
- `checkpoint_review_score`: `232` matches / `0` mismatches.
- `nwr_dynasty_score`: `0` field diffs.
- `shadow_model_v2_metrics.csv`: not required for current-board hash rebuild.
- Exact original `veteran_player_inputs.csv`: absent; review-safe QB age adapter from recovered lifecycle receipt rows reproduced the board exactly.
- Current status: `candidate_review_only_main_display`.
- Row-level stamp: `candidate_review_only_not_active_rankings`.
- Candidate mode: `wr_qb_v2_candidate`.

## Cold-Water Accuracy Facts Preserved

- Production Rankings Backtest V1 verdict: `YELLOW_PRODUCTION_RANKINGS_ACCURACY_PARTIAL_WITH_CAVEATS`.
- Current-formula-family partial proxy result: rank MAE `21.65`, Spearman `0.675`, startable precision `58.3%`.
- Simple prior-year finish baseline result on the same row set: rank MAE `21.39`, Spearman `0.681`, startable precision `58.4%`.
- Interpretation: exact rebuild proves reproducibility, not superiority over the prior-year baseline.

## Guardrails Preserved

- No board promotion.
- No source promotion.
- No ranking output change.
- No model weight change.
- No app behavior change.
- No app-label change.
- No benchmark or tuning run.
- No canonical `local_exports` write.
- No push or canonical HQ merge performed.
