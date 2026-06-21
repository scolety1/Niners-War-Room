# NWR Backtest V0 Design And Results - 2026-06-21

Owner: Master/Main HQ

Status: GREEN for local-only first serious backtest scaffold and run. YELLOW
for interpretation. This does not approve private value, rankings, hidden sort,
recommendations, simulations, final draft decisions, deployment, Mock Draft
logic, or `latest_approved`.

## Purpose

Backtest V0 measures whether expanded factual nflverse feature sets improve
next-season NWR fantasy football prediction versus a simple prior-season
production baseline.

This is a research evaluation only. Outputs are local-only and must not be used
as draft advice or model/private-value changes.

## Local-Only Artifact Path

`C:\NWR_SHARED_DATA\backtests\backtest_v0_20260621_first_serious`

Local-only files created:

- `feature_dataset_baseline.csv`
- `feature_dataset_expanded.csv`
- `labels.csv`
- `metrics_by_position.csv`
- `metrics_by_year.csv`
- `predictions.csv`
- `backtest_v0_report.md`
- `build_manifest.json`
- `run_manifest.json`

None of these artifacts are committed to Git.

## Seasons And Positions

Input seasons loaded:

- 2018
- 2019
- 2020
- 2021
- 2022
- 2023
- 2024
- 2025

Feature seasons:

- 2018 through 2024

Target seasons:

- 2019 through 2025

Rolling-origin evaluation seasons:

- 2021 through 2025, after requiring at least two prior target seasons for
  training.

Core positions:

- QB
- RB
- WR
- TE

Excluded from Backtest V0:

- K
- DST
- IDP

## NWR Scoring Used For Labels

Backtest V0 computes NWR scoring directly from factual stat columns instead of
using `fantasy_points` or `fantasy_points_ppr`.

Scoring:

- pass yards: 1 per 30
- pass TD: 3
- interception: -1
- rush yards: 1 per 10
- receiving yards: 1 per 10
- rush TD: 4
- receiving TD: 4
- rush first down: 0.4
- receiving first down: 0.4
- return yards: 1 per 30
- return TD / special teams TD: 4
- 2-point conversions: 2
- fumble lost: -1
- reception: 0

Labels created:

- next-season NWR fantasy points
- next-season NWR fantasy points per game
- positional finish buckets:
  - QB T12
  - RB T12, RB T24
  - WR T12, WR T24, WR T36
  - TE T12

## Feature Sets

### Baseline

Baseline uses simple season-S factual production:

- position and identity
- prior-season games
- prior-season NWR points and PPG computed from factual stats
- pass attempts/completions/yards/TD/INT
- carries, rushing yards, rushing TDs, rushing first downs
- targets, receptions, receiving yards, receiving TDs, receiving first downs
- 2-point conversions
- punt/kickoff return yards and attempts
- special teams TDs
- fumbles lost
- snap count fields when available

### Expanded Factual

Expanded factual adds low-risk factual context:

- age at season end
- years experience
- draft round/pick/log pick
- weekly roster active/status-derived availability
- depth-chart best rank where available
- air yards
- YAC
- first-down rates
- red-zone and goal-line rush/target features derived from opportunity PBP
- QB rushing role and scramble count when safely derivable
- sack, sack-fumble, and sack-yard context
- team plays, pass rate, run rate, and offensive TD environment

### YELLOW Challenger Features

YELLOW challenger fields were not run in Backtest V0 main models:

- EPA
- CPOE
- WOPR
- PACR
- RACR
- target share
- air-yards share
- expected/diff fields
- participation-derived 2023+ fields
- PFR/FTN advanced fields

## Blocked Inputs

Backtest V0 blocks these from input features:

- ADP
- Sleeper ADP
- market rankings
- trade calculators
- projections
- external rankings
- `fantasy_points`
- `fantasy_points_ppr`
- hidden composite scores
- target-season future data

## Method

`sklearn` was not available in the active runtime, so Backtest V0 used a local
numpy ridge-regression fallback with fold-local preprocessing.

Design:

- season S features predict season S+1 outcomes
- rolling-origin validation
- position-specific models
- preprocessing statistics fit inside train folds only
- target-season data excluded from feature rows

Methods run:

- `rolling_origin_numpy_ridge`

YELLOW challenger models:

- not run

## Dataset And Output Counts

