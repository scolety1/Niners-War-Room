# NFLVerse Stats Upgrade Implementation Requirements

Source reports:

- `2026-05-07_public_structured_data_stack.md`
- `2026-05-07_final_stats_first_veteran_model.md`

This file extracts implementation requirements only. It does not approve formula changes or make the current model decision-ready.

## Requirements Summary

The reports require a stats-first veteran model built from local nflverse/ffverse source snapshots. Market data must be removed from private/stat value and kept only for trade liquidity and market edge. LVE scoring must be rebuilt locally from raw and expected component fields because public fantasy-point totals do not match no-PPR plus 0.4 rushing/receiving first-down scoring.

## Data Source Requirements

| id | requirement | source basis | priority |
|---|---|---|---|
| NFS-001 | Add an nflverse raw-source import layer for weekly player stats. | `load_player_stats(summary_level="week")`, 1999+, core production and first-down fields. | required |
| NFS-002 | Add an nflverse play-by-play import layer for exact local derivation and validation. | `load_pbp()`, 1999+, play-level first downs, TDs, player attribution, EPA. | required |
| NFS-003 | Add player master import. | `load_players()`, canonical bio/draft/ID enrichment. | required |
| NFS-004 | Add weekly roster import. | `load_rosters_weekly()`, active status, team, position, Sleeper IDs. | required |
| NFS-005 | Add fantasy ID crosswalk import. | `load_ff_playerids()`, Sleeper/GSIS/PFR/ESPN/PFF bridge. | required |
| NFS-006 | Add snap-count import. | `load_snap_counts()`, 2012+, offense snaps and offense percent. | required |
| NFS-007 | Add expected opportunity import. | `load_ff_opportunity(stat_type="weekly")`, 2006+, expected yards/TDs/first downs. | required |
| NFS-008 | Add season-roster import as supplemental identity/status data. | `load_rosters()`, current team/status enrichment. | recommended |
| NFS-009 | Add participation import only as caveated enrichment. | 2016+, not a true routes-run table, 2023+ not in-season. | optional/review |
| NFS-010 | Add depth-chart import only as caveated role enrichment. | 2001+, post-2024 schema changed and is timestamped rather than weekly. | optional/review |
| NFS-011 | Add injury import for historical data only. | 2009-2024; no official nflverse 2025+ injury feed per report. | optional/review |
| NFS-012 | Add Next Gen Stats import only as optional enrichment. | 2016+, threshold-filtered, not core model backbone. | optional |

## Raw CSV Contract Requirements

The raw import layer must persist local CSVs before any normalized features are created.

| id | csv | required columns |
|---|---|---|
| NFS-013 | `dim_player_ids.csv` | `gsis_id`, `sleeper_id`, `pfr_id`, `espn_id`, `pff_id`, `smart_id`, `merge_name`, `display_name`, `birth_date`, `position`, `position_group`, `latest_team`, `mapping_source`, `mapping_rule`, `mapping_confidence`, `is_current`, `source_dataset`, `source_release`, `ingested_at_utc` |
| NFS-014 | `dim_players.csv` | `gsis_id`, `display_name`, `first_name`, `last_name`, `short_name`, `football_name`, `birth_date`, `college_name`, `jersey_number`, `position`, `position_group`, `ngs_position`, `rookie_season`, `last_season`, `years_of_experience`, `draft_year`, `draft_round`, `draft_pick`, `height`, `weight`, `headshot`, `source_dataset`, `source_release`, `ingested_at_utc` |
| NFS-015 | `fact_player_week_stats.csv` | `player_id`, `season`, `week`, `season_type`, `team`, `opponent_team`, `position`, `position_group`, passing/rushing/receiving yards, TDs, attempts/opportunities, first downs, air yards, target share, air-yard share, `wopr`, `source_dataset`, `source_release`, `ingested_at_utc` |
| NFS-016 | `fact_player_week_usage.csv` | `gsis_id`, `season`, `week`, `game_id`, `team`, `position`, `pfr_player_id`, `offense_snaps`, `offense_pct`, `st_snaps`, participation/depth-chart proxy fields, `source_dataset`, `source_release`, `ingested_at_utc` |
| NFS-017 | `fact_player_week_health.csv` | `gsis_id`, `season`, `week`, `team`, `position`, roster status, active/IR flags, injury report/practice fields, `source_dataset`, `source_release`, `ingested_at_utc` |
| NFS-018 | `fact_player_week_xfp.csv` | `player_id`, `season`, `week`, `posteam`, `position`, expected pass/rec/rush attempts, expected yards, expected TDs, expected first downs, `total_fantasy_points_exp`, `source_dataset`, `model_version`, `source_release`, `ingested_at_utc` |

