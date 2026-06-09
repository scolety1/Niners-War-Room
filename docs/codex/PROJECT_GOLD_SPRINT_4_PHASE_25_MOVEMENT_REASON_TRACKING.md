# Project Gold Sprint 4 / Phase 25: Movement Reason Tracking

Last reviewed: 2026-05-14

## Status

Movement tracking is now an audit-only metadata layer. It does not alter player
scores, formulas, rankings, gates, or readiness labels.

## What Changed

- Added a reusable movement classifier for checkpoint comparisons.
- Added movement export support to the model audit packet exporter when a
  comparison baseline is provided.
- Added these movement columns:
  - `movement_reason`
  - `movement_magnitude`
  - `movement_review_flag`
  - `movement_review_label`
- Added CLI support:
  - `--comparison-baseline`
  - `--movement-export-name`

## Movement Reasons

The classifier can label movement as:

- `source_update`
- `formula_update`
- `lifecycle_update`
- `confidence_update`
- `outlier_acceptance`
- `source_gap_acceptance`
- `market_isolation`
- `ranking_surface_change`
- `no_material_movement`
- `unknown_movement`

Unknown medium or large movement is flagged for review with
`movement_review_flag=true`.

## Generated Packet

Fresh Phase 25 packet:

`local_exports/model_audits/sprint4_phase25_movement_reason_tracking_20260514`

Comparison baseline:

`local_exports/model_audits/sprint2_phase12_checkpoint_20260514`

Movement export:

`movement_vs_sprint2_checkpoint.csv`

Current result against that baseline:

| movement_reason | rows |
|---|---:|
| `no_material_movement` | 1039 |

This is expected because the current active rankings and the Sprint 2 checkpoint
snapshot on disk share the same active stats-first output timestamp.

## Safety

- Rankings remain review-only.
- `decision_ready_allowed` remains `false`.
- Movement reasons are for audit and external review only.

## Verification

Focused tests:

- `tests/test_movement_reason_service.py`
- `tests/test_model_audit_packet_service.py`

Result:

- `14 passed`
