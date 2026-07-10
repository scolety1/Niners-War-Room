# Formula Temporal Validation Framework V1 Report

## Verdict

`RED_REGULARIZED_CHALLENGER_FAILED_TEMPORAL_VALIDATION`

The preregistered rolling-origin evaluation completed across **11 independent target seasons (2015–2025)** and all four supported positions. Every scored origin used only earlier target seasons for fitting and only feature-season T-1 facts for target season T. Predictions were hashed before each scored origin's outcomes were joined.

All historical evidence is `RETROSPECTIVE_TEMPORAL_VALIDATION_WITH_PRIOR_SELECTION_CAVEATS`. It is candidate-screening evidence, not fresh or untouched proof and not a production superiority claim.

## Controlling reconciliation preserved

The accepted audit at `dce5131d77f9fb671bdf6141650677d2a3444641` was not rerun or altered. Its controlling values remain PYF `0.741285` ranking-aligned / `0.693350` pooled and exact GAUNTLET_081 `0.754604` ranking-aligned / `0.708315` pooled. The retired 70/20/10 proxy remains retired. The present rolling-origin scoreboards answer a new temporal-stability question and do not replace those audit values.

## Shared-row headline results

| Candidate | Position-balanced Spearman | PYF on same rows | Delta | Season-balanced Spearman | PYF on same rows | Delta |
|---|---:|---:|---:|---:|---:|---:|
| Exact legacy GAUNTLET_081 | 0.693350 | 0.674042 | +0.019308 | 0.693350 | 0.674042 | +0.019308 |
| Position-specific ridge | 0.682360 | 0.674559 | +0.007801 | 0.682360 | 0.674559 | +0.007801 |

With the complete 11×4 season-position grid, macro, position-balanced, and season-balanced arithmetic means are algebraically equal. They are still reported separately to preserve the preregistered weighting contracts.

The ridge's worst position was **QB** at `-0.001213` versus PYF. Its worst season was **2020** at `-0.002022`. It improved in `9` of 11 season-balanced comparisons.

## Severe misses and coverage

On ridge/PYF shared rows, severe false positives were `79` for ridge versus `73` for PYF. Severe false negatives were `70` versus `75`. Net severe misses were `149` versus `148`.

Ridge full historical coverage was `4731/4731` (`1.000000`), versus PYF `4731/4731` (`1.000000`). Shared-row and full-coverage evaluations remain separate in their dedicated scoreboards.

## Uncertainty

The paired season-cluster bootstrap used 10,000 draws and seed `20260710`. The position-balanced 95% interval is `[+0.003512, +0.012502]`; the season-balanced interval is `[+0.003512, +0.012502]`. The inference unit is season, never player. Eleven seasons support a stability review but not a claim of formal certainty or production proof.

## Mechanical gate

| Gate | Result |
|---|---|
| Headline improvement | PASS |
| Not isolated to one season | PASS |
| No material repeated position regression | FAIL |
| No severe-FP increase overall or by position | FAIL |
| No favorable coverage reduction | PASS |
| Season-cluster uncertainty review | PASS |
| Source, leakage, identity, and runtime | PASS |

Failed gates: `no_repeated_position_regression|no_severe_fp_increase`.

## Prospective 2026 freeze

- PYF frozen: **yes**, `231` valid scores on the controlled population.
- Exact GAUNTLET_081 frozen: **yes**, `231` valid scores.
- Exact current-board comparator frozen: **yes**, `232` native valid rows, separately caveated.
- Ridge passed every historical gate: **no**.
- New review-only challenger frozen: **no**.

The common freeze timestamp is `2026-07-10T22:34:06Z`. The snapshots are review-only tracking artifacts. They do not change rankings, production formulas, the app, runtime behavior, or source status.
