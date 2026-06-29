# Outcome V2 Label Factory Feasibility

Date: 2026-06-29

## 1. Executive Verdict

`PARTIALLY_FEASIBLE_BUILD_LABELS`

Outcome V2 historical horizon labels do not require pre-existing horizon labels. They can be built from factual historical player-season outcomes already present locally in the ignored shared NFL usage cache and documented by committed review artifacts.

The feasible path is a review-only historical label factory that computes actual NWR/LVE season scoring, position finishes, same-season threshold hits, next-season threshold hits, and censored within-five-year threshold hits. This is not an app artifact, not current-player prediction, not model training, and not Rankings wiring.

The build is partial rather than fully green because the approved/review-only local target set currently covers target seasons 2019-2024. That is enough for this-year labels, next-year labels for anchor seasons 2018-2023, and complete five-year windows only for older anchor rows. Recent rows must be censored. Broader five-year training coverage would require older or newly approved factual player_stats seasons.

## 2. Data Found

### Local Shared Cache

These files exist locally and are intentionally outside Git under `C:\NWR_SHARED_DATA\nfl_usage_cache\`.

| Path | Rows | Seasons | Key Columns | Status |
| --- | ---: | --- | --- | --- |
| `C:\NWR_SHARED_DATA\nfl_usage_cache\target_backtest\historical_expansion\panels\player_season_core_usage_panel.csv` | 3,701 | 2018-2023 | `season`, `player_id`, `player_name`, `position`, `team`, `targets`, `carries`, `receptions`, `rushing_yards`, `receiving_yards`, `rushing_first_downs`, `receiving_first_downs`, `games_with_usage_row` | review-only, outside Git |
| `C:\NWR_SHARED_DATA\nfl_usage_cache\target_backtest\historical_expansion\panels\player_week_core_usage_panel.csv` | 35,311 | 2018-2023 | `season`, `week`, `player_id`, `player_name`, `position`, `team`, usage/stat fields, rush/receive first downs | review-only, outside Git |
| `C:\NWR_SHARED_DATA\nfl_usage_cache\target_backtest\historical_expansion\nfl_usage_expanded_target_labels_v0.csv` | 3,578 | target seasons 2019-2024 | `target_season`, `player_id`, `player_name`, `position`, `recent_team`, `next_season_nwr_points`, `next_season_games`, `next_season_position_rank`, top-threshold flags | review-only, outside Git |
| `C:\NWR_SHARED_DATA\nfl_usage_cache\target_backtest\historical_expansion\nfl_usage_expanded_target_backtest_joined_panel_v0.csv` | 2,848 | feature seasons 2018-2023, target seasons 2019-2024 | feature-season fields plus target-season NWR points/ranks/threshold hits | review-only, outside Git |
| `C:\NWR_SHARED_DATA\nfl_usage_cache\target_backtest\nfl_usage_target_labels_v0.csv` | 1,164 | target seasons 2023-2024 | same next-season target label schema | review-only, outside Git |
| `C:\NWR_SHARED_DATA\nfl_usage_cache\historical_panel\panels\player_season_core_usage_panel.csv` | 1,840 | 2022-2024 | same core player-season usage/stat fields | review-only, outside Git |

### Committed Evidence and Manifests

| Path | Finding |
| --- | --- |
| `docs/hq/data_sources/nfl_usage/historical_panel/historical_usage_expanded_panel_manifest_v0.csv` | Documents 2018-2023 expanded player-week/player-season panels and ignored shared-cache paths. |
| `docs/hq/data_sources/nfl_usage/historical_panel/historical_usage_expanded_field_coverage_matrix_v0.csv` | Shows 2018-2023 coverage for `targets`, `carries`, `receptions`, yards, `rushing_first_downs`, and `receiving_first_downs`; player_id coverage is 100% for expanded player_stats fields. |
| `docs/hq/data_sources/nfl_usage/historical_panel/historical_usage_expanded_source_summary_v0.csv` | Documents `player_stats` source row count 108,821 with 99.88% player_id coverage. |
| `docs/hq/data_sources/nfl_usage/target_backtest/nfl_usage_target_label_manifest_v0.csv` | Documents review-only target labels derived from factual nflreadpy/player_stats, with `model_input_allowed=no` and `app_wiring_allowed=no`. |
| `docs/hq/data_sources/nfl_usage/target_backtest/nfl_usage_expanded_target_label_coverage_summary_v0.csv` | Documents expanded target label coverage of 2,848 joined player rows with 100% player_id coverage and QB/RB/WR/TE position coverage. |
| `docs/hq/data_sources/nfl_usage/promotion_gate/nfl_usage_backtest_target_label_audit_v0.csv` | Confirms target labels are allowed for backtest only with conditions and must not be promoted without gates. |
| `src/services/nfl_usage_target_label_service.py` | Existing service recomputes NWR/LVE points from factual player_stats fields and derives position ranks and threshold labels. |
| `tests/test_nfl_usage_target_label_service.py` | Focused tests prove scoring formula expectations, including first-down scoring. |
| `docs/model_v4/LEAGUE_RULES_LOCK.md` | Canonical scoring rule source: 1QB, non-PPR, rush/receive first down 0.4, reception 0. |

### Candidate Display Context Found But Not Used As Label Truth

`C:\NWR_SHARED_DATA\lane_exchange\stats_context\player_season_stats_display_context\20260621_pre_backtest_scoring_aligned_v1\player_season_stats_display_context.csv` exists with 4,017 rows for seasons 2024-2025 and rich stat fields. Its manifest marks it `approval_status=candidate`, `allowed_use=display_stat_context_only`, and forbids `model_training`, simulation, hidden rank/sort, and latest approval. It should not be used as target truth until a source-policy gate explicitly approves it for historical label derivation.

## 3. Data Missing

- Generic imported fantasy point fields are not needed and should remain blocked as model/target inputs. The feasible route recomputes NWR/LVE points from factual stat components.
- `passing_first_downs` exists in newer/player_stats schemas but is not needed for league scoring because first-down scoring applies only to rushing and receiving first downs.
- Exact medical injury cause is not available in the verified historical label path. Injury-shortened seasons can be flagged from games/usage availability, but no medical projection or injury-risk label should be created.
- Complete five-year horizon windows are limited by the currently approved/review-only target-season range. With target seasons 2019-2024, recent anchor seasons must be censored.
- Rookies/prospects do not have reliable NFL-experienced history in this label path. They should be excluded or marked out of scope unless a separate rookie outcome lane is approved.

## 4. Source-Policy Status

| Source | Status | Notes |
| --- | --- | --- |
| nflverse/nflreadpy player_stats | approved factual target source for review-only labels | Allowed by `docs/hq/data_sources/nfl_usage/NWR_NFL_USAGE_SOURCE_CONTRACT_V0_20260624.md` and target-label plan. |
| Shared NFL usage cache | review-only, untracked | Raw/cache files must stay under `C:\NWR_SHARED_DATA\nfl_usage_cache\` and must not be committed. |
| Existing target labels | approved review-only target labels | `model_input_allowed=no`, `app_wiring_allowed=no`; useful for label-factory proof, not app promotion. |
| Lane Exchange stats context candidate | display-only candidate | Not approved as target truth for label factory yet. |
| ADP, market, DynastyProcess, projections, analyst ranks, trade values | blocked | Must not be used as target truth or inputs. |
| CFBD | blocked for this lane | Do not use college/rookie data for Outcome V2 veteran horizon labels. |
| RotoWire/vendor/Gmail | blocked | Do not use vendor scrape, Gmail, or private/vendor rows. |
| true routes/TPRR/YPRR | blocked/licensed gap | Public participation proxies are not exact route truth. |

## 5. Label Factory Feasibility

### This-Year Labels

Feasible.

For each factual `target_season`, compute or reuse:

- `fantasy_points` as recomputed NWR/LVE points.
- `position_finish` by ranking within `target_season` and `position`.
- `top_6_hit`, `top_12_hit`, `top_24_hit`, `top_36_hit` according to the position threshold map.

The existing expanded target label file already demonstrates this for target seasons 2019-2024 through `next_season_nwr_points`, `next_season_position_rank`, and position-specific top-threshold flags. A new Outcome V2 factory should rename the semantics away from `next_season_*` when using the same factual row as the target season.

### Next-Year Labels

Feasible for anchor seasons with observed N+1 target season.

The existing joined panel already proves season N to target season N+1 joins for feature seasons 2018-2023 and target seasons 2019-2024. A factory can derive:

- `next_year_top_6_hit`
- `next_year_top_12_hit`
- `next_year_top_24_hit`
- `next_year_top_36_hit`

Rows without N+1 target data must be censored, not treated as misses.

### Within-Five-Year Labels

Partially feasible with censoring.

The operation is straightforward: for each anchor `player_id` and position-scoped threshold, check whether any observed target season in the next five complete NFL seasons hit the threshold. However, with currently verified target seasons 2019-2024, only older anchor seasons have full five-year windows. Recent seasons must receive:

- `label_window_complete=false`
- `censoring_status=right_censored`
- no negative label fabricated from incomplete future years

If the next-five-years definition means seasons N+1 through N+5, complete windows are available only for anchors with N+5 <= 2024. If the definition includes the current season plus the next four, complete windows are available for anchors with N+4 <= 2024. The exact inclusive/exclusive rule should be locked before build.

### Scoring Approximation

Exact scoring is feasible for the verified player_stats target-label path because the scoring service uses factual fields:

- passing yards
- passing TDs
- passing interceptions
- rushing yards
- rushing TDs
- receiving yards
- receiving TDs
- rushing first downs
- receiving first downs
- punt/kickoff return yards
- special teams TDs
- two-point conversions
- fumbles lost

The scoring formula is implemented in `src/services/nfl_usage_target_label_service.py` and aligns to `docs/model_v4/LEAGUE_RULES_LOCK.md`.

If a future older-season extension lacks first-down fields, the output can still be built as `scoring_mode=approximation`, but it must be visibly labeled and separated from exact rows. Missing material scoring components must not silently become zero unless the source schema omission policy is documented and approved.

### Availability Context

Supported with caveats.

Available fields include `next_season_games`, `games_with_usage_row`, player-week row counts, and season stat rows. Those support:

- `games_played`
- `availability_context`
- limited-sample flags
- right-censoring flags

They do not support medical projection. Injury-shortened seasons can be flagged as low-games/limited availability, not diagnosed as injury-risk outcomes.

### Identity and Position

Supported.

The expanded target labels and joined panel use stable `player_id` and provide `player_name`, `position`, and team context. The expanded target coverage summary reports 100% player_id coverage and QB/RB/WR/TE position coverage for the joined target labels.

### Rookie / Prospect Handling

Supported by exclusion, not by prediction.

The label factory should restrict to NFL-experienced QB/RB/WR/TE rows with factual NFL player-season data. Current rookies/prospects without NFL seasons should be excluded or marked `out_of_scope_rookie_or_prospect`. Do not fill rookie labels from CFBD, ADP, draft capital, market data, or manual scouting notes.

## 6. Proposed Next Build Step

Do not build until explicitly approved.

If approved, create a small review-only historical label factory:

- `src/services/outcome_v2_historical_label_factory.py`
- `scripts/build_outcome_v2_historical_labels.py`
- `tests/test_outcome_v2_historical_label_factory.py`
- output artifact under `C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels\outcome_v2_historical_horizon_labels.csv`
- manifest under the same ignored shared-data folder

The output should include:

- `player_id`
- `player_name`
- `position`
- `season`
- `scoring_mode`
- `fantasy_points`
- `position_finish`
- `games_played`
- `availability_context`
- `top_6_hit`
- `top_12_hit`
- `top_24_hit`
- `top_36_hit`
- `next_year_top_6_hit`
- `next_year_top_12_hit`
- `next_year_top_24_hit`
- `next_year_top_36_hit`
- `within_5y_top_6_hit`
- `within_5y_top_12_hit`
- `within_5y_top_24_hit`
- `within_5y_top_36_hit`
- `label_window_complete`
- `censoring_status`
- `data_quality_status`

Required tests:

- scoring formula parity with `nfl_usage_target_label_service`
- threshold map by position: QB T6/T12, RB T6/T12/T24/T36, WR T6/T12/T24/T36, TE T6/T12
- same-year position finish derivation
- next-year join by `player_id`
- within-five-year hit aggregation
- censoring for recent incomplete windows
- rookie/prospect exclusion
- blocked-source scan
- raw/shared cache not committed

Stop conditions:

- no factual player-season target rows found
- missing `player_id`, `position`, or season keys
- first-down/stat fields insufficient and no approved approximation mode
- attempt to use ADP, market, DynastyProcess, projections, CFBD, vendor, Gmail, or Outcome display gaps as target truth
- attempt to wire app/Rankings/model output
- attempt to commit shared-cache/raw artifacts

## 7. Do-Not-Use List

Do not use these for Outcome V2 historical horizon labels:

- market/ADP/DynastyProcess
- CFBD
- unapproved NFL usage fields
- vendor/Gmail
- RotoWire live scraping or vendor scrape rows
- FantasyPros projections/ranks
- true routes, true TPRR, true YPRR unless an approved exact route source is later added
- injury projections
- analyst blurbs
- trade values
- app-facing Outcome V1 display gaps as negative target labels
- lane-exchange `latest_candidate` display snapshots unless explicitly approved as target truth by source policy
