# NWR Overnight Model Tune V1 Expanded Results - 2026-06-22

Status: GREEN for local-only evidence generation. No model is approved or promoted.

This summary records the true V1 expanded search that repaired the V0 small-grid
mistake. It does not approve private value, rankings, hidden sort, Mock Draft
behavior, simulations, final draft advice, deployment, `latest_candidate`, or
`latest_approved`.

## Restore Points

| Checkpoint | Commit |
| --- | --- |
| PRE_V1_EXPANDED_TUNE_RESTORE_POINT | `c9dd8ddaeb8efb0c8694656a82accd53ca0b6a1e` |
| PRE_FULL_V1_TUNE_RESTORE_POINT | `0202d318ce8a323f6bc2a673d9391686fcf6b42f` |

## Local-Only Artifacts

Output root:
`C:\NWR_SHARED_DATA\backtests\overnight_model_tune_v1_expanded_20260622`

Key local-only reports:

- `V0_SMALL_GRID_DIAGNOSIS.md`
- `V1_EXPANDED_PRE_RUN_GRID_MANIFEST.csv`
- `V1_EXPANDED_PRE_RUN_SUMMARY.md`
- `VENDOR_FEATURE_READINESS.md`
- `VENDOR_FEATURE_JOIN_COVERAGE.csv`
- `V1_EXPANDED_RUN_MANIFEST.csv`
- `V1_EXPANDED_POSITION_RESULTS.csv`
- `V1_EXPANDED_YEARLY_RESULTS.csv`
- `V1_EXPANDED_VARIANT_RANKINGS.csv`
- `V1_EXPANDED_VENDOR_CHALLENGER_RESULTS.csv`
- `V1_EXPANDED_WINNERS_BY_POSITION.md`
- `V1_EXPANDED_FINAL_REPORT.md`

## V0 Diagnosis

V0 finished in roughly 56 seconds because it was a small finite scaffold grid:
four safe feature variants by position, fixed starter hyperparameters, no
phase-2 deepening, no phase-3 stability stress tests, and no actual model-ready
vendor feature join. Vendor challengers were marked as planned research rows,
but not joined into model-ready historical feature rows.

V1 corrected this by requiring an actual vendor join, requiring an expanded
pre-run grid, adding larger hyperparameter grids and model families, and adding
explicit Phase 2 and Phase 3 search/stability rows.

## Pre-Run Grid

| Item | Count |
| --- | ---: |
| Planned position-level fits | 24,408 |
| QB planned fits | 5,424 |
| RB planned fits | 6,328 |
| WR planned fits | 6,328 |
| TE planned fits | 6,328 |
| Vendor feature columns joined | 71 |

Feature-family planned fits:

| Feature family | Planned fits |
| --- | ---: |
| SAFE_BASELINE | 1,808 |
| SAFE_EXPANDED | 1,808 |
| SAFE_NO_SNAP | 1,808 |
| SAFE_SNAP_FIXED | 1,808 |
| YELLOW_CHALLENGER | 10,848 |
| VENDOR_YELLOW_CHALLENGER | 6,328 |

Vendor challenger readiness was GREEN for research-only use. Vendor features
remained isolated as `VENDOR_YELLOW_CHALLENGER`; no vendor variant is a safe
promotion candidate.

## Run Summary

| Item | Result |
| --- | ---: |
| Runtime seconds | 8,577.203 |
| Runtime | about 2h 23m |
| Completed fits | 24,408 |
| Skipped fits | 0 |
| Position result rows | 24,408 |
| Yearly result rows | 122,040 |
| Prediction rows | 14,065,336 |
| Phase 2 deepening | ran |
| Phase 3 stability stress | ran |
| Blocked-field scan | PASS |
| Leakage scan | PASS |

The expanded grid was exhausted before the 480-minute cap. This was not another
small V0-style run.

## Best By Position

| Pos | Best variant | Family | Model | Top-N | Spearman | MAE | RMSE | Label |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| QB | `role_usage_core` | YELLOW_CHALLENGER | extra trees | 0.417 | 0.670 | 61.362 | 76.674 | BASELINE_OR_CONTROL_PREFERRED |
| RB | `role_usage_core` | YELLOW_CHALLENGER | extra trees | 0.500 | 0.676 | 42.672 | 57.481 | SAFE_RESEARCH_CANDIDATE |
| TE | `safe_baseline` | SAFE_BASELINE | random forest | 0.500 | 0.714 | 20.069 | 26.714 | BASELINE_REFERENCE |
| WR | `vendor_rotowire_receiving_redzone` | VENDOR_YELLOW_CHALLENGER | extra trees | 0.556 | 0.712 | 30.291 | 39.385 | VENDOR_RESEARCH_CANDIDATE |

## Baseline Comparison

| Pos | Baseline Top-N | Best Top-N | Read |
| --- | ---: | ---: | --- |
| QB | 0.250 | 0.417 | Best row was YELLOW, but stability gate did not support safe candidate status. |
| RB | 0.458 | 0.500 | SAFE_RESEARCH_CANDIDATE exists for `role_usage_core`. |
| TE | 0.500 | 0.500 | Baseline remains preferred/reference. |
| WR | 0.472 | 0.556 | Vendor research candidate exists; best safe candidate was `safe_no_snap` at 0.556. |

## Candidate Labels

| Label | Rows |
| --- | ---: |
| BASELINE_OR_CONTROL_PREFERRED | 16,128 |
| VENDOR_YELLOW_HOLD | 6,231 |
| BASELINE_REFERENCE | 1,808 |
| SAFE_RESEARCH_CANDIDATE | 144 |
| VENDOR_RESEARCH_CANDIDATE | 97 |

SAFE_RESEARCH_CANDIDATE rows appeared for RB and WR only. Vendor research
candidates appeared for WR only. Vendor rows remain research-only and require
source/license review before any future model/backtest package use.

## Recommendation

Baseline remains preferred for TE and remains the safest default where expanded
variants do not clear stability gates. RB `role_usage_core` and WR `safe_no_snap`
are worth future local-only candidate-package review. WR RotoWire receiving
red-zone vendor challenger is interesting as research evidence only; it must not
be labeled safe or flow into private value, rankings, Mock Draft, simulations, or
draft advice without separate approval.

No `latest_candidate` or `latest_approved` package was created or updated.
