# Model v4 Receipt Source Trace

Date: 2026-07-08

## HQ Base

Canonical remote checked:

`origin/work/hq-parallel-control`

Verified HEAD:

`9e3532dafaa1dfaeaa460ef544403dcc391bcd5f`

## Prior Packets Verified

### Production Rankings Backtest V1

Path:

`C:\NWR\Niners-War-Room-production-rankings-backtest-v1-20260708\docs\hq\model\production_rankings_backtest_v1_20260708`

Commit verified:

`2b9710d176d529304a04ef7c5102787183efcf59`

Files read:

- `PRODUCTION_RANKINGS_BACKTEST_V1_REPORT.md`
- `PRODUCTION_RANKINGS_BACKTEST_V1_SOURCE_TRACE.md`
- `PRODUCTION_RANKINGS_BACKTEST_V1_CAVEATS.md`
- `PRODUCTION_RANKINGS_BACKTEST_V1_SCORECARD.csv`

Use in this lane:

- Confirmed proxy backtest caveat and no exact Model v4 replay.
- Confirmed current board hash/pin context.

### Historical Model v4 Replay Substrate V1

Path:

`C:\NWR\Niners-War-Room-historical-model-v4-replay-substrate-v1-20260708\docs\hq\model\historical_model_v4_replay_substrate_v1_20260708`

Commit verified:

`75b9805b64841d8b6c4e1b4e66ba7d324278e83f`

Files read:

- `HISTORICAL_MODEL_V4_REPLAY_SUBSTRATE_V1_REPORT.md`
- `MODEL_V4_REPLAY_BLOCKERS.md`
- `MODEL_V4_REPLAY_CONTRACT.md`
- `MODEL_V4_FORMULA_COMPONENT_SOURCE_MAP.csv`
- `MODEL_V4_HISTORICAL_REPLAY_AVAILABILITY_MATRIX.csv`
- `MODEL_V4_REPLAY_SOURCE_TRACE.md`

Use in this lane:

- Confirmed exact replay remains blocked.
- Confirmed historical partial substrate is not exact Model v4 score replay.

### Model v4 Formula Documentation / Cleanup V1

Path:

`C:\NWR\Niners-War-Room-model-v4-formula-documentation-cleanup-v1-20260708\docs\hq\model\model_v4_formula_documentation_cleanup_v1_20260708`

Commit verified:

`6a05959bd5e4a9d9c8c0553ef1a06d826730c032`

Files read:

- `MODEL_V4_FORMULA_DOCUMENTATION_CLEANUP_V1_REPORT.md`
- `MODEL_V4_ACTIVE_FORMULA_CONTRACT.md`
- `MODEL_V4_MISSING_COMPONENT_RECEIPTS.md`
- `MODEL_V4_COMPONENT_REGISTRY.csv`
- `MODEL_V4_FORMULA_SOURCE_TRACE.md`

Use in this lane:

- Seeded normalized missing receipt list.
- Confirmed current board status as `candidate_review_only_main_display`.
- Confirmed active production formula is not identifiable.

## Current Code Files Read

- `src/services/draft_day_app_v1_service.py`
- `src/services/full_player_board_value_service.py`
- `src/services/model_v4_wr_qb_v2_candidate_service.py`
- `src/services/model_v4_current_value_checkpoint_service.py`
- `src/services/model_v4_rb_wr_current_value_service.py`
- `src/services/model_v4_qb_te_current_value_service.py`
- `src/services/model_v4_replacement_vorp_core_service.py`
- `src/services/model_v4_lifecycle_archetype_service.py`
- `src/services/model_v4_confidence_missingness_service.py`
- `src/services/model_v4_formula_contract_service.py`

## Current Board Artifact Inspected Read-Only

Path:

`C:\NWR\Niners-War-Room\local_exports\model_v4\current_value\latest\full_player_board_value_review_rows.csv`

Reason:

`src/services/draft_day_app_v1_service.py` defines the app control board path and expected hash for this artifact.

Observed:

- Rows: 240
- SHA256: `263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4`
- `allowed_use = candidate_review_only_not_active_rankings`: 240 rows
- `candidate_mode = wr_qb_v2_candidate`: 240 rows
- `score_status = scored`: 232 rows
- `score_status = not_scored`: 8 rows

Primary checkout note:

The primary checkout was inspected read-only. It was not modified, reset, cleaned, stashed, merged, or pushed.

## Generated Review Artifacts

Generator:

`docs/hq/model/model_v4_component_receipt_backfill_v1_20260708/build_model_v4_component_receipt_backfill_v1.py`

Generated CSV artifacts:

- `MODEL_V4_COMPONENT_RECEIPT_INVENTORY.csv`
- `MODEL_V4_COMPONENT_RECEIPTS_CURRENT_BOARD.csv`
- `MODEL_V4_SOURCE_ADMISSION_READINESS_MATRIX.csv`
- `MODEL_V4_HISTORICAL_REPLAY_RECEIPT_READINESS.csv`

## Source Trace Limits

- No production formula files were edited.
- No rankings files were edited.
- No UI/runtime behavior was changed.
- No source was promoted.
- No benchmark or tuning lane was run.
- No fake component receipts were created.
