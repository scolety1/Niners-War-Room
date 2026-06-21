# NWR Backtest V1 Feature Cleanup Results - 2026-06-21

Owner: Master/Main HQ

Status: GREEN for local-only Backtest V1 scaffold and run. YELLOW for model
usefulness. This does not approve private value, rankings, hidden sort,
recommendations, simulations, final draft decisions, deployment, Mock Draft
logic, or `latest_approved`.

## Purpose

Backtest V1 cleaned the V0 expanded factual feature set by making feature
whitelists position-specific, adding explicit metadata missingness indicators,
and rerunning rolling-origin evaluation.

The goal was not to add more signals. The goal was to reduce noisy role-mismatch
features and test whether a disciplined factual feature set improves over a
simple prior-season baseline.

## Local-Only Artifact Path

`C:\NWR_SHARED_DATA\backtests\backtest_v1_feature_cleanup_20260621`

Local-only files created:

- `feature_dataset_v1_baseline.csv`
- `feature_dataset_v1_clean_expanded.csv`
- `labels_v1.csv`
- `metrics_by_position_v1.csv`
- `metrics_by_year_v1.csv`
- `predictions_v1.csv`
- `feature_missingness_summary_v1.csv`
- `feature_whitelist_by_position_v1.csv`
- `excluded_features_v1.csv`
- `backtest_v1_feature_cleanup_report.md`
- `build_manifest_v1.json`
- `run_manifest.json`

None of these artifacts are committed to Git.

## Seasons And Positions

Input seasons loaded:

- 2018 through 2025

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

Excluded from Backtest V1:

- K
- DST
- IDP
- ADP/market/projection fields
- `fantasy_points` and `fantasy_points_ppr`
- YELLOW challenger fields such as EPA, CPOE, WOPR, PACR, RACR, share,
  expected, and diff fields

## Feature Sets

### V0 Baseline Reference

The V0 baseline feature set was rerun as a reference. This preserves the prior
comparison point.

### V1 Baseline

The V1 baseline uses position-specific prior-season production and volume:

- QB: passing, QB rushing, sacks/fumbles, and NWR scoring-aligned production
- RB: rushing, receiving role, fumbles, snaps, and NWR scoring-aligned production
- WR/TE: receiving role, fumbles, snaps, and NWR scoring-aligned production

Return usage was excluded from the primary V1 baseline role features.

### V1 Clean Expanded Factual

The clean expanded feature set adds only position-appropriate factual context:

- age and years experience
- draft round/pick/log pick
- explicit metadata missingness indicators
- active-week and depth-chart context when available
- QB sack/scramble/team-environment context
- RB red-zone and goal-line rush context
- WR/TE air-yard and YAC context
- safe prior-season rates with denominator guards

No YELLOW challenger features were run in the primary V1 result.

## Imputation And Missingness

Role/stat absence can be zero-filled where zero means no usage. Metadata fields
are zero-filled only with explicit missing indicators.

Missingness summary:

| Position | age_missing | draft_capital_missing | snap_pct_missing | air_yards_missing |
| --- | ---: | ---: | ---: | ---: |
| QB | 0 / 424 | 274 / 424 | 424 / 424 | 37 / 424 |
| RB | 0 / 789 | 439 / 789 | 788 / 789 | 329 / 789 |
| WR | 0 / 1214 | 700 / 1214 | 1212 / 1214 | 22 / 1214 |
| TE | 0 / 681 | 400 / 681 | 681 / 681 | 9 / 681 |

Important caveat: `snap_pct_missing` is effectively universal in this run. Treat
snap percentage as YELLOW until the snap-count source join is audited separately.

## Excluded Feature Summary

Top exclusion reasons from `excluded_features_v1.csv`:

| Count | Reason |
| ---: | --- |
| 65 | not in position-specific V1 whitelist |
| 34 | inappropriate receiver rushing or passing feature |
| 20 | return or special-teams usage excluded from primary role features |
| 16 | inappropriate QB receiving role feature |
| 12 | team environment limited to QB in primary V1 |
| 7 | inappropriate RB passing feature |

## Metrics By Position

| Feature set | Position | N | MAE points | RMSE points | Spearman | Top-N hit |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| V0 baseline reference | QB | 317 | 59.515 | 77.178 | 0.675 | 0.333 |
| V1 baseline | QB | 317 | 59.287 | 77.295 | 0.678 | 0.250 |
| V1 clean expanded | QB | 317 | 63.593 | 81.493 | 0.669 | 0.333 |
| V0 baseline reference | RB | 570 | 43.871 | 58.267 | 0.669 | 0.375 |
| V1 baseline | RB | 570 | 43.000 | 58.268 | 0.677 | 0.417 |
| V1 clean expanded | RB | 570 | 43.491 | 58.581 | 0.668 | 0.375 |
| V0 baseline reference | WR | 886 | 30.495 | 40.633 | 0.698 | 0.472 |
| V1 baseline | WR | 886 | 29.865 | 39.459 | 0.719 | 0.500 |
| V1 clean expanded | WR | 886 | 29.412 | 38.814 | 0.732 | 0.361 |
| V0 baseline reference | TE | 495 | 21.754 | 45.440 | 0.736 | 0.250 |
| V1 baseline | TE | 495 | 19.149 | 26.075 | 0.745 | 0.333 |
| V1 clean expanded | TE | 495 | 19.630 | 26.696 | 0.740 | 0.333 |