Every raw CSV must preserve source IDs and provenance. Derived LVE scoring must live in separate derived tables, not in raw source tables.

## Identity Requirements

| id | requirement |
|---|---|
| NFS-019 | Use `gsis_id` as the canonical internal player key for nflverse-derived veteran stats. |
| NFS-020 | Use `sleeper_id` only as a crosswalk column, not the warehouse primary key. |
| NFS-021 | Primary mapping path: `ff_playerids.sleeper_id -> gsis_id`. |
| NFS-022 | Verification path: weekly/season rosters confirm `sleeper_id`, `gsis_id`, team, position, and status. |
| NFS-023 | Enrichment path: player master fills names, bio fields, draft fields, and alternate IDs. |
| NFS-024 | Snap-count bridge must map `pfr_id -> pfr_player_id` because snap counts are PFR-keyed. |
| NFS-025 | Fallback matching order must be exact alternate IDs first, then normalized `merge_name + birth_date + position`, then `name + team + jersey` only as last resort. |
| NFS-026 | Store `mapping_source`, `mapping_rule`, and `mapping_confidence` on every identity row. |
| NFS-027 | Low-confidence or ambiguous identity matches must block high-value ranking trust until manually reviewed. |

## LVE Scoring Requirements

| id | requirement |
|---|---|
| NFS-028 | League scoring constants must be configurable: passing yards, passing TD, interception, rushing yards, rushing TD, receiving yards, receiving TD, fumble lost, and first-down bonus. |
| NFS-029 | `actual_lve_points` must be locally computed from component stats. |
| NFS-030 | `expected_lve_points` must be locally computed from expected component stats. |
| NFS-031 | Do not use shipped `fantasy_points`, `fantasy_points_ppr`, `rec_fantasy_points`, or `total_fantasy_points_exp` as league-exact model targets. |
| NFS-032 | Passing first downs may be imported for QB context but must not receive LVE first-down scoring unless league rules change. |
| NFS-033 | Rushing and receiving first downs must be directly imported from weekly stats where available and validated/derivable from play-by-play. |
| NFS-034 | If expected turnovers cannot be modeled defensibly, leave expected turnovers out of `expected_lve_points` and keep turnovers in historical/efficiency layers only. |

## Derived Feature Requirements

| id | requirement |
|---|---|
| NFS-035 | Build season and active-game rate features with a three-season recency blend: `0.55*Y0 + 0.30*Y-1 + 0.15*Y-2`, redistributing missing seasons proportionally. |
| NFS-036 | Use active-game rates instead of season totals. Active-game thresholds: QB `pass_attempts + rush_attempts >= 8`, RB `snap_share >= 15%`, WR/TE `snap_share >= 25%`. |
| NFS-037 | Apply empirical-Bayes shrinkage to noisy rates before normalization. |
| NFS-038 | Use fixed training distributions from 2018-2025 qualified player-seasons for percentile normalization. |
| NFS-039 | Winsorize raw features at 2.5th/97.5th percentile within position and feature before percentile ranking. |
| NFS-040 | Invert lower-is-better features after normalization. |
| NFS-041 | Create bucket scores: `H`, `X`, `R`, `E`, `F`, `EFF`, `P`, `A`, `D`, `M`, `VOR`, and confidence. |
| NFS-042 | Create `lve_player_inputs.csv` as the single wide player-snapshot feature input table. |
| NFS-043 | Create `lve_bucket_scores.csv` as the inspectable bucket-score table. |
| NFS-044 | Create `lve_model_outputs.csv` as the output table. |

