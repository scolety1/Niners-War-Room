# Build Sprint 5M: Broader Historical Universe

Date: 2026-06-11

Verdict: `READY_FOR_5N_BROADER_HISTORICAL_REBUILD`

Sprint 5M identifies and scaffolds a broader source-safe historical player-season universe for 2023 and 2024. It does not train calibrated models, create app percentage values, create public/player-facing probabilities, create rankings, push, deploy, or modify active app/ranking logic.

## Mission

Sprint 5L produced 48 trainable historical rows, but the truth-set universe remained enriched:

- `same_year_starter`: one-class, 48 / 0
- `same_year_useful`: one-class, 48 / 0
- `same_year_replacement_or_bust`: one-class in the opposite direction, 0 / 48

Sprint 5M looks for a broader football-data-only universe that can add non-events, lower-tier rows, and replacement/bust cases without using public rankings, ADP, projections, market data, trade values, prior fantasy draft history, or legacy `private_score`.

## Sources Inspected

| Source | Status | Use |
| --- | --- | --- |
| `local_exports/truth_set_lab/v3/downloads/player_stats.csv` | `ready_candidate` | Primary broader player-season universe and label component source. |
| `local_exports/truth_set_lab/v3/reports/truth_set_v3_production_player_season.csv` | `ready_but_enriched_truth_set_only` | Comparison baseline. |
| `local_exports/truth_set_lab/v3/reports/truth_set_v3_usage_player_season.csv` | `manual_review_required` | Optional feature enrichment; not required for broad universe. |
| `local_exports/truth_set_lab/v3/reports/truth_set_v3_snap_share_player_season.csv` | `manual_review_required` | Optional feature enrichment; not required for broad universe. |
| `local_exports/nflverse/preview/sprint2_phase7_public_20260514/downloads/dynastyprocess_db_playerids.csv` | `ready_candidate` | Identity/DOB support. |

`player_stats.csv` contains imported fantasy totals and EPA-style fields (`fantasy_points`, `fantasy_points_ppr`, passing/rushing/receiving EPA, `pacr`, `racr`, `dakota`, `wopr`). These were quarantined and not used for labels or features.

## Universe Rules

The broader historical universe includes QB/RB/WR/TE player-seasons in 2023 and 2024 when a player:

- appears in local `player_stats.csv`,
- has a valid player ID,
- has a supported fantasy position,
- logs offensive activity through source-safe stat components.

Kickers are excluded. Fantasy relevance ranks, public rankings, ADP, projections, market values, trade values, prior league draft history, and legacy scores are not used to define inclusion.

## Candidate Universe Size

Label-eligible player-seasons:

| Season | QB | RB | WR | TE | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2023 | 81 | 136 | 211 | 116 | 544 |
| 2024 | 78 | 134 | 225 | 119 | 556 |

Total label-eligible rows: 1,100.

Blocked rows: 4.

Blocked reason:

- `no_offensive_activity`: 4 rows

No rows were blocked for missing player ID, missing supported position, or missing required scoring component coverage in the label-eligible set.

## Label Eligibility

Sprint 1-compatible labels can be estimated from source-safe raw components in `player_stats.csv`:

- passing yards / TD / interceptions
- rushing yards / TD / first downs
- receiving yards / TD / first downs
- receptions
- fumbles lost by component
- 2-point conversions
- special teams TDs

Imported fantasy totals are rejected as labels. EPA-style fields are not used.

Return yards, return TDs, and fumble recovery TDs remain governed by prior supplement policy and are not needed to determine whether the broader universe can improve event/non-event balance.

## Outcome Support Estimate

Aggregate support:

| Outcome | 2023 events / non-events | 2024 events / non-events | Status |
| --- | ---: | ---: | --- |
| `same_year_difference_maker` | 33 / 511 | 33 / 523 | Both classes present. |
| `same_year_starter` | 66 / 478 | 66 / 490 | Both classes present. |
| `same_year_useful` | 102 / 442 | 102 / 454 | Both classes present. |
| `same_year_replacement_or_bust` | 442 / 102 | 454 / 102 | Both classes present. |
| `next_year_starter` | 58 / 357 | 0 / 0 | 2023 mature; 2024 censored/unavailable. |

This materially improves the one-class problem from Sprint 5L.

## Truth-Set Vs Broader Universe

| Season | Truth-set rows | Sprint 5L trainable rows | Broader label-eligible rows | Additional vs truth set | Additional vs Sprint 5L |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2023 | 28 | 20 | 544 | 516 | 524 |
| 2024 | 35 | 28 | 556 | 521 | 528 |

The broader universe adds lower-tier QB/RB/WR/TE rows, starter/useful non-events, and replacement/bust cases.

## Feature Snapshot Readiness

Feature readiness estimate:

| Status | Count |
| --- | ---: |
| `ready_for_5n` | 827 |
| `blocked_missing_prior_source` | 277 |

By season:

| Season | Ready for 5N | Blocked missing prior source |
| --- | ---: | ---: |
| 2023 | 412 | 133 |
| 2024 | 415 | 144 |

Readiness is based on whether a prior completed-season player row exists for derived-availability features and whether identity/DOB support is available. Missing optional identity fields should remain missing, not zero-filled, in any future rebuild.

## Local Exports

Sprint 5M wrote local-only outputs under:

`local_exports/outcome_probability/sprint_5m_broader_historical_universe/`

Files:

- `broader_universe_candidate_players.csv`
- `broader_universe_source_coverage.csv`
- `broader_universe_label_eligibility.csv`
- `broader_universe_outcome_support_estimate.csv`
- `truth_set_vs_broader_universe_comparison.csv`
- `broader_feature_snapshot_readiness.csv`
- `blocked_broader_rows.csv`
- `README_SPRINT_5M.md`

## Readiness

Readiness verdict: `READY_FOR_5N_BROADER_HISTORICAL_REBUILD`

Sprint 5N can start a broader historical rebuild for rows marked `ready_for_5n`, while preserving all blocked and missing-prior rows in audit outputs.

Production/app modeling remains blocked until broader rebuilt rows pass feature legality, trainability support is re-audited, out-of-time validation is viable, confidence/display gates exist, and the final leakage audit passes.
