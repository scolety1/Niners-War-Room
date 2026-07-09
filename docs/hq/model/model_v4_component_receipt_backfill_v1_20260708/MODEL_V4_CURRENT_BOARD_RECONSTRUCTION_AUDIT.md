# Model v4 Current Board Reconstruction Audit

Date: 2026-07-08

## Audit Scope

This audit inspected whether the current app-visible candidate board can be deterministically reconstructed from local repo files and local data without changing formula logic, weights, rankings, or source-gate status.

No production/runtime outputs were written. The app control-path board was inspected read-only because `src/services/draft_day_app_v1_service.py` defines it as the pinned control artifact.

## Control Board Observed

Path inspected read-only:

`C:\NWR\Niners-War-Room\local_exports\model_v4\current_value\latest\full_player_board_value_review_rows.csv`

Observed:

- Rows: 240
- Columns: 58
- SHA256: `263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4`
- Expected app pin: `263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4`
- `allowed_use`: `candidate_review_only_not_active_rankings` on 240 rows
- `candidate_mode`: `wr_qb_v2_candidate` on 240 rows
- `score_status`: 232 scored, 8 not scored
- `upstream_source_column`: `checkpoint_review_score` on 232 rows, blank on 8 rows

## Reconstruction Checks

| Check | Result | Evidence | Caveat |
| --- | --- | --- | --- |
| Clean worktree current board file | Missing | `local_exports/model_v4/current_value/latest` is absent in the fresh worktree | Runtime artifacts are not tracked in canonical HQ |
| Control-path final board | Present | Hash matches app pin | Read-only observation only |
| Candidate output folder | Missing | `local_exports/model_v4/current_value/candidates/wr_qb_v2` absent in control runtime | Reason/guardrail reports unavailable |
| Base full board before candidate overlay | Missing | `current_player_value_full_board_review_rows.csv` absent | Blocks base board reconstruction |
| Checkpoint review rows | Missing | `current_player_value_review_rows.csv` absent | Blocks `checkpoint_review_score` reconstruction |
| Checkpoint component rows | Missing | `current_player_value_component_rows.csv` absent | Blocks component reconciliation |
| Checkpoint receipts | Missing | `current_player_value_receipts.csv` absent | Blocks source trace |
| RB/WR component receipts | Missing | `rb_wr_current_value_*` files absent | Blocks RB/WR component math |
| QB/TE component receipts | Missing | `qb_te_current_value_*` files absent | Blocks QB/TE component math |
| Replacement/VORP receipts | Missing | replacement/VORP player/component/receipt files absent | Blocks VORP/first-down anchor proof |
| Lifecycle receipts | Missing | lifecycle rows/receipts absent | Blocks lifecycle modifier proof |
| Confidence receipts | Missing | confidence/missingness rows/receipts absent | Blocks confidence cap proof |

## Candidate Delta Audit

The final board contains observable `base_nwr_dynasty_score`, `nwr_dynasty_score`, and `candidate_adjustment` fields for 232 scored rows.

Read-only arithmetic check:

- Nonblank candidate adjustments: 232
- Nonblank base scores: 232
- Nonblank base ranks: 232
- `nwr_dynasty_score - base_nwr_dynasty_score == candidate_adjustment` mismatches: 0

This proves only that the final board's copied base/final/delta fields are internally consistent. It does not prove the upstream component math that produced the base score or candidate overlay.

## Conclusion

The current app-visible candidate board cannot be deterministically reconstructed in this lane. The final board is observable and hash-verified, but the builder input chain is missing.

Safe output produced:

- Observed final-board field receipts in `MODEL_V4_COMPONENT_RECEIPTS_CURRENT_BOARD.csv`.
- Receipt/input artifact inventory in `MODEL_V4_COMPONENT_RECEIPT_INVENTORY.csv`.

Unsafe output deliberately not produced:

- Fake checkpoint rows.
- Fake RB/WR/QB/TE component values.
- Fake VORP, lifecycle, confidence, or source receipts.
- Any production ranking or model formula change.
