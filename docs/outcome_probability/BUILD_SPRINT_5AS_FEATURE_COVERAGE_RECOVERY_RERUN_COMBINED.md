# Build Sprint 5AS: Combined Feature Coverage Recovery Rerun

## Verdict

`BLOCKED_BY_MISSING_2025_PRIOR_SEASON_DATA`

The combined recovery materially improved local data availability. Historical
direct threshold support can now be rebuilt from recovered 2020-2024 NFL weekly
player stats, and the current 2026 player pool is available for coverage audit.

Actual 2026 threshold probability model training should not start yet because
canonical completed NFL 2025 `player_stats` / factual scoring data is still
missing. Without that source, the 2026 veteran prior-season feature generator
cannot legally emit prediction rows.

This sprint did not create app probabilities, fake probabilities, calibrated
probabilities, player-facing probabilities, rankings, sorting, app wiring,
app-readable probability tables, promoted artifacts, push, or deploy.

## Local Outputs

Local-only outputs were written under:

`local_exports/outcome_probability/sprint_5as_feature_coverage_recovery_rerun_combined/`

Created files:

- `combined_recovery_copy_log_20260612.csv`
- `combined_recovery_import_inventory.csv`
- `historical_source_inventory_after_combined_recovery.csv`
- `rebuilt_or_restored_threshold_support.csv`
- `current_2026_feature_source_inventory_after_combined_recovery.csv`
- `current_2026_row_coverage_audit_after_combined_recovery.csv`
- `veteran_prediction_feature_candidates_after_combined_recovery.csv`
- `rookie_prediction_path_audit_after_combined_recovery.csv`
- `extra_2025_support_file_audit.csv`
- `remaining_probability_blockers.csv`
- `summary_sprint_5as_combined_rerun.json`
- `README_SPRINT_5AS_COMBINED_RERUN.md`

## Historical Target/Head Support

Historical direct threshold support is now available for audit/training
planning. It was rebuilt locally from:

`local_exports/truth_set_lab/v3/downloads/player_stats.csv`

Scope:

- Regular-season NFL weekly player stats.
- Seasons 2020-2024.
- Positions QB, RB, WR, TE.
- Reconstructed NWR scoring components.
- Position-specific season total ranks and qualified PPG ranks.
- Direct threshold labels only, not prediction features.

Support output:

`rebuilt_or_restored_threshold_support.csv`

Rows rebuilt:

- 95 season/position/target support rows.
- 5 seasons x 19 direct threshold targets.
- 48 season/target rows are `candidate_internal_training`.
- 47 season/target rows are sparse and require caution or blocking.

## Threshold Support Findings

Targets with all five seasons candidate-ready by the current support heuristic:

- `same_year_qb_t18`
- `same_year_qb_t24`
- `same_year_rb_t24`
- `same_year_rb_t36`
- `same_year_rb_t48`
- `same_year_wr_t24`
- `same_year_wr_t36`
- `same_year_wr_t48`
- `same_year_te_t24`

Targets sparse in all five seasons:

- `same_year_qb_t6`
- `same_year_qb_t12`
- `same_year_rb_t6`
- `same_year_rb_t12`
- `same_year_wr_t6`
- `same_year_wr_t12`
- `same_year_te_t3`
- `same_year_te_t6`
- `same_year_te_t12`

Mixed support:

- `same_year_te_t18`: 3 candidate seasons and 2 sparse seasons.

The historical support unblock is meaningful, but it does not by itself unblock
actual 2026 probabilities because 2026 prediction feature rows remain missing.

## Canonical 2025 NFL Player Stats

`canonical_2025_nfl_player_stats_exists = no`

Recovered NFL `player_stats.csv` files contain:

- 134,470 weekly rows.
- Seasons 1999-2024.
- No 2025 rows.

No `player_stats_2025.csv` or equivalent canonical completed NFL 2025 offensive
scoring file was found. 2024 data was not substituted for 2025.

## Current 2026 Player-Pool/Identity Coverage

Recovered current data-pack pool:

| Source | Rows |
| --- | ---: |
| Rostered players | 240 |
| Available veterans | 460 |
| Rookie draftables | 80 |
| Total unique pool rows | 780 |

Position counts:

| Position | Rows |
| --- | ---: |
| QB | 113 |
| RB | 171 |
| WR | 309 |
| TE | 179 |
| K | 8 |

Identity coverage:

- Player/Sleeper id present for all 780 rows.
- GSIS/nflverse id present for 64 of 460 available veterans.
- GSIS/nflverse id present for 80 of 80 rookie draftables.
- GSIS/nflverse id absent for the 240 rostered rows in the recovered data pack.

The app board also restored 240 `full_player_board_value_review_rows.csv` rows.
Those rows remain app/value context only and are not legal prediction feature
rows because they include ranking/value/context fields that must not be used as
outcome-probability features.

## Veteran Feature Coverage

