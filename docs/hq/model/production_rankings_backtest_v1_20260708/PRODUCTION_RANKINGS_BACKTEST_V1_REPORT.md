# Production Rankings Backtest V1 Report

## Verdict

`YELLOW_PRODUCTION_RANKINGS_ACCURACY_PARTIAL_WITH_CAVEATS`

Exact replay of the current production ranking surface is not safely measurable from local evidence. The current surface is a pinned 240-row full-player-board artifact sorted by `nwr_dynasty_score`, but the score chain depends on current/local Model v4 evidence matrices, current value checkpoints, lifecycle/confidence layers, and source receipts that are not available as historical season-by-season artifacts.

This report therefore measures a review-only partial proxy of the current formula families against the V3 historical N-to-N+1 substrate. The proxy uses only lagged factual fields already marked review-safe in V3 and excludes every display-only, blocked, review-only-for-display, current-only, or leakage-unsafe field.

## Clear Answer

Based on this backtest, the current production ranking surface is strongest at `WR`, weakest at `TE`, and overall should be trusted as a useful review-only ordering aid for players with prior-season production, not as an approved standalone accuracy model or a single draft-day truth number.

The partial proxy is baseline-like rather than clearly additive: in the same V3 row set, the simple prior-year finish baseline slightly outperformed the current-formula-family proxy overall on rank MAE and Spearman. That is a real warning, not a cosmetic caveat.

## Metrics Summary

| Position | Seasons Tested | Rows | MAE | RMSE | Spearman | Top-12 Hit | Top-24 Hit | Top-36 Hit | Startable Precision | Trust | Metric Unit | Exact Replay | Benchmark Layer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| QB | 13 | 754 | 10.141 | 13.363 | 0.699 | 55.8% | N/A | N/A | 51.5% | PARTIAL_LOW_MEDIUM | finish-rank places | No | current_formula_family_partial_proxy_review_only |
| RB | 13 | 1429 | 20.831 | 27.297 | 0.636 | 41.7% | 57.7% | 66.7% | 61.0% | PARTIAL_LOW_MEDIUM | finish-rank places | No | current_formula_family_partial_proxy_review_only |
| WR | 13 | 2124 | 29.225 | 38.106 | 0.686 | 42.3% | 56.1% | 64.1% | 64.6% | PARTIAL_LOW_MEDIUM | finish-rank places | No | current_formula_family_partial_proxy_review_only |
| TE | 13 | 1211 | 16.494 | 21.588 | 0.685 | 48.1% | N/A | N/A | 48.1% | PARTIAL_LOW_MEDIUM | finish-rank places | No | current_formula_family_partial_proxy_review_only |

MAE/RMSE are finish-rank-place errors between the proxy predicted rank and the next-season position finish. Spearman is rank correlation where higher is better. Startable precision uses the NWR league contract: QB10, RB30, WR40, TE12.

## Overall Accuracy Summary

No approved single overall accuracy number is defensible yet.

Reasons: exact formula replay is blocked, the benchmark is a partial proxy, K is intentionally outside the modeled chain, rookies without prior-season NFL rows are structurally missing, and position thresholds have different fantasy meaning in a 1QB non-PPR first-down league. A proxy aggregate can be calculated, but it should not be promoted as an approved production accuracy number.

## Baseline Comparison

| Model / Baseline | Scope | Metric | Result | Caveat |
| --- | --- | --- | --- | --- |
| Production formula family partial proxy | V3 2013-2025 targets, QB/RB/WR/TE | rank MAE / Spearman / startable precision | 21.65 / 0.675 / 58.3% | Exact current formula replay blocked; proxy uses only overlapping lagged factuals. |
| Simple prior-year finish baseline | Same V3 rows | rank MAE / Spearman / startable precision | 21.39 / 0.681 / 58.4% | Derived from prior-season NWR scoring only; safe but not dynasty-aware. |
| Opportunity-only baseline | Same V3 rows | rank MAE / Spearman / startable precision | 21.93 / 0.669 / 56.9% | Uses attempts/carries/targets only; review-only local factuals. |
| Prior NWR historical Backtest V1 baseline | 2021;2022;2023;2024;2025 | points MAE / RMSE / Spearman / Top-N | 34.94 / 46.55 / 0.709 / 58.2% | Existing local review-only baseline; points metrics are not directly comparable to rank MAE. |
| Market / ADP baseline | Not run | N/A | Excluded | Only current/display-only market data was found; unsafe as historical input. |

## Source Trace

