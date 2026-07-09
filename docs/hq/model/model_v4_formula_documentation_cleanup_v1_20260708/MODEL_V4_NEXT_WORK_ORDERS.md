# Model v4 Next Work Orders

Date: 2026-07-08

## 1. Component Receipt Backfill / Source-Admission Lane

Objective: Restore or regenerate the current Model v4 component receipt chain that reconciles `nwr_dynasty_score`.

Files likely involved:

- `src/services/model_v4_replacement_vorp_core_service.py`
- `src/services/model_v4_rb_wr_current_value_service.py`
- `src/services/model_v4_qb_te_current_value_service.py`
- `src/services/model_v4_lifecycle_archetype_service.py`
- `src/services/model_v4_confidence_missingness_service.py`
- `src/services/model_v4_current_value_checkpoint_service.py`
- `src/services/full_player_board_value_service.py`
- `local_exports/model_v4/current_value/latest/*`
- `local_exports/model_v4/replacement_vorp/latest/*`

Data needed: Current admitted component inputs, row-level source receipts, missingness/warning matrices, first-down scoring receipts, replacement/VORP receipts.

Metric to produce: 100% reconciliation from component receipts to current `nwr_dynasty_score` for scored rows, or a row-level blocker reason.

Gate required: Source admission and receipt integrity gate.

Safe now: Yes for read-only inventory and receipt existence checks; receipt regeneration needs human review.

## 2. Formula Cleanup / App-Label Correction Lane

Objective: Resolve whether the app should display the current board as candidate review-only or whether a documented promotion occurred but labels/receipts are stale.

Files likely involved:

- `app/pages/20_final_board_v1.py`
- `src/services/draft_day_app_v1_service.py`
- `docs/hq/rankings/*`
- `docs/hq/model/*`
- Current board artifact policy columns.

Data needed: Human promotion decision, app status labels, row-level allowed-use stamps, tests proving no hidden sort/source promotion.

Metric to produce: 0 mismatches between app labels, row-level allowed-use, docs, and tests.

Gate required: Human review plus app/ranking guardrail tests.

Safe now: Needs human review before any behavior or label change.

## 3. Historical Component Receipt Design Lane

Objective: Define the season-by-season decision-date receipt schema needed for exact Model v4 replay.

Files likely involved:

- `docs/hq/model/historical_model_v4_replay_substrate_v1_20260708/*`
- `docs/model_v4/*`
- Source gate docs for NFLVerse, PFR, NGS, CFBD, DynastyProcess, injury/availability.

Data needed: Historical labels, canonical identity map, source availability by season, component schemas, leakage policy.

Metric to produce: Historical receipt availability matrix with target season, feature season, component, admitted source, coverage, and blocker reason.

Gate required: Decision-date/leakage gate.

Safe now: Yes as documentation/design only.

## 4. Source Gate Consolidation Lane

Objective: Produce one authoritative model-use/display-only/review-only/blocked status table for every source that could feed Model v4.

Files likely involved:

- Source gate docs under `docs/hq`
- Data health docs
- PFR, NGS, NFLVerse, CFBD, DynastyProcess, injury/availability review packets.

Data needed: Existing source gates and row-count/coverage evidence.

Metric to produce: One row per source/field family with production-use status, coverage, identity risk, and replay eligibility.

Gate required: Source governance review.

Safe now: Yes as review documentation.

## 5. Exact Historical Replay Benchmark Lane

Objective: Run a true historical replay benchmark for the approved formula target.

Files likely involved:

- Future replay harness files.
- Historical component receipt outputs.
- Historical labels/outcomes.
- Baseline comparison definitions.

Data needed: Approved formula target, complete historical decision-date receipts, historical labels, baseline ladder.

Metric to produce: Top-N precision, startable precision, MAE/RMSE, rank correlation, bucket accuracy, position-level results, and baseline deltas.

Gate required: Formula target gate plus replay/leakage gate.

Safe now: No. This remains blocked until receipt backfill and formula status cleanup are complete.

## 6. Candidate Overlay Promotion Or Rejection Lane

Objective: Decide whether WR/QB v2 candidate overlay should be rejected, retained as review-only, or promoted after evidence.

Files likely involved:

- `src/services/model_v4_wr_qb_v2_candidate_service.py`
- Candidate output artifacts under `local_exports/model_v4/current_value/candidates/wr_qb_v2`
- Prior backtest and replay packets.

Data needed: Candidate overlay receipts, player-level deltas, false-positive review, baseline comparison after exact replay substrate exists.

Metric to produce: Candidate overlay lift versus base formula and prior-year baseline, by position and player archetype.

Gate required: Human promotion/rejection gate.

Safe now: No promotion or benchmark yet; safe only as review design.
