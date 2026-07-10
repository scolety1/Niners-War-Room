# Formula Miss Taxonomy / Red Team Review V1

## Verdict

`GREEN_FORMULA_RED_TEAM_FOUND_ACTIONABLE_MISS_REDUCTION_PATH`

## Scope

This lane red-teamed accepted review-only formula references and did not tune formulas, run a new Gauntlet, run ranking simulation, change rankings, change app/runtime behavior, promote sources, push, merge, or write canonical `local_exports`.

Remote HQ verified: `b125be9ee73f1adc3487c1fa69ae954e8e49790f`.

Prior canonicalization commit verified: `8fefe3d9c270df753f78115ee8a1450f1afbd4e9`.

## Formula References Analyzed

1. `PYF_BASELINE`
2. `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_DEPTH_STABILITY_PCT100`
3. `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_SNAP_NOT_LOW_PCT100`
4. `GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_FFOPPORTUNITY_PCT10`

## Window Separation

- Full-history: `2013-2025`
- Broad-window: `2014-2025`
- Partial modern window: `2022-2025`

Partial-window results remain separate and are not full-history comparable.

## Miss Definitions

False positives are rows where formula rank is inside the accepted position startable threshold but the historical `label_startable_hit` is false. False negatives are rows where formula rank is outside that threshold but `label_startable_hit` is true.

Severe misses use the same accepted position thresholds and flag extreme rank/outcome gaps. Outcome labels are the existing Formula Data Mart labels only.

## Top False-Positive Categories

prior_production_trap (1457), injury_availability_caveat (1346), old_late_lifecycle_decline (229), veteran_high_volume_decline (189), unknown (67), low_snap_depth_warning (27)

## Top False-Negative Categories

availability_rebound_or_clean_report_context (835), young_breakout (600), starter_depth_chart_signal (583), snap_depth_role_promotion_signal (482), expected_fantasy_opportunity_signal (162), sparse_history_breakout (133)

## Formula Comparison

Best PYF miss reducer: `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_SNAP_NOT_LOW_PCT100`, net miss reduction `54` on `5122` comparable rows.

Formula creating the most new misses vs PYF: `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_DEPTH_STABILITY_PCT100`, new misses `146`. This is expected to some degree because each additive ingredient resolves some PYF misses while creating others near the threshold.

## Actionable Interpretation

The most actionable red-team path is `Sparse-history / young-player breakout modeling`. Existing formulas reduce broad miss volume mostly through production stability and snap/depth context, but false negatives remain concentrated in young, sparse-history, early-career, and opportunity-emergence rows. False positives remain concentrated around prior-production traps, older/late lifecycle risk, role/depth warnings, and availability caveats.

## Ranking Simulation Decision

Review-only ranking simulation remains not justified. The miss clusters are understandable but not resolved enough to treat the current best candidates as stable board projection tools.

## Source / Use Gate Summary

Sidecar joins used for miss context: `{'snap_depth': 5518, 'injury': 5518, 'rookie_draft': 3870, 'receiving_opportunity': 5518, 'epa': 5360, 'team_env': 5518, 'ffopportunity': 1740, 'ngs': 944}`.

All source fields used here came from accepted review-only artifacts. They remain not production/model-use and not ranking-integration approved.
