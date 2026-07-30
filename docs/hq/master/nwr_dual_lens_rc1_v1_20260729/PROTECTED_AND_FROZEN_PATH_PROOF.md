# Protected and frozen path proof

Pinned read-only inputs:

- `docs/hq/model/current_board_deterministic_rebuild_with_recovery_inputs_v1_20260708/rebuilt_full_player_board_value_review_rows.csv` → `263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4`;
- `docs/hq/model/formula_temporal_validation_framework_prospective_2026_challenger_freeze_v1_20260710/PROSPECTIVE_2026_BASELINE_FREEZE.csv` → `b3270d9782cf53de745e966c318dd61aa7f482db17da7c4ceb51ef8baa8e1179`;
- `docs/hq/master/nwr_outcome_columns_v3_rc1_v1_20260729/CURRENT_2026_OUTCOME_V3_SHADOW_BOARD.csv` → `256c4deb8c0199d29143fc117a43496dc6847dd0e7b3724549a372cb1b6df577`;
- `docs/hq/master/nwr_outcome_columns_v3_rc1_v1_20260729/OUTCOME_V3_SCHEMA.csv` → `7001e319eb0aafc2a3eb9d4de8a2fd421b19fabd552bc16a1a5df69b48ab2cff`.

The source ledger records every file the builder reads. The write allow-list is
only `docs/hq/master/nwr_dual_lens_rc1_v1_20260729` (or an explicitly supplied detached output
directory). No V2-2 path, local export, refresh pointer, app runtime, or
protected/frozen artifact is written.
