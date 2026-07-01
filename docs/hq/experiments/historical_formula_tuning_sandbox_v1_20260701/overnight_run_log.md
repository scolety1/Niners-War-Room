# Overnight Run Log

Generated at: `2026-07-01T07:57:28.044834+00:00`

## Phase 0

- Read packet master and all phase files before repo changes.
- Fetched origin.
- Created clean isolated worktree from `origin/work/hq-parallel-control`.
- Confirmed base HEAD `7e99865871d11890f0bfac3fd2282525f163a40d`.
- Created branch `work/historical-formula-tuning-sandbox-v1-20260701`.

## Phase 1

- Inventoried tracked Core Usage Dataset V1, typed red-zone sidecar, compact Outcome V2 labels, and local generated Backtest V1 artifacts.
- Found Core Usage Dataset V1 alone has only 2024-2025 usage and lacks admitted 2025 labels for N to N+1 tuning.
- Continued in safe-YELLOW review-only mode using local generated Backtest V1 substrate whose checksums are documented in tracked HQ docs.

## Phase 2

- Used frozen local generated `v1_baseline` prediction artifact as the baseline comparison.
- Did not edit production formulas, models, app code, rankings, source truth, hidden sort, or runtime logic.

## Phase 3

- Evaluated `12` fixed candidate-only formulas.
- Used fold-local one-dimensional calibration using prior target years only.
- Did not tune on holdout.

## Phase 4

- Compared candidates on validation years `2023;2024` and holdout year `2025`.
- Rejected candidates as tuning-ready because no candidate improved MAE, Spearman, and Top-N hit rate across validation and holdout.

## Phase 5

- Wrote review-only artifacts under `docs\hq\experiments\historical_formula_tuning_sandbox_v1_20260701`.
- Final validation and push are performed outside this generator and reported in the final Codex response.