| Artifact | Rows | SHA256 |
| --- | ---: | --- |
| `feature_dataset_baseline.csv` | 3,108 | `f6030f7e4e062d5a8d1007c40f29bb90367a4b4a656e3b7e06c1fdc593ca99d8` |
| `feature_dataset_expanded.csv` | 3,108 | `a11daf801f51ccecf39ca240385297e6735c6b6c1ff1d7fe7eb715c5a8f96165` |
| `labels.csv` | 3,108 | `63d1f76627f00578a1152c83fd0339d6cfd061b732f07480f74921f2f28986d3` |
| `metrics_by_position.csv` | 8 | `c6ac98f4e70111927243aacc7148e4f9747addca81c83d976cb42c5bc0f87aeb` |
| `metrics_by_year.csv` | 40 | `29cf6ec5ef16a49c6d2cf0beddedd2aeee836c12fba538ea49824c5df679b736` |
| `predictions.csv` | 4,536 | `1df543009b60bfe4796458222f0aaffe65fb175cd2c0fbcc2e857a439ab364b6` |

## Metrics By Position

| Feature set | Position | N | MAE points | RMSE points | Spearman | Top-N hit rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | QB | 317 | 59.515 | 77.178 | 0.675 | 0.333 |
| Expanded factual | QB | 317 | 62.174 | 80.992 | 0.659 | 0.333 |
| Baseline | RB | 570 | 43.871 | 58.267 | 0.669 | 0.375 |
| Expanded factual | RB | 570 | 43.805 | 58.326 | 0.660 | 0.375 |
| Baseline | WR | 886 | 30.495 | 40.633 | 0.698 | 0.472 |
| Expanded factual | WR | 886 | 30.822 | 41.189 | 0.705 | 0.444 |
| Baseline | TE | 495 | 21.754 | 45.440 | 0.736 | 0.250 |
| Expanded factual | TE | 495 | 22.249 | 43.813 | 0.699 | 0.333 |

## Expanded Factual Result Versus Baseline

Positive values mean expanded factual improved the metric versus baseline.

| Position | MAE improvement | RMSE improvement | Spearman improvement | Top-N hit improvement |
| --- | ---: | ---: | ---: | ---: |
| QB | -2.659 | -3.814 | -0.016 | 0.000 |
| RB | 0.065 | -0.059 | -0.009 | 0.000 |
| WR | -0.326 | -0.557 | 0.007 | -0.028 |
| TE | -0.495 | 1.627 | -0.037 | 0.083 |

Interpretation:

- Expanded factual features did not produce a clean overall win in V0.
- RB had a tiny MAE improvement but slightly worse RMSE and rank correlation.
- WR had a small rank-correlation improvement but worse MAE/RMSE and Top-N hit.
- TE improved RMSE and Top-N hit rate but worsened MAE and rank correlation.
- QB was worse on MAE, RMSE, and rank correlation.

The result is useful because it argues against blindly promoting expanded
features. Feature groups need ablation, stronger missingness handling, and
position-specific refinement before any model/private-value proposal.

## Leakage Guard Results

Guardrails enforced:

- No ADP/market/ranking/projection fields in feature datasets.
- No `fantasy_points` or `fantasy_points_ppr` input features.
- YELLOW challenger fields excluded from main feature sets.
- Season S features predict season S+1 labels.
- Fold preprocessing fit only on train folds.
- Participation-derived 2023+ fields were not used in main features.
- K/DST/IDP excluded from core Backtest V0.

## Limitations

- `sklearn` was unavailable, so logistic bucket models, Brier score, and
  calibration were not implemented in V0.
- Top-N hit rate was evaluated from point predictions, not a dedicated
  classifier.
- Expanded features were grouped together; V0 does not isolate which expanded
  family helped or hurt.
- Direct live injury status, true routes run, true TPRR, direct OL grades, and
  YELLOW advanced sources remain outside the main V0 feature sets.

## Recommended Next Steps

1. Run position-specific ablation:
   - baseline plus roster metadata
   - baseline plus air yards/YAC
   - baseline plus red-zone/goal-line
   - baseline plus team environment
   - baseline plus snap/depth context
2. Add missingness coverage reports for each feature family by position/year.
3. Add simple non-linear baselines only after leakage tests expand.
4. Keep YELLOW challenger features isolated in a separate challenger run.
5. Do not propose private-value or Mock Draft integration until an ablation run
   shows stable incremental value.

## Master Verdict

GREEN for Backtest V0 scaffold and local-only run.

YELLOW for model usefulness because expanded factual features were mixed and not
stable enough for promotion.

RED for any direct use of these results as private value, rankings, hidden sort,
recommendations, simulations, or final draft-day decisions.
