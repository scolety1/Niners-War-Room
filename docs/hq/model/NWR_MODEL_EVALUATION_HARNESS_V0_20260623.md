# NWR Model Evaluation Harness V0

Date: 2026-06-23
Branch: work/hq-parallel-control
Verdict: GREEN

## Purpose

Model Evaluation Harness V0 is a read-only evaluation layer for current NWR model/ranking outputs. It audits coverage, evidence eligibility, market sanity diagnostics, Outcome support, and potential false-confidence rows without changing any rank, weight, model label, source-truth artifact, or app workflow.

This is evaluation infrastructure, not tuning.

## Prerequisite

The Draft-Day App V2 release-candidate audit was checked before implementation:

- `docs/hq/draft_day_v2/NWR_DRAFT_DAY_APP_V2_RELEASE_CANDIDATE_AUDIT_20260623.md`
- RC verdict: GREEN
- P0/P1 blockers: none

## Files Added

- `src/services/model_evaluation_harness_service.py`
- `scripts/run_model_evaluation_harness_v0.py`
- `tests/test_model_evaluation_harness_service.py`
- `docs/hq/model/evaluation_v0/NWR_MODEL_EVALUATION_SUMMARY_V0_20260623.csv`
- `docs/hq/model/evaluation_v0/NWR_MODEL_EVALUATION_BY_BUCKET_V0_20260623.csv`
- `docs/hq/model/evaluation_v0/NWR_MODEL_EVALUATION_WARNINGS_V0_20260623.csv`
- `docs/hq/model/evaluation_v0/NWR_MODEL_EVALUATION_WARNING_REPAIR_QUEUE_20260623.csv`

## Inputs Inspected

- Current full dynasty board through the draft-day app service.
- Frozen baseline board through the draft-day app service.
- Expanded draftable pool through the draft-day app service.
- Outcome coverage match table:
  - `docs/hq/parallel_lanes/NWR_OUTCOME_COLUMNS_COVERAGE_MATCH_TABLE_20260622.csv`
- Historical drop reconstruction:
  - `docs/hq/data_sources/historical_drop_lists/NWR_HISTORICAL_DROP_LIST_RECONSTRUCTION_2010_2026.csv`
- Backtest eligibility rules:
  - `docs/hq/model/NWR_BACKTEST_ROW_ELIGIBILITY_RULES_20260623.csv`
- DynastyProcess/market baseline context through the existing market baseline service.

## Evidence Buckets

The harness keeps evidence classes separated:

| Bucket | Included Evidence | Use |
| --- | --- | --- |
| Truth backtest | `ACTUAL_DROP` with high-confidence actual evidence | Honest actual-evidence backtest bucket only |
| Caution backtest | `ACTUAL_DROP` plus medium/high `INFERRED_DROP` | Wider review bucket, not training truth |
| Sensitivity test | `PROXY_DROP`, `PROXY_ONLY`, low-confidence rows | Sensitivity only |
| Market sanity diagnostics | DynastyProcess/ADP/market context | Display-only diagnostics, never training truth |

No bucket is marked training-eligible in this V0 run.

## Current Output Summary

- Full dynasty board rows: 240
- Frozen baseline board rows: 66
- Expanded draftable pool rows: 143
- Outcome matched rows: 12
- Outcome unsupported/missing rows: 54
- Truth backtest rows: 22
- Caution backtest rows: 149
- Sensitivity-only proxy rows: 480
- P0/P1 model trust warnings: 0
- P2 potential false-confidence warnings after repair: 2
- Evaluation-only player ID repairs: 29
- Explicit `Not enough information` Outcome clarifications: 30

The harness explicitly reports predictive accuracy as `Not enough information` because no actual future outcome label is available in this evaluation pass.

## Warnings

The warning file currently contains P2 potential false-confidence warnings. These are not release blockers, but they should stay visible in model/accountability reviews.

Common warning pattern:

- high-rank player has a remaining age gap;
- confidence/caveat should remain visible to the user;
- missing data should display as `Not enough information`.

Remaining P2 examples:

- KC Concepcion: age remains `Not enough information`.
- Brian Thomas: age remains `Not enough information`.

Resolved/clarified issues are tracked in the repair queue rather than hidden. Player IDs were resolved for evaluation only from existing high-confidence identity artifacts and were not written into the frozen board or rankings. Outcome gaps remain unsupported but are explicitly labeled `Not enough information`, not low probability.

## Guardrail Confirmations

- No model/rank logic changed.
- No tuning or retraining was run.
- No production rankings were overwritten.
- Frozen Final Draft Board V1 was not mutated.
- `final_board_rank` values were not changed.
- Dynasty Rank values were not changed.
- `latest_candidate` and `latest_approved` were not updated.
- Pinned snapshot was not mutated.
- Proxy and low-confidence evidence rows are not training truth.
- DynastyProcess/ADP/market context remains diagnostics-only.
- No `C:\NWR_SHARED_DATA` files were tracked.
- No runtime state JSON was tracked.

## Validation

Commands run:

- `python scripts/run_model_evaluation_harness_v0.py`
- `python -m pytest tests/test_model_evaluation_harness_service.py`
- `python -m ruff check src/services/model_evaluation_harness_service.py scripts/run_model_evaluation_harness_v0.py tests/test_model_evaluation_harness_service.py`
- `python -m py_compile src/services/model_evaluation_harness_service.py scripts/run_model_evaluation_harness_v0.py tests/test_model_evaluation_harness_service.py`
- `git diff --check`

Results:

- Harness output validation: passed.
- Focused pytest: 5 passed.
- Ruff: passed.
- Python compile: passed.
- Diff check: passed.

## Recommended Next Step

Use this harness as the baseline for future model/accountability work. The next useful lane is to add actual future outcome labels or confirmed historical draft/drop/trade evidence, then rerun V0 without collapsing actual, inferred, proxy, and market rows into one truth bucket.
