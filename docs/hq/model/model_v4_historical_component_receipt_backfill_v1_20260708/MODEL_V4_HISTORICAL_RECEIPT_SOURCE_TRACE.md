# Model v4 Historical Receipt Source Trace

## Primary Sources

| Source | Path | Use |
| --- | --- | --- |
| Exact current-board rebuild packet | `C:\NWR\Niners-War-Room-current-board-deterministic-rebuild-with-recovery-inputs-v1-20260708\docs\hq\model\current_board_deterministic_rebuild_with_recovery_inputs_v1_20260708` | Current receipt chain and exact current-board proof. |
| Formula documentation / cleanup packet | `C:\NWR\Niners-War-Room-model-v4-formula-documentation-cleanup-v1-20260708\docs\hq\model\model_v4_formula_documentation_cleanup_v1_20260708` | Current component registry and replay blockers. |
| Historical Model v4 replay substrate | `C:\NWR\Niners-War-Room-historical-model-v4-replay-substrate-v1-20260708\docs\hq\model\historical_model_v4_replay_substrate_v1_20260708` | Component source map, partial replay panel, and availability matrix. |
| Production Rankings Backtest V1 | `C:\NWR\Niners-War-Room-production-rankings-backtest-v1-20260708\docs\hq\model\production_rankings_backtest_v1_20260708` | Accuracy caveat and prior-year baseline comparison context. |
| Model v4 human review packet | `C:\NWR\Niners-War-Room-model-v4-production-active-human-review-packet-v1-20260708\docs\hq\model\model_v4_production_active_human_review_packet_v1_20260708` | Production-active consideration caveats. |
| Label correction packet | `C:\NWR\Niners-War-Room-model-v4-formula-app-label-correction-packet-v1-20260708\docs\hq\model\model_v4_formula_app_label_correction_packet_v1_20260708` | Canonical board label/status taxonomy. |
| App-visible label implementation | `C:\NWR\Niners-War-Room-model-v4-app-visible-label-correction-v1-20260708\docs\hq\model\model_v4_app_visible_label_correction_v1_20260708` | Confirmed current app label is display-only and review-safe. |

## Historical Panel

- Panel: `C:\NWR\Niners-War-Room-historical-model-v4-replay-substrate-v1-20260708\docs\hq\model\historical_model_v4_replay_substrate_v1_20260708\MODEL_V4_PARTIAL_REPLAY_INPUT_PANEL_REVIEW_ONLY.csv`
- Receipt CSV source alias: `MODEL_V4_PARTIAL_REPLAY_INPUT_PANEL_REVIEW_ONLY.csv`
- Receipt pointer alias: `v3_source_semantics_substrate_parquet`
- Receipt pointer full path: `docs/hq/experiments/historical_tuning_substrate_expansion_v3_source_semantics_audit_20260701/nwr_historical_tuning_feature_target_substrate_v3.parquet`
- SHA256: `dd5897cd215f501af57d9d30ab27020d981ae8da505eb05245c5f992a7fea44a`
- Rows: `5518`
- Status: `review_only=true`, `model_use_allowed=false`, `training_allowed=false`, `production_approved=false`

## Source Limits

The backfilled receipts trace lagged factual V3 overlap only. They do not contain exact Model v4 normalized scores, weights, checkpoint outputs, lifecycle modifiers, confidence caps, WR/QB v2 candidate overlays, or production-active approvals.
