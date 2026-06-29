# RB Elite 5Y Outcome Diagnostic

Date: 2026-06-30

Lane: `work/rb-elite-5y-outcome-diagnostic-20260630`

Status: `GREEN_DIAGNOSTIC_COMPLETE`

This is a review-only / diagnostic-only Outcome V2 lane. It does not create app-facing
probabilities, Rankings wiring, Dynasty Rank changes, hidden sort, trade value, pick value,
Live Draft behavior, Mock Draft behavior, or any production model artifact.

## Executive Summary

The RB elite 5Y diagnostic explains why the earlier RB T6/T12 Within 5Y fields failed the
generic Outcome V2 calibration gate and tests whether RB T10 Within 5Y is a better elite
threshold.

The richer RB-only diagnostic improves Brier score and aggregate calibration versus rolling
prevalence for all tested thresholds, including RB T6 and RB T12. However, the missed-prior-season
slice remains too sparse for promotion: only 4 validation rows carry `missed_prior_season_flag=true`.
The low-sample recent-season slice is larger but still a caveat group. Because of that subgroup
instability, this report recommends no new RB elite field for app/display promotion yet.

Recommendation:

| Target | Recommendation |
| --- | --- |
| RB T6 Within 5Y | `test-only` |
| RB T10 Within 5Y | `keep blocked` |
| RB T12 Within 5Y | `test-only` |
| RB T24 Within 5Y | `test-only` in this diagnostic; already separately validated in Outcome V2 |
| RB T36 Within 5Y | `test-only` in this diagnostic; already separately validated in Outcome V2 |

RB T10 did not clearly outperform both T6 and T12 on weighted calibration error, so it remains
blocked under the lane rule.

## Sources

Inputs are approved/review-only historical veteran NFL facts already present locally:

| Source | Path | Use |
| --- | --- | --- |
| Extended anchor horizon labels | `C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels_extended\outcome_v2_extended_anchor_horizon_labels.csv` | Anchor rows, complete/censored 5Y windows |
| Extended season outcome labels | `C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels_extended\outcome_v2_extended_season_outcome_labels.csv` | T6/T10/T12/T24/T36 target construction from factual position finishes |
| Player-season usage panel | `C:\NWR_SHARED_DATA\nfl_usage_cache\target_backtest\historical_expansion\panels\player_season_core_usage_panel.csv` | Usage and role context where available |
| Joined usage panel | `C:\NWR_SHARED_DATA\nfl_usage_cache\target_backtest\historical_expansion\nfl_usage_expanded_target_backtest_joined_panel_v0.csv` | Red-zone and joined factual usage context where available |

Blocked inputs were not used: ADP, market values, DynastyProcess, CFBD, Gmail, vendor data,
RotoWire, FantasyPros, projections, analyst ranks, trade values, true routes, TPRR, YPRR,
injury projections, medical comeback assumptions, and rookie/prospect college data.

The local attachment cache did not expose a separately readable RB/T10 Deep Research file, so the
diagnostic implementation follows the detailed Deep Research design requirements included in the
task prompt.

## Dataset

Generated diagnostic dataset:

`C:\NWR_SHARED_DATA\outcome_v2_horizon\rb_elite_5y_diagnostic\rb_elite_5y_diagnostic_dataset.csv`

Rows: 1,937 RB anchor rows.

Complete 5Y rows by target:

| Target | Complete rows | Positives | Negatives | Censored/missing |
| --- | ---: | ---: | ---: | ---: |
| RB T6 Within 5Y | 224 | 60 | 164 | 1,713 |
| RB T10 Within 5Y | 224 | 86 | 138 | 1,713 |
| RB T12 Within 5Y | 224 | 101 | 123 | 1,713 |
| RB T24 Within 5Y | 224 | 137 | 87 | 1,713 |
| RB T36 Within 5Y | 224 | 160 | 64 | 1,713 |

Incomplete windows remain censored or `Not enough information`; they are not treated as misses.

## Feature Families Tested

Feature families are RB-only and factual:

- Season totals: current season fantasy points, finish, rushing/receiving yards, first downs.
- Per-game rates: points, touches, opportunities, yards.
- Per-opportunity rates: yards, first downs, points per opportunity.
- Role share / availability: usage games, offense percentage, team opportunity share, red-zone touches.
- Age / experience: experience-year count and seasons since first observed. Age itself is unavailable and remains `Not enough information`.
- Recency-weighted summaries: 2-year and 3-year points, points per game, and games.
- Last materially active season: factual non-medical active-season definition only.
- Missed-prior-season flags: factual prior-row/games context only.
- Limited-recent-sample flags: factual sample-size caveat only.

`Last healthy season` was not used. The implemented language is `last materially active season`.

Materially active definition:

`games_played>=8 or fantasy_points>=100 or position_finish<=36`

This is a factual participation/production rule, not medical inference.

## Rolling Validation

Validation is season-ordered. Each validation fold trains only on complete RB anchor rows from
earlier anchor seasons and validates on the next complete anchor season. The comparison baseline is
rolling train prevalence. The model family is a deterministic L2-penalized logistic regression
implemented locally for this diagnostic.

Best diagnostic result by target:

| Target | Best feature set | Validation rows | Positives | Model Brier | Baseline Brier | Delta | Weighted calibration error | Large-bucket max error | Status |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| RB T6 Within 5Y | usage_role_context | 169 | 49 | 0.144510 | 0.209950 | 0.065440 | 0.030184 | 0.042204 | PASS_DIAGNOSTIC_VALIDATION |
| RB T10 Within 5Y | material_activity_caveats | 169 | 66 | 0.162232 | 0.242193 | 0.079961 | 0.041021 | 0.126227 | PASS_DIAGNOSTIC_VALIDATION |
| RB T12 Within 5Y | material_activity_caveats | 169 | 78 | 0.168866 | 0.251706 | 0.082840 | 0.047350 | 0.052747 | PASS_DIAGNOSTIC_VALIDATION |
| RB T24 Within 5Y | usage_role_context | 169 | 104 | 0.166658 | 0.237116 | 0.070458 | 0.052220 | 0.141959 | PASS_DIAGNOSTIC_VALIDATION |
| RB T36 Within 5Y | material_activity_caveats | 169 | 121 | 0.151988 | 0.203584 | 0.051596 | 0.043373 | 0.005903 | PASS_DIAGNOSTIC_VALIDATION |

The aggregate diagnostic pass is not a display approval because the caveat slices remain thin.

## T10 Diagnostic

Best weighted calibration errors:

| Target | Best weighted calibration error |
| --- | ---: |
| RB T6 Within 5Y | 0.030184 |
| RB T10 Within 5Y | 0.041021 |
| RB T12 Within 5Y | 0.047350 |

T10 improves Brier versus baseline, but it does not beat T6 by calibration and does not beat both
T6 and T12 by the required clear margin. Under the task rule, T10 remains `keep blocked`.

## Missed-Season And Low-Sample Slices

Best-model error slices:

| Target | Slice | Rows | Positives | Observed | Predicted | Abs calibration error |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| RB T6 | missed_prior=true | 4 | 0 | 0.000000 | 0.196856 | 0.196856 |
| RB T6 | limited_recent_sample=true | 35 | 3 | 0.085714 | 0.140248 | 0.054534 |
| RB T10 | missed_prior=true | 4 | 1 | 0.250000 | 0.245306 | 0.004694 |
| RB T10 | limited_recent_sample=true | 35 | 5 | 0.142857 | 0.227728 | 0.084871 |
| RB T12 | missed_prior=true | 4 | 1 | 0.250000 | 0.300527 | 0.050527 |
| RB T12 | limited_recent_sample=true | 35 | 6 | 0.171429 | 0.304722 | 0.133294 |
| RB T24 | missed_prior=true | 4 | 1 | 0.250000 | 0.427177 | 0.177177 |
| RB T24 | limited_recent_sample=true | 35 | 14 | 0.400000 | 0.405140 | 0.005140 |
| RB T36 | missed_prior=true | 4 | 1 | 0.250000 | 0.396965 | 0.146965 |
| RB T36 | limited_recent_sample=true | 35 | 18 | 0.514286 | 0.536114 | 0.021828 |

The missed-prior-season slice is too small for promotion. If a future display artifact ever uses
these fields, rows with missed-prior-season or materially limited recent samples should remain
`Not enough information` until a separate gate validates that subgroup.

## Why RB T6/T12 Failed Earlier

The earlier generic Outcome V2 validation used a broad prior-finish empirical bucket model. It
beat prevalence for RB T6/T12 5Y but failed calibration:

- RB T6 Within 5Y: weighted calibration error 0.202095.
- RB T12 Within 5Y: weighted calibration error 0.185918 and large-bucket error 0.317420.

This diagnostic shows the failure was not solely event scarcity. RB-specific factual features,
especially role/usage and material-activity caveats, materially reduce aggregate calibration error.
The remaining blocker is subgroup stability around missed/limited recent seasons, not the lack of
any learnable RB signal.

## Artifacts

Generated review-only artifacts, not committed:

- `C:\NWR_SHARED_DATA\outcome_v2_horizon\rb_elite_5y_diagnostic\rb_elite_5y_diagnostic_dataset.csv`
- `C:\NWR_SHARED_DATA\outcome_v2_horizon\rb_elite_5y_diagnostic\rb_elite_5y_target_summary.csv`
- `C:\NWR_SHARED_DATA\outcome_v2_horizon\rb_elite_5y_diagnostic\rb_elite_5y_fold_metrics.csv`
- `C:\NWR_SHARED_DATA\outcome_v2_horizon\rb_elite_5y_diagnostic\rb_elite_5y_calibration_buckets.csv`
- `C:\NWR_SHARED_DATA\outcome_v2_horizon\rb_elite_5y_diagnostic\rb_elite_5y_error_slices.csv`
- `C:\NWR_SHARED_DATA\outcome_v2_horizon\rb_elite_5y_diagnostic\rb_elite_5y_recommendations.csv`
- `C:\NWR_SHARED_DATA\outcome_v2_horizon\rb_elite_5y_diagnostic\rb_elite_5y_manifest.csv`

## Guardrails

- Review-only diagnostic outputs only.
- No current-player probabilities.
- No app UI changes.
- No Rankings / Outcome Lens changes.
- No Dynasty Rank, tier, hidden sort, trade value, or pick value changes.
- No Live Draft, Mock Draft, or draft runtime changes.
- No ADP, market, DynastyProcess, projection, analyst, vendor, Gmail, CFBD, or rookie/prospect input.
- No medical-style recovery fields.
- Missing and censored targets remain `Not enough information`, not 0.

## Recommended Next Step

Keep RB T10 blocked. Keep RB T6/T12 elite 5Y fields out of app-facing Outcome V2 display. If this
diagnostic is continued, the next lane should test a candidate policy where missed-prior-season and
limited-recent-sample rows are explicitly gated to `Not enough information`, then rerun the RB-only
validation on non-caveat rows only. That should still be review-only until separately approved.
