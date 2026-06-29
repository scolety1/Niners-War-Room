# RB Intermediate 5Y Diagnostic Report

## Verdict

GREEN_DIAGNOSTIC_COMPLETE.

This lane is review-only and diagnostic-only. It does not create app-facing
probabilities, does not change Outcome Lens, and does not change Dynasty Rank,
tiers, hidden sort, trade value, pick value, Live Draft, Mock Draft, or app
runtime behavior.

## Source Data

Approved/review-only local factual NFL sources used:

- `C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels_extended\outcome_v2_extended_anchor_horizon_labels.csv`
- `C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels_extended\outcome_v2_extended_season_outcome_labels.csv`
- `C:\NWR_SHARED_DATA\nfl_usage_cache\target_backtest\historical_expansion\panels\player_season_core_usage_panel.csv`
- `C:\NWR_SHARED_DATA\nfl_usage_cache\target_backtest\historical_expansion\nfl_usage_expanded_target_backtest_joined_panel_v0.csv`

No ADP, market values, DynastyProcess, CFBD, vendor, projection, analyst rank,
trade value, true routes, TPRR, YPRR, or medical projection inputs were used.

Generated artifacts, not committed:

- `C:\NWR_SHARED_DATA\outcome_v2_horizon\rb_intermediate_5y_diagnostic\rb_intermediate_5y_diagnostic_dataset.csv`
- `C:\NWR_SHARED_DATA\outcome_v2_horizon\rb_intermediate_5y_diagnostic\rb_intermediate_5y_target_summary.csv`
- `C:\NWR_SHARED_DATA\outcome_v2_horizon\rb_intermediate_5y_diagnostic\rb_intermediate_5y_fold_metrics.csv`
- `C:\NWR_SHARED_DATA\outcome_v2_horizon\rb_intermediate_5y_diagnostic\rb_intermediate_5y_calibration_buckets.csv`
- `C:\NWR_SHARED_DATA\outcome_v2_horizon\rb_intermediate_5y_diagnostic\rb_intermediate_5y_error_slices.csv`
- `C:\NWR_SHARED_DATA\outcome_v2_horizon\rb_intermediate_5y_diagnostic\rb_intermediate_5y_recommendations.csv`
- `C:\NWR_SHARED_DATA\outcome_v2_horizon\rb_intermediate_5y_diagnostic\rb_intermediate_5y_manifest.csv`

## Target Construction

RB intermediate targets were built directly from factual future season
`position_finish` rows. Pre-existing intermediate labels were not required.

Incomplete five-year windows remain censored and emit `Not enough information`.
They are not treated as misses or zeroes.

| Target | Complete rows | Positives | Prevalence | Censored/missing |
| --- | ---: | ---: | ---: | ---: |
| RB T12 Within 5Y | 224 | 101 | 0.450893 | 1713 |
| RB T15 Within 5Y | 224 | 110 | 0.491071 | 1713 |
| RB T18 Within 5Y | 224 | 121 | 0.540179 | 1713 |
| RB T20 Within 5Y | 224 | 132 | 0.589286 | 1713 |
| RB T24 Within 5Y | 224 | 137 | 0.611607 | 1713 |

Complete anchor seasons: `2012|2013|2014|2015|2016|2017|2018|2019`.

## Feature Families Tested

- Season totals.
- Per-game rates.
- Per-opportunity rates.
- Role share / availability.
- Recency-weighted multi-year summaries.
- Last materially active season.
- Missed-prior-season flags.
- Limited-recent-sample flags.

`Last healthy season` language was not used. The implemented factual label is
`last_materially_active_season`, defined as:

`games_played>=8 or fantasy_points>=100 or position_finish<=36`

## Best Result By Target

| Target | Best feature set | Brier | Baseline Brier | Delta | Weighted calibration error | Max large-bucket error | Fold win rate | Recommendation |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| RB T12 Within 5Y | role_availability | 0.229327 | 0.251706 | 0.022379 | 0.052054 | 0.032011 | 0.833333 | test_only |
| RB T15 Within 5Y | role_availability | 0.230097 | 0.251751 | 0.021654 | 0.035491 | 0.018895 | 0.833333 | test_only |
| RB T18 Within 5Y | season_totals | 0.185050 | 0.249101 | 0.064052 | 0.067635 | 0.119535 | 1.000000 | test_only |
| RB T20 Within 5Y | role_availability | 0.220299 | 0.241369 | 0.021071 | 0.037830 | 0.020372 | 0.666667 | test_only |
| RB T24 Within 5Y | role_availability | 0.216568 | 0.237116 | 0.020548 | 0.028167 | 0.005265 | 0.833333 | test_only |

## Intermediate Threshold Result

RB T15, T18, and T20 all show diagnostic signal, but none is safe for a future
display-candidate promotion from this lane alone.

Reason: the missed-prior-season validation slice remains too sparse and unstable.
The true missed-prior-season slice has only 4 validation rows. Limited-recent
sample slices have 35 rows and remain caveated. Following the Deep Research
recommendation, these rows should prefer `Not enough information` until a later
source-approved availability/injury context layer is validated.

RB T18 is the strongest intermediate diagnostic candidate by Brier improvement,
but its recommendation remains `test_only`.

## Comparison Against T12 And T24

- RB T12 remains blocked from app display in current Outcome V2 because the long
  horizon signal is not stable enough for elite RB interpretation.
- RB T24 is already display-safe through the main Outcome V2 validation lane;
  this diagnostic does not change that status.
- RB T15/T18/T20 provide a useful middle-ground experiment but do not clear the
  missed/limited sample caveat needed for future display-candidate review.

## Stop-Condition Result

No intermediate RB 5Y threshold is promoted to `safe_for_display_candidate`.

Current status:

- RB T15 Within 5Y: `test_only`
- RB T18 Within 5Y: `test_only`
- RB T20 Within 5Y: `test_only`
- RB T12 Within 5Y: `test_only` in this diagnostic, still blocked for app display
- RB T24 Within 5Y: `test_only` in this diagnostic, already handled by Outcome V2

## Guardrails

- Review-only / diagnostic-only.
- No Rankings or Outcome Lens changes.
- No app-facing probabilities.
- No Dynasty Rank, tier, hidden sort, trade value, or pick value changes.
- No Live Draft or Mock Draft changes.
- No medical inference, recovery projection, or injury-risk score.
- Missing or censored windows stay `Not enough information`.
- Raw/generated shared-data artifacts stay outside Git.