Veteran modeled rows audited:

- 692 QB/RB/WR/TE veteran rows.
- 0 legal 2026 prediction feature rows.
- 692 blocked by missing required renamed prior-season features.

Required features still missing include the Sprint 5R renamed prior completed
season fields, such as:

- `prior_season_nwr_ppg`
- `prior_season_nwr_finish_rank`
- `prior_completed_season_games`
- `prior_completed_season_games_played`
- `prior_completed_season_games_active`
- `prior_completed_season_rushing_first_downs`
- `prior_completed_season_receiving_first_downs`
- `prior_completed_season_receptions`
- `prior_completed_season_rushing_yards`
- `prior_completed_season_receiving_yards`
- `prior_completed_season_passing_yards`

These cannot be legally built for actual 2026 veteran predictions until
completed 2025 NFL factual scoring data is acquired and registered.

## Rookie Path Audit

Rookie rows audited:

- 80 rookie draftable rows.
- 80 have GSIS ids in the recovered draftable file.
- 2026 factual draft-capital file is present.
- 2025 CFBD passing, rushing, and receiving season files are present.

Rookie recommendation:

`READY_FOR_ROOKIE_PATH_DESIGN_ONLY`

The rookie path can move to schema design/audit, but it cannot be folded into
the veteran prior-season head. CFBD college stats are rookie-path inputs only
after separate schema legality review. They are not veteran NFL prior-season
features and do not replace canonical 2025 NFL player stats.

## 2025 Support Files

Files now present:

- 2025 nflverse depth charts.
- 2025 nflverse injuries.
- 2025 nflverse snap counts.
- 2025 CFBD player/team/recruiting/draft files.
- 2025 RotoWire manual support files.

What these files can be used for:

- Source coverage auditing.
- Context and identity review.
- Rookie-path schema design after legality review.
- Limited field-level support only after explicit source legality approval.

What these files cannot be used for:

- Replacing canonical completed NFL 2025 `player_stats`.
- Fake or placeholder 2026 veteran prior-season features.
- App probabilities.
- Calibrated probabilities.
- Player-facing probabilities.
- Rankings/sorting.
- RotoWire rankings, projections, outlooks, values, or market-like fields.

## Monotonicity Readiness

Monotonicity remains not evaluable because no player-level threshold
probabilities were generated.

Future internal threshold chains must still pass:

- QB: T6 <= T12 <= T18 <= T24.
- RB: T6 <= T12 <= T24 <= T36 <= T48.
- WR: T6 <= T12 <= T24 <= T36 <= T48.
- TE: T3 <= T6 <= T12 <= T18 <= T24.

No monotonicity repair was applied.

## Remaining Blockers

1. Canonical completed NFL 2025 player stats/factual scoring data is missing.
2. Legal 2026 veteran prior-season feature snapshots do not exist.
3. Current-pool GSIS/nflverse identity is partial and needs reconciliation.
4. Rookie threshold schema/head is not designed, trained, or validated.
5. Sparse direct targets need target-level training policy before release
   consideration.
6. Player-level threshold probabilities do not exist.
7. Calibration, monotonicity, release gate, and display gate audits have not
   passed for actual probabilities.

## Decision

Sprint 5AT actual 2026 threshold model training should not start yet.

Historical threshold support is now available for internal planning, but actual
2026 probability training/release remains blocked until the completed 2025 NFL
factual scoring source and legal 2026 feature generator are present.

## Do Next

1. Acquire and register canonical completed NFL 2025 `player_stats` / factual
   offensive scoring data.
2. Rebuild 2026 veteran prior-season feature snapshots with the Sprint 5R
   renamed schema.
3. Run identity bridge/reconciliation for the 780-row current pool.
4. Re-run 5AS coverage after the 2025 source is present.
5. Separately design the rookie feature schema/head using CFBD and factual draft
   capital only after legality review.
6. Then consider internal-only 5AT threshold training with sparse-target policy,
   calibration, monotonicity, and display-gate audits.

## Do Not Do Next

1. Do not substitute 2024 data for missing 2025 prior-season data.
2. Do not use app ranks, market ranks, values, trade values, projections, ADP,
   public rankings, RotoWire outlooks, RotoWire projections, RotoWire rankings,
   or RotoWire values as features.
3. Do not wire probabilities into the app.
4. Do not show exact percentages or probability bands.
5. Do not add rankings-table probability columns.
6. Do not sort by outcome probabilities.
7. Do not promote model artifacts.
8. Do not push or deploy.

## Confirmed Non-Actions

- No app probabilities were created.
- No fake probabilities were created.
- No placeholder probabilities were created.
- No calibrated probabilities were created.
- No player-facing probabilities were created.
- No app wiring was changed.
- No rankings or sorting were changed.
- No decision automation was created.
- No app-readable probability tables were created.
- No model artifacts were promoted.
- No push or deploy occurred.
