# Historical Model v4 Replay Substrate V1 Report

## Verdict

`YELLOW_MODEL_V4_HISTORICAL_REPLAY_SUBSTRATE_PARTIAL_WITH_BLOCKERS`

## Clear Answer

Exact historical replay of the current production formula is not possible because the current displayed Full Dynasty board is a review-only WR/QB v2 candidate artifact, the upstream current checkpoint/component receipt files are absent locally, and no season-by-season historical Model v4 component receipt layer exists with decision-date source proofs.

A partial replay substrate is possible for QB/RB/WR/TE target seasons 2013-2025 using V3 lagged factual overlap, but it is not an exact Model v4 score replay and cannot claim production accuracy.

## Current Surface Facts

- Board rows inspected: `240`.
- Board allowed_use values: `['candidate_review_only_not_active_rankings']`.
- Board candidate_mode values: `['wr_qb_v2_candidate']`.
- The displayed board sorts by `nwr_dynasty_score`, then `nwr_rank` is assigned from that score.
- The current artifact points to `checkpoint_review_score` upstream, but the named upstream file is not present in the local canonical runtime folder.

## Formula Component Map Summary

| Component | Production Input? | Source | Gate Status | Historical Availability | Decision-Date Safe? | Replay Status | Caveat |
| --------- | ----------------- | ------ | ----------- | ----------------------- | ------------------- | ------------- | ------ |
| nwr_dynasty_score | Yes_current_displayed_score | current full board CSV; upstream checkpoint file named by rows is abs... | candidate_review_only_not_active_rankings in current artifact | not available historically as exact score; current-only final score p... | No for historical replay | EXACT_REPLAY_BLOCKED | The UI sorts by this field, but the current artifact is a review-only candidate surface. |
| nwr_rank | Yes_current_displayed_sort | derived from nwr_dynasty_score sort | derived display rank | only derivable after exact score exists historically | No until score replay is safe | EXACT_REPLAY_BLOCKED | Rank is a consequence of score, not an independent model input. |
| checkpoint_review_score | Yes_base_score_input | current_player_value_full_board_review_rows.csv plus component rows | review_only current value checkpoint | not present as historical season-by-season checkpoint rows | No | EXACT_REPLAY_BLOCKED | The current board points to this upstream source, but the source file is not present in this ... |
| position_specific_review_score | Yes_base_component | rb_wr_current_value_rows.csv; qb_te_current_value_rows.csv | review_only current value component output | not present historically; partial factual overlap only | No | EXACT_REPLAY_BLOCKED | This is the base score before lifecycle and confidence cap. |
| positive_vorp_points | Yes_base_component | NFL evidence matrix; admitted first-down views; admitted return view | formula contract admits current matched views only | not in V3 substrate | No | EXACT_REPLAY_BLOCKED | Requires position replacement baselines and exact review scoring rows. |
| review_scoring_points | Yes_base_component | NFL evidence matrix; admitted first-down views; admitted return view | formula contract admits current matched views only | partial V3 overlap | Yes for V3 lagged proxy only | PARTIAL_REPLAY_AVAILABLE | Can be partially proxied from V3 prior_nwr_points, but not exact current receipt. |
| imported_first_down_points | Yes_base_component | NFL evidence matrix; admitted first-down views; admitted return view | formula contract admits current matched views only | partial V3 overlap | Yes for V3 lagged proxy only | PARTIAL_REPLAY_AVAILABLE | Can be partially computed from V3 rushing/receiving first downs, but exact current source sta... |
| RB role_volume | Yes_base_component | target_carry_volume / target_share_team_share / rushing_att / receivi... | review_only formula component; explicit field-path guarded | partial V3 lagged factual overlap | Yes for proxy overlap only | PARTIAL_REPLAY_AVAILABLE | V3 overlap preserves component name but not exact current normalized score/weight receipt. |
| WR target_route_role | Yes_base_component | target_carry_volume / target_share_team_share / routes_run_tprr / rou... | review_only formula component; explicit field-path guarded | partial V3 lagged factual overlap | Yes for proxy overlap only | PARTIAL_REPLAY_AVAILABLE | V3 overlap preserves component name but not exact current normalized score/weight receipt. |
| QB passing_volume_security | Yes_base_component | passing_attempts / passing_completions / passing_yards | review_only formula component; explicit field-path guarded | partial V3 lagged factual overlap | Yes for proxy overlap only | PARTIAL_REPLAY_AVAILABLE | Partial overlap is not score-equivalent to Model v4. |
| TE route_target_role | Yes_base_component | route_data_route / route_data_targets / team_tar / routes_run_tprr | review_only formula component; explicit field-path guarded | partial V3 lagged factual overlap | Yes for proxy overlap only | PARTIAL_REPLAY_AVAILABLE | Partial overlap is not score-equivalent to Model v4. |
| lifecycle_modifier_review | Yes_base_component | lifecycle_archetype_rows.csv; age/source sidecars; stats_first evidence | review_only lifecycle component | not available in V3; age/role shape not safely reconstructed for all ... | No | EXACT_REPLAY_BLOCKED | Current role/age shape is one of the biggest replay blockers. |
| confidence_cap | Yes_base_component | source_coverage_matrix.csv and component warning flags | review_only confidence cap | not available historically with current source-coverage receipts | No | EXACT_REPLAY_BLOCKED | Missingness/caveat logic is part of score and cannot be guessed. |
| wr_qb_v2_candidate_adjustment | Yes_current_displayed_candidate_layer | current board, current component rows, age sidecar, historical shadow... | candidate_review_only_not_active_rankings | not historically available with decision-date receipts | No | EXACT_REPLAY_BLOCKED | Current displayed board applies a WR/QB candidate overlay, but it is stamped not active ranki... |
| old_pocket_qb_horizon_cap | Yes_current_displayed_candidate_layer | current board, current component rows, age sidecar, historical shadow... | candidate_review_only_not_active_rankings | not historically available with decision-date receipts | No | EXACT_REPLAY_BLOCKED | Requires historical age, role_archetype, and current component receipts. |
| market_rank | No | market/ADP context | blocked/display-only/review-only | not eligible for exact replay | No | EXCLUDED_FROM_REPLAY | display-only; blocked as private value input |
| NGS advanced metrics | No | NGS display packet | blocked/display-only/review-only | not eligible for exact replay | No | EXCLUDED_FROM_REPLAY | review-only display; not model input |
| PFR advanced metrics | No | advanced metrics bridge | blocked/display-only/review-only | not eligible for exact replay | No | EXCLUDED_FROM_REPLAY | identity unsafe in current gate |
| CFBD college metrics | No | CFBD review artifacts | blocked/display-only/review-only | not eligible for exact replay | No | EXCLUDED_FROM_REPLAY | review-only identity review required |