## Clean Expanded Versus V1 Baseline

Positive values mean clean expanded improved over V1 baseline.

| Position | MAE improvement | RMSE improvement | Spearman improvement | Top-N hit improvement | V1 read |
| --- | ---: | ---: | ---: | ---: | --- |
| QB | -4.306 | -4.198 | -0.009 | 0.083 | Baseline preferred |
| RB | -0.490 | -0.313 | -0.010 | -0.042 | Baseline preferred |
| WR | 0.453 | 0.644 | 0.013 | -0.139 | YELLOW: signal, but Top-N worsened |
| TE | -0.481 | -0.621 | -0.005 | 0.000 | Baseline preferred |

Year-stability read:

- QB: clean expanded improved at least two metrics in 1 of 5 test years.
- RB: clean expanded improved at least two metrics in 3 of 5 test years, but
  aggregate metrics still favored V1 baseline.
- WR: clean expanded improved at least two metrics in 5 of 5 test years, but
  aggregate Top-N hit rate materially worsened.
- TE: clean expanded improved at least two metrics in 2 of 5 test years, but
  aggregate metrics favored V1 baseline.

## Interpretation

Backtest V1 produced a cleaner and more useful baseline than V0. The
position-specific baseline improved the prior reference for RB, WR, and TE and
slightly improved QB MAE/Spearman while worsening QB Top-N.

The clean expanded factual feature set is still not ready for promotion:

- QB, RB, and TE favor V1 baseline.
- WR shows stable MAE/RMSE/Spearman improvement, but Top-N hit rate drops from
  0.500 to 0.361, which is too costly for draft-use ranking decisions.
- Snap percentage is not reliable in this run because nearly all rows are flagged
  as missing.

The safest current conclusion is:

- Use V1 baseline as the preferred backtest baseline for future comparisons.
- Keep clean expanded factual features as YELLOW research-only.
- Do not integrate these features into private value, rankings, hidden sort,
  recommendations, simulations, or Mock Draft behavior.

## Artifact Checksums

| Artifact | Rows | SHA256 |
| --- | ---: | --- |
| `feature_dataset_v1_baseline.csv` | 3108 | `8630aa16471d04f3af5f5758decce86a3695975fa50a7884b1d79e5faf1c4a6e` |
| `feature_dataset_v1_clean_expanded.csv` | 3108 | `b72c7440d810c25ce4b4b2b7fc6829e9658655b21c7d1235fa74741772e713b7` |
| `labels_v1.csv` | 3108 | `63d1f76627f00578a1152c83fd0339d6cfd061b732f07480f74921f2f28986d3` |
| `metrics_by_position_v1.csv` | 12 | `140e454b92f6031e719676b2a3991bacbe8ac9a7ecaefffe755bc03615fa5082` |
| `metrics_by_year_v1.csv` | 60 | `9f4e61d2a52f6bccd69a1409b7eaf740152982729e8297305f07267a07f25870` |
| `feature_missingness_summary_v1.csv` | 16 | `bf5e3444a184b6b57ed07ebe683e97fb2743e5dca5bb576592a11cff481afe61` |
| `feature_whitelist_by_position_v1.csv` | 177 | `04d3be56ab05e9f0593734dd124af075f4d08326d445dc001f723c47a9219bc3` |
| `excluded_features_v1.csv` | 154 | `6c6ae22d1e0b0b022a5a0fbe109584dc8ca1c70fdb60f8a7d075cb8ddb223cff` |

## Guardrail Validation

- `latest_approved` was not touched.
- The pinned live-test snapshot was not touched.
- No `C:\NWR_SHARED_DATA` files are committed.
- No raw backtest, nflverse, or API data is committed.
- No ADP, Sleeper ADP, market, projection, trade calculator, or FantasyPros
  fields are used.
- `fantasy_points` and `fantasy_points_ppr` are not input features.
- V1 uses fold-local preprocessing through the existing numpy ridge fallback.
- No simulations, recommendations, Mock Draft behavior, deployment, scheduled
  tasks, or Lane Exchange approvals were created.

## Recommended Next Steps

1. Treat V1 baseline as the preferred baseline for future backtests.
2. Run a narrow WR-only ablation for air yards/YAC/rates, with Top-N hit rate as
   the gating metric.
3. Audit snap-count join coverage before using `offense_pct` or snap-share
   features.
4. Run RB red-zone/goal-line as a separate ablation because year-level signal was
   mixed but not hopeless.
5. Keep YELLOW challenger fields out until the factual feature families prove
   stable.

## Master Verdict

GREEN for Backtest V1 scaffold, local-only dataset generation, and evaluation.

YELLOW for feature usefulness. V1 baseline is better disciplined, but clean
expanded factual features are not ready for model/private-value use.

RED for any use as draft advice, private value, rankings, hidden sort,
recommendations, simulations, final draft decisions, deployment, or
`latest_approved`.