- Current ranking surface: `C:\NWR\Niners-War-Room\local_exports\model_v4\current_value\latest\full_player_board_value_review_rows.csv`
- Current board hash matches pinned app hash: `True`
- Historical substrate: `C:\NWR\Niners-War-Room-production-rankings-backtest-v1-20260708\docs\hq\experiments\historical_tuning_substrate_expansion_v3_source_semantics_audit_20260701\nwr_historical_tuning_feature_target_substrate_v3.parquet`
- V3 feature seasons: `2012-2024`; target seasons: `2013-2025`
- Ranking app/page trace: `app/pages/20_final_board_v1.py` -> `load_dynasty_rankings()` -> `build_unified_player_board()` -> `sort_rankings_frame_by_column()`.
- Score/rank trace: `full_player_board_value_review_rows.csv.nwr_dynasty_score` -> `_assign_private_ranks()` descending score sort.
- Formula-family trace: `model_v4_rb_wr_current_value_service.py`, `model_v4_qb_te_current_value_service.py`, `model_v4_replacement_vorp_core_service.py`, `model_v4_current_value_checkpoint_service.py`, and `model_v4_formula_contract_service.py`.

## Excluded Signals

- Display-only: DynastyProcess value/rank/ECR, market gap, Outcome V1/V2 probabilities, NFLVerse context display, injury context display.
- Review-only but not production-approved: V3 historical substrate rows, historical formula candidates, candidate ranks, current-board candidate feature gates.
- Blocked: market, ADP, projections, rankings, mocks, big boards, generic JSON slurping, canonical first-down views not routed through admitted matched views.
- Not joined or identity unsafe: same-name audit fields, unresolved current identity rows, any row without GSIS canonical identity.
- Leakage unsafe: 2026 current roster/status/injury/depth/schedule, current ADP, current market ranks, target-season outcomes as inputs.
- Not historically available in V3: current lifecycle/age guards, current confidence-missingness layer, current RotoWire route/YPRR/TPRR coverage, red-zone context, depth-chart role changes, medical/injury status.
- K: intentionally not meaningfully modeled; current full-board current-value chain supports QB/RB/WR/TE.

## Biggest Miss Patterns

| Pattern | Count | Evidence |
| --- | --- | --- |
| WR prior-production decline false positive | 160 | Curtis Samuel 2021 pred 28 actual 158; Will Fuller 2021 pred 35 actual 157; Allen Robinson 2017 pred 22 actual 144; Courtland Sutton 2020 pred 17 actual 139; Mike Wallace 2018 pred 37 actual 156 |
| RB prior-production decline false positive | 137 | Adrian Peterson 2016 pred 2 actual 97; David Johnson 2017 pred 1 actual 89; Saquon Barkley 2020 pred 10 actual 92; Mikel Leshoure 2013 pred 20 actual 101; Marlon Mack 2020 pred 20 actual 99 |
| TE prior-production decline false positive | 69 | Delanie Walker 2018 pred 4 actual 68; David Njoku 2019 pred 8 actual 68; Trey Burton 2019 pred 9 actual 66; Robert Tonyan 2021 pred 6 actual 46; Logan Thomas 2021 pred 4 actual 44 |
| RB low-prior-opportunity breakout miss | 68 | Raheem Mostert 2022 pred 110 actual 18; Jerome Ford 2023 pred 107 actual 20; James Conner 2018 pred 86 actual 5; Adrian Peterson 2015 pred 83 actual 2; Mike Davis 2020 pred 94 actual 13 |
| WR low-prior-opportunity breakout miss | 60 | K.J. Osborn 2021 pred 178 actual 40; Curtis Samuel 2022 pred 151 actual 26; Keenan Allen 2017 pred 122 actual 3; Tyrell Williams 2016 pred 128 actual 13; Allen Robinson 2018 pred 150 actual 36 |
| QB prior-production decline false positive | 58 | Jameis Winston 2020 pred 4 actual 53; Ben Roethlisberger 2019 pred 4 actual 41; Cam Newton 2019 pred 5 actual 39; Daniel Jones 2023 pred 6 actual 34; Jayden Daniels 2025 pred 2 actual 29 |
| TE low-prior-opportunity breakout miss | 8 | Larry Donnell 2014 pred 76 actual 12; Darren Waller 2019 pred 66 actual 3; Robert Tonyan 2020 pred 66 actual 4; Tyler Eifert 2015 pred 68 actual 7; Gary Barnidge 2015 pred 52 actual 2 |

Position miss summary:

| Position | False Negative Startable Misses | False Positive Startable Misses | Worst Under-Rank | Worst Over-Rank |
| --- | --- | --- | --- | --- |
| QB | 63 | 63 | Jordan Love 2023 pred 54 actual 5; Patrick Mahomes 2018 pred 42 actual 1; Sam Darnold 2024 pred 42 actual 7; Geno Smith 2022 pred 41 actual 7; Dak Prescott 2025 pred 35 actual 6 | Jameis Winston 2020 pred 4 actual 53; Ben Roethlisberger 2019 pred 4 actual 41; Cam Newton 2019 pred 5 actual 39; DeShone Kizer 2018 pred 10 actual 41; Daniel Jones 2023 pred 6 actual 34 |
| RB | 152 | 152 | Raheem Mostert 2022 pred 110 actual 18; Jerome Ford 2023 pred 107 actual 20; Adrian Peterson 2015 pred 83 actual 2; Mike Davis 2020 pred 94 actual 13; James Conner 2018 pred 86 actual 5 | Adrian Peterson 2016 pred 2 actual 97; David Johnson 2017 pred 1 actual 89; Saquon Barkley 2020 pred 10 actual 92; Mikel Leshoure 2013 pred 20 actual 101; Marlon Mack 2020 pred 20 actual 99 |
| WR | 184 | 184 | K.J. Osborn 2021 pred 178 actual 40; Curtis Samuel 2022 pred 151 actual 26; Keenan Allen 2017 pred 122 actual 3; Tyrell Williams 2016 pred 128 actual 13; Allen Robinson 2018 pred 150 actual 36 | Curtis Samuel 2021 pred 28 actual 158; Courtland Sutton 2020 pred 17 actual 139; Will Fuller 2021 pred 35 actual 157; Allen Robinson 2017 pred 22 actual 144; Mike Wallace 2018 pred 37 actual 156 |
| TE | 81 | 81 | Taysom Hill 2019 pred 88 actual 12; Larry Donnell 2014 pred 76 actual 12; Darren Waller 2019 pred 66 actual 3; Robert Tonyan 2020 pred 66 actual 4; Tyler Eifert 2015 pred 68 actual 7 | Delanie Walker 2018 pred 4 actual 68; David Njoku 2019 pred 8 actual 68; Trey Burton 2019 pred 9 actual 66; Robert Tonyan 2021 pred 6 actual 46; Logan Thomas 2021 pred 4 actual 44 |

Interpretation: the proxy is most exposed to one-year role changes, breakouts from low prior opportunity, and prior-production decline false positives. Injury slices remain review-only caveats because the safe historical feature substrate does not admit injury as an input.

## Draft-Day Interpretation

- Good for: ordering veterans with meaningful prior-season QB/RB/WR/TE production and comparing broad position tiers.
- Bad for: rookies, UDFA/low-draft-capital players, injured players, sudden RB role changes, WR breakouts, TE volatility, and any player whose case depends on current depth charts or market context.
- Trust most: positions with stronger Spearman/startable precision in the scorecard, especially when source coverage and component weight are high.
- Human override needed: rookies, ambiguous role changes, older assets, injury-affected players, TE outliers, and 1QB QB value debates.
- Player archetypes needing extra review: low-prior-opportunity breakouts, prior top scorers with role/health decline risk, and players with optional source null fences or missing current formula components.

## Historical Label, Identity, And Source Coverage

| Position | seasons | rows | optional_null_fenced_rows | median_component_weight | actual_startable_rows |
| --- | --- | --- | --- | --- | --- |
| QB | 13 | 754 | 140 | 0.950 | 130 |
| RB | 13 | 1429 | 719 | 1.000 | 390 |
| TE | 13 | 1211 | 188 | 0.950 | 156 |
| WR | 13 | 2124 | 324 | 1.000 | 520 |

Identity join coverage in V3 is 5,518/5,518 matched feature-label rows with 0 position mismatches and 0 duplicate player-season-pair keys. Source coverage is review-only: V3 marks model_use_allowed=false, training_allowed=false, source_truth_allowed=false, and production_approved=false.

## Next Work Orders

1. Build a historical Model v4 replay substrate with current formula component names, not just proxy overlap columns.
2. Add a rookie/first-NFL-season backtest lane with draft capital, college production, and identity-safe rookie labels.
3. Create a role-change miss packet for RB and WR using only lagged usage and admitted depth/availability snapshots if approved.
4. Build a 1QB positional calibration lane to separate football points from keeper-format replacement value.
5. Decide whether V3 source-semantics can graduate from review-only evidence into a strictly bounded candidate-search gate.
