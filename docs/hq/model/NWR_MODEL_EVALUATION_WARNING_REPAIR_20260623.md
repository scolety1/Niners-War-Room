# NWR Model Evaluation Warning Repair

Date: 2026-06-23
Branch: work/hq-parallel-control
Verdict: GREEN

## Purpose

This lane repaired review-safe data-quality/accountability issues behind Model Evaluation Harness V0 warnings. It did not tune, retrain, rerank, or mutate source-truth artifacts.

## Starting Point

Starting warning file:

- `docs/hq/model/evaluation_v0/NWR_MODEL_EVALUATION_WARNINGS_V0_20260623.csv`

Starting warning count:

- 30 P2 `potential_false_confidence` warnings

Primary warning causes:

- high-rank expanded draftable-pool rows missing `player_id`;
- approved Outcome support absent;
- a few age gaps;
- explicit `Not enough information` Outcome labels were still being counted as warnings.

## Repairs Made

### Player ID Gaps

The harness now uses existing review-safe identity evidence for evaluation-only repairs:

- approved full dynasty board exact name + position matches;
- `docs/hq/data_sources/identity/player_id_coverage_audit_v1.csv` high-confidence, no-manual-review rows.

This resolves 29 high-rank player ID gaps for evaluation reporting only. No IDs were written into the frozen board, full dynasty board, app source artifacts, or latest files.

### Outcome Support Gaps

The harness now distinguishes:

- blank/unlabeled Outcome support, which remains warning-worthy;
- explicit `Not enough information`, which is a clarified unsupported Outcome state.

Thirty high-rank rows remain without approved Outcome probabilities, but they are explicitly labeled `Not enough information`. They are tracked in the repair queue and are not treated as low probability or hidden.

### Remaining Legitimate Warnings

Ending warning count:

- 2 P2 warnings

Remaining warnings:

| Player | Remaining issue | Why not repaired |
| --- | --- | --- |
| KC Concepcion | Age missing | No safe existing approved age source found. |
| Brian Thomas | Age missing | Existing approved source says `Not enough information`; not a real age value. |

## Repair Queue

Created:

- `docs/hq/model/evaluation_v0/NWR_MODEL_EVALUATION_WARNING_REPAIR_QUEUE_20260623.csv`

Queue columns:

- `warning_id`
- `player_name`
- `issue_type`
- `current_status`
- `repair_action`
- `source_used`
- `confidence`
- `remaining_risk`
- `notes`

Repair queue summary:

- 29 `player_id` rows resolved for evaluation only.
- 30 Outcome support gaps clarified as explicit `Not enough information`.
- 2 age gaps remain `Not enough information`.

## Guardrails

Confirmed:

- no model/rank logic changed;
- no retraining or tuning;
- no production rankings changed;
- frozen Final Draft Board V1 not mutated;
- `final_board_rank` unchanged;
- Dynasty Rank unchanged;
- `latest_candidate` / `latest_approved` untouched;
- pinned snapshot untouched;
- DynastyProcess/market/ADP not promoted to model truth;
- proxy rows not used as training truth;
- no fabricated player IDs;
- no fabricated Outcome probabilities;
- no `C:\NWR_SHARED_DATA` files tracked;
- no runtime JSON tracked.

## Validation

Passed:

- `python scripts/run_model_evaluation_harness_v0.py`
- `pytest tests/test_model_evaluation_harness_service.py`
- `ruff check src/services/model_evaluation_harness_service.py tests/test_model_evaluation_harness_service.py scripts/run_model_evaluation_harness_v0.py`
- Python compile on touched Python files
- CSV load and required-column validation through the harness validator
- `git diff --check`

## Result

The warning set is smaller and more accurate:

- player ID gaps are repaired only where a high-confidence existing source already exists;
- unresolved age gaps remain visible;
- unsupported Outcome remains honest and visible as `Not enough information`;
- warning reduction did not hide missing data or mutate source truth.
