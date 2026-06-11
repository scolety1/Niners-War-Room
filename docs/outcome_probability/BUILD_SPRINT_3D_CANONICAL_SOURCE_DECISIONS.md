# Build Sprint 3D - Canonical Source Decisions

Status: READY_FOR_SPRINT_4_WITH_COMPONENT_WAIVERS

Sprint 3D resolved the Sprint 3C source-registration blocker for the first limited truth-set label/base-rate pass. It did not build v0 base rates, train models, create player probabilities, create rankings, create app percentage values, push, or deploy.

## Canonical Raw Scoring Source

Recommended canonical source for Sprint 4:

$prodRel

This file is suitable as the canonical raw offensive scoring source for the audited truth-set universe because it has row-level source_date, player identity, season/week/team/position, raw passing/rushing/receiving components, rushing first downs, receiving first downs, and fumbles lost. It has no imported fantasy totals and no detected banned rank/market/projection/private-score headers.

Limitations:

- It covers 1,183 player-week rows, 35 unique players, and seasons 2022-2024.
- It is a truth-set universe, not a full-NFL historical base-rate universe.
- It lacks some nonzero but rare scoring components, so Sprint 4 must use component waivers or registered supplemental sources.

## Source Decisions

See local_exports/outcome_probability/sprint_3d_source_registration/canonical_source_decisions.csv.

Key decisions:

- 	ruth_set_v3_production_player_week.csv: production_candidate.
- 	ruth_set_v3_usage_player_week.csv: production_candidate for feature snapshots after cutoff policy.
- 	ruth_set_v3_snap_share_player_week.csv: production_candidate for feature snapshots after cutoff policy.
- player_stats.csv: econciliation_only; rich raw stats but no row-level source timestamp and imported fantasy total fields must be quarantined.
- play_by_play_2022/2023/2024.csv.gz: econciliation_only; useful for special/return/first-down reconciliation but requires aggregation and strict field quarantine.
- sleeper_nflverse_identity_bridge.csv: econciliation_only; not a model feature or label source.
- Current 2026 draft-capital files: display_only for current rookie context, not historical Sprint 4 labels.
- Historical draft-pick files: manual_review_required because they need source timestamps and column allowlists.

## Missing Component Policy

See missing_component_policy.csv and aw_stat_component_coverage.csv.

Resolved policy:

- Passing first downs: optional_zero_weight_component; can default zero with audit.
- Sacks suffered: optional_zero_weight_component; can default zero with audit.
- Misc yards: optional_zero_weight_component; can default zero with audit.
- Two-point conversions: nonzero scoring component; needs user decision to waive or supplement.
- Return yards: nonzero scoring component; needs user decision to waive or supplement.
- Return TDs: nonzero scoring component; needs user decision to waive or supplement.
- Special TDs: nonzero scoring component; can be supplemented from player_stats.csv after registration or waived with audit.
- Fumble recovery TDs: nonzero scoring component; needs user decision to waive or supplement.

## Row-Family Readiness

See ow_family_readiness.csv.

- ll_player_pre_week1: ready for Sprint 4 label/base-rate exploration with component waivers.
- offseason_carryover: ready for Sprint 4 label/base-rate exploration with component waivers.
- ookie_post_draft: still needs historical draft-capital source registration for full feature rows.

## Leakage / Forbidden Field Findings

The canonical production candidate had no detected forbidden headers. Supplemental sources do contain quarantined fields:

- player_stats.csv: antasy_points, antasy_points_ppr must not be used as label sources.
- play-by-play files: EPA/WP/probability/post-play fields and fantasy identity fields must be excluded from predictive features.
- CFBD draft-pick file: pre-draft ranking/grade columns must be excluded.
- NFLVERSE draft-pick history has career outcome columns and must be column-allowlisted before use.

## Sprint 4 Recommendation

Sprint 4 can start as a limited, audited v0 base-rate pass over the truth-set universe only, with explicit component waivers and no app probabilities. Sprint 4 should not claim full-NFL production readiness until supplemental component policy, identity coverage, and historical draft-capital registration are complete.