## Historical Availability Summary

| Season Range | Position | Replay Rows Possible | Label Coverage | Input Coverage | Identity Coverage | Main Blocker |
| ------------ | -------- | -------------------: | -------------: | -------------: | ----------------: | ------------ |
| 2013-2025 | QB | 0 exact / 754 partial | 100.0% | 0.0% exact / 36.4% partial | 100.0% | missing current QB component receipts, age/role lifecycle receipts, and candidate old-pocket overlay history |
| 2013-2025 | RB | 0 exact / 1429 partial | 100.0% | 0.0% exact / 62.5% partial | 100.0% | missing current RB component receipts for role/red-zone/efficiency plus lifecycle/confidence history |
| 2013-2025 | WR | 0 exact / 2124 partial | 100.0% | 0.0% exact / 55.6% partial | 100.0% | missing current WR route/YPRR/air-yard/stats-first receipts plus candidate overlay history |
| 2013-2025 | TE | 0 exact / 1211 partial | 100.0% | 0.0% exact / 44.4% partial | 100.0% | missing TE route/YPRR/red-zone receipts and TE discipline/lifecycle/confidence history |

## Replay Contract

The next lane must run, if and only if exact component receipts are available, a target-season `Y` replay using only completed `Y-1` factual inputs and static events known before the `Y` decision anchor. The player universe is QB/RB/WR/TE with approved identity joins. Required labels are next-season NWR points, position finish, top-N hits, and startable labels under the 10-team 1QB non-PPR first-down league contract. Required inputs are the Model v4 component names and source receipts listed in `MODEL_V4_REPLAY_CONTRACT.md`.

## Blocked / Excluded Signals

- Display-only: market rank, league rank, DynastyProcess values/ECR, Outcome V2 probabilities, NGS display fields.
- Review-only: V3 substrate, advanced-metrics shadow panels, CFBD review artifacts, current WR/QB v2 candidate overlay.
- Blocked: ADP, projections, rankings, mocks, big boards, consensus, source row order, generic JSON slurping.
- Not historically available: current component receipt rows, lifecycle/role archetype rows, confidence cap rows, route/YPRR/TPRR receipts.
- Not decision-date safe: current roster/status/injury/depth/schedule context and current market context.
- Identity unsafe: PFR advanced bridge and ESPN QBR under current advanced metrics gate; CFBD before identity review approval.

## Biggest Replay Blockers

1. Current board is review-only candidate, not a clean approved production formula target.
2. Upstream current component/checkpoint receipt files are absent from the local canonical runtime folder.
3. Historical Model v4 component receipts with current names do not exist.
4. Route/YPRR/TPRR/red-zone/stats-first evidence is not historically admitted with as-of receipts.
5. Lifecycle, age, role archetype, warning, and confidence layers are current-state dependent.
6. Rookie and UDFA first-season rows are structurally outside the V3 prior-season veteran substrate.

## Recommendation

The next lane should be `Formula documentation/cleanup lane first`, followed by a bounded component-receipt backfill/source-admission lane. An actual Model v4 Historical Replay Benchmark should wait until the current board surface is clearly separated into approved production versus review-only candidate layers and historical component receipts exist.

## Generated Artifacts

- `MODEL_V4_FORMULA_COMPONENT_SOURCE_MAP.csv`
- `MODEL_V4_HISTORICAL_REPLAY_AVAILABILITY_MATRIX.csv`
- `MODEL_V4_REPLAY_CONTRACT.md`
- `MODEL_V4_REPLAY_BLOCKERS.md`
- `MODEL_V4_REPLAY_SOURCE_TRACE.md`
- `MODEL_V4_PARTIAL_REPLAY_INPUT_PANEL_REVIEW_ONLY.csv`
- `build_historical_model_v4_replay_substrate_v1.py`

## Non-Goals Honored

No formula weights were tuned, no rankings were changed, no source was promoted, no app behavior was changed, and no current/future-only fields were used as historical inputs.