## Position Formula Requirements

These are extracted formula requirements, not approved coefficients.

| id | position | requirement |
|---|---|---|
| NFS-045 | QB | Build QB buckets from historical LVE scoring, expected LVE scoring, starter security, dropback/rushing opportunity, first-down/TD fit, efficiency, projection, age, and durability. |
| NFS-046 | QB | Apply 1QB suppression to ordinary QBs. Only elite QBs can recover suppression. |
| NFS-047 | QB | Elite exception requires meaningful projected LVE PPG edge over QB14 plus rushing or efficiency edge. |
| NFS-048 | RB | Split RB into private value, win-now value, and dynasty-hold value so one-year role cannot dominate all outputs. |
| NFS-049 | RB | Model RB fragility from age window, workload, lower-body injury events, durability, and role stability. |
| NFS-050 | RB | Reward expected opportunity share and first-down/TD fit, but cap dynasty hold when age/injury/workload risk is weak. |
| NFS-051 | WR | Center WR scoring on target earning, air-yard share, first-down creation, role stability, age, expected LVE scoring, and historical production. |
| NFS-052 | WR | Apply LVE lineup-demand boost for 3WR plus 2 flex, while still avoiding raw catch/PPR logic. |
| NFS-053 | TE | Suppress non-elite TEs in no-premium scoring. |
| NFS-054 | TE | Require route/target involvement for elite TE exception. |
| NFS-055 | All | Compute outputs: `private_lve_value`, `win_now_value`, `dynasty_hold_value`, `keeper_score`, `drop_candidate_score`, `trade_value`, `market_edge_score`, and `confidence_score`. |

## Market And League-Rank Requirements

| id | requirement |
|---|---|
| NFS-056 | Market data must contribute 0% to private/stat value. |
| NFS-057 | Market data may contribute only to trade value, trade liquidity, and market edge. |
| NFS-058 | If true trade-volume data is unavailable, use deterministic position liquidity priors only in market/liquidity outputs. |
| NFS-059 | League rank must remain a rule/availability/forced-release signal, not a football quality input. |
| NFS-060 | Forced-release flag may affect keeper/drop/trade action context, but must not silently contaminate private stat value. |

## Replacement And VOR Requirements

| id | requirement |
|---|---|
| NFS-061 | Use LVE replacement baselines for value-over-replacement: `QB14`, `RB30`, `WR46`, `TE14`. |
| NFS-062 | Compute `VOR_pos` from projected LVE PPG above the positional replacement line. |
| NFS-063 | Keep replacement-line choices tunable and covered by calibration tests. |

## Confidence And Guardrail Requirements

| id | requirement |
|---|---|
| NFS-064 | Confidence must include sample quality, source coverage, role clarity, health clarity, projection agreement, and stability. |
| NFS-065 | Missing current injury feed must degrade confidence and cap durability rather than invent certainty. |
| NFS-066 | Participation/route proxies must be marked as proxy/review-only unless true route denominators exist. |
| NFS-067 | Low confidence should reduce action certainty, not bury the player invisibly. |
| NFS-068 | Keep rankings review-only until identity, source coverage, sanity fixtures, and calibration gates pass. |

## Calibration Requirements

| id | requirement |
|---|---|
| NFS-069 | Add rolling season-forward backtest support. |
| NFS-070 | Use train/validation/test windows: train 2018-2023, validate 2024, test 2025. |
| NFS-071 | Backtest each output against its own target: private value to next-season LVE PPG, win-now to same-season VOR, dynasty hold to two-year discounted production, keeper to roster survival/retention, drop candidate to cut probability, trade value to production plus liquidity execution. |
| NFS-072 | Track Spearman rank correlation, MAE, Brier score, confidence calibration by decile, and error slices by position/age/injury/sample buckets. |
| NFS-073 | Tune only bucket weights, shrinkage constants, replacement lines, RB fragility coefficients, and elite QB/TE thresholds. |
| NFS-074 | Do not tune formulas against market outcomes. |

