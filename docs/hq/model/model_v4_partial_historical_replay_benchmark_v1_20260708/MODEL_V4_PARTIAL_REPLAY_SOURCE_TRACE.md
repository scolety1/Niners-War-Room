# Model v4 Partial Replay Source Trace

## Sources Used

| Source | Path | Use Gate |
| --- | --- | --- |
| Historical component receipt backfill | `C:\NWR\Niners-War-Room-model-v4-historical-component-receipt-backfill-v1-20260708\docs\hq\model\model_v4_historical_component_receipt_backfill_v1_20260708` | Review-only partial receipts; not exact replay. |
| Partial replay input panel | `C:\NWR\Niners-War-Room-historical-model-v4-replay-substrate-v1-20260708\docs\hq\model\historical_model_v4_replay_substrate_v1_20260708\MODEL_V4_PARTIAL_REPLAY_INPUT_PANEL_REVIEW_ONLY.csv` | Lagged V3 factual overlap; decision-date separated. |
| Production Rankings Backtest V1 | `C:\NWR\Niners-War-Room-production-rankings-backtest-v1-20260708\docs\hq\model\production_rankings_backtest_v1_20260708` | Prior proxy/current-formula-family comparison context. |
| Historical Model v4 replay substrate | `C:\NWR\Niners-War-Room-historical-model-v4-replay-substrate-v1-20260708\docs\hq\model\historical_model_v4_replay_substrate_v1_20260708` | Partial replay panel and original contract. |
| Exact current-board rebuild packet | `C:\NWR\Niners-War-Room-current-board-deterministic-rebuild-with-recovery-inputs-v1-20260708\docs\hq\model\current_board_deterministic_rebuild_with_recovery_inputs_v1_20260708` | Current board exact rebuild proof only; not historical input. |
| Formula documentation / cleanup packet | `C:\NWR\Niners-War-Room-model-v4-formula-documentation-cleanup-v1-20260708\docs\hq\model\model_v4_formula_documentation_cleanup_v1_20260708` | Component/blocker taxonomy. |
| HQ1 receipt-chain standard | `docs\hq\deep_research_upgrades\hq1_source_receipt_chain_standard_v1_20260708` | Source receipt/use-gate standard. |

## HQ1 Use-Gate Answers

1. Do we actually have the information? Yes, for the lagged factual partial component columns only.
2. Where did it come from? The V3 historical replay substrate and the prior historical component receipt backfill packet.
3. Is it reliable enough for review-only benchmark use? Yes, with explicit review-only/proxy caveats.
4. Use gate: `YELLOW_REVIEW_ONLY`; not model-use, not production, not source-truth.
5. Can it be reproduced? Yes, via `build_model_v4_partial_historical_replay_benchmark_v1.py` and the source hashes in `MODEL_V4_PARTIAL_REPLAY_INPUT_RECEIPTS_USED.csv`.
6. Can it be tested historically without leakage? Yes for this partial panel; exact Model v4 replay remains blocked.

## Non-Inputs

No current ADP, market, injury/depth/roster context, production rankings artifact, current-board score, checkpoint, lifecycle, confidence, or target-season outcome field was used as an input.