## Sanity Fixture Requirements

These are extracted from the report as expected behavior tests. They need audit before coefficients are locked.

| id | fixture | expected behavior |
|---|---|---|
| NFS-075 | Kyren vs Bijan/Gibbs/Jeanty | Bijan/Gibbs above Kyren in major scores; Kyren above Jeanty in private and win-now; Jeanty can close dynasty-hold gap but not win solely on youth. |
| NFS-076 | JSN vs Tee Higgins | JSN clearly over Higgins in private, dynasty hold, and usually win-now. |
| NFS-077 | BTJ vs Luther Burden | BTJ over Burden in private, dynasty hold, keeper, and trade; Burden may only win market edge if pricing creates edge. |
| NFS-078 | Chase Brown vs Luther Burden | Brown over Burden in private and win-now; Burden can only win dynasty hold if Brown role certainty deteriorates materially. |
| NFS-079 | Elite QB exception | Only QBs with clear QB14 separation plus rushing/efficiency edge break suppression. |
| NFS-080 | No-premium TE | Non-elite TEs should not outrank comparable WR25/RB25 profiles. |

## Rejected Features And Double-Counting Guards

| id | requirement |
|---|---|
| NFS-081 | Do not include ADP, startup prices, dynasty calculators, market ranks, or expert consensus inside private/stat value. |
| NFS-082 | Do not double count raw fantasy points and yards/TDs/first downs at full weight. |
| NFS-083 | Do not stack YPRR, targets per route, target share, and yards per target all at full weight. |
| NFS-084 | Do not stack snap share, route participation, and route count all at full weight. |
| NFS-085 | Do not stack actual TDs and expected TDs at full weight across multiple buckets. |
| NFS-086 | Do not separately stack injury designation, games missed, and durability penalties without consolidation. |
| NFS-087 | Do not score veteran draft capital after Year 2 except as a minor role-security tiebreaker if explicitly enabled. |
| NFS-088 | Do not use PPR-based expected-points totals for this no-PPR league. |

## UI And Workflow Requirements

| id | requirement |
|---|---|
| NFS-089 | Add source coverage views showing which nflverse/ffverse buckets are present per player. |
| NFS-090 | Add feature receipts showing raw value, shrunk value, normalized value, bucket, weight, source, date, imputation, and contribution. |
| NFS-091 | Add model comparison views for player-vs-player disputes using stats buckets, not just final rank. |
| NFS-092 | Add explicit preview/apply workflow for stats-first outputs. Raw source import and preview generation must not silently mutate active decision boards. |
| NFS-093 | Preserve review-only status until calibration gate passes. |

## Open Decisions Before Coding

| id | decision needed |
|---|---|
| NFS-D01 | Confirm exact passing-yard, interception, fumble-lost, and turnover scoring constants. |
| NFS-D02 | Decide whether to use Python-only ingestion, R-assisted export, or direct URL download for RDS-heavy sources. |
| NFS-D03 | Decide how to handle current-season injury/status gaps until a reliable feed is available. |
| NFS-D04 | Decide whether contract security uses OverTheCap import now or remains blank/proxy. |
| NFS-D05 | Decide if participation/route proxy is included in v1 or deferred until after core stats/opportunity/snap data works. |
| NFS-D06 | Decide whether named sanity fixtures from the report are accepted as hard ordering tests or softer review flags. |

## Immediate Implementation Order

1. Identity bridge and raw CSV contracts.
2. Weekly stats, snap counts, rosters, player IDs, and expected opportunity import adapters.
3. Local LVE actual/expected scoring derivation.
4. Source coverage and identity audit gates.
5. Normalization service with recency, shrinkage, winsorization, and percentile scoring.
6. Bucket score generation and feature receipts.
7. Stats-first veteran output preview only.
8. Sanity fixtures and player comparison audit.
9. Calibration/backtesting.
10. Explicit apply into active boards only after gates pass.
