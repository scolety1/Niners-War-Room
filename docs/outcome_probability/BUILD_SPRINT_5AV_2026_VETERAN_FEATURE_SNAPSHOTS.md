# Build Sprint 5AV: 2026 Veteran Feature Snapshots

## Verdict

`PARTIAL_VETERAN_FEATURE_SNAPSHOTS_READY`

Sprint 5AV built the first legal local-only 2026 veteran feature snapshot layer
from the official 2025 nflverse player-stats source registered in Sprint 5AU.

This is not probability training. No probabilities, fake probabilities, app
wiring, rankings/sorting changes, decision automation, app-readable probability
tables, promoted artifacts, push, or deploy occurred.

## Local Outputs

Local-only exports were written under:

`local_exports/outcome_probability/sprint_5av_2026_veteran_feature_snapshots/`

Created files:

- `player_stats_2025_component_mapping.csv`
- `player_stats_2025_forbidden_field_quarantine.csv`
- `current_2026_identity_repair_audit.csv`
- `current_2026_veteran_feature_snapshots.csv`
- `current_2026_veteran_feature_coverage.csv`
- `current_2026_rookie_path_audit.csv`
- `current_2026_feature_snapshot_blockers.csv`
- `summary_sprint_5av.json`
- `README_SPRINT_5AV.md`

Tracked report:

`docs/outcome_probability/BUILD_SPRINT_5AV_2026_VETERAN_FEATURE_SNAPSHOTS.md`

## Component Mapping Result

Component mapping status:

`mapped_with_policy_and_quarantine`

Mapped into the renamed NWR 2026 prior-season schema:

- `prior_completed_season_games`
- `prior_completed_season_games_played`
- `prior_completed_season_games_active`
- `prior_completed_season_passing_yards`
- `prior_completed_season_rushing_yards`
- `prior_completed_season_receiving_yards`
- `prior_completed_season_rushing_first_downs`
- `prior_completed_season_receiving_first_downs`
- `prior_completed_season_receptions`
- `prior_season_nwr_ppg`
- `prior_season_nwr_finish_rank`
- `age_at_snapshot`
- `experience_at_snapshot`

Component details:

| Component | Mapping |
| --- | --- |
| Passing interceptions | `passing_interceptions` mapped to internal scoring key `interceptions`. |
| Split fumbles lost | `sack_fumbles_lost + rushing_fumbles_lost + receiving_fumbles_lost`. |
| Split 2PT fields | Passing/rushing/receiving 2PT conversion fields mapped to scoring inputs. |
| Return yards | `punt_return_yards + kickoff_return_yards`. |
| Return TDs | `special_teams_tds` used as special/return TD scoring proxy. |
| First downs | Direct rushing and receiving first-down fields used. |
| Games / active games | Distinct regular-season player-week rows used for games, games played, and games active in this sprint. |
| NWR PPG | Derived from mapped weekly NWR scoring totals divided by games with recorded stats. |
| NWR finish rank | Position-specific 2025 regular-season NWR total-score rank. |

## Season-Scope Policy

`REG_ONLY`

The raw 2025 source includes regular season and postseason rows, but 2026
prior-season veteran features use regular season only.

Reason:

- Prior NWR feature/label work used completed regular-season player-stat facts.
- Postseason opportunity is team-dependent and would introduce a different
  availability/use policy.
- The raw postseason rows remain preserved in the downloaded source for audit,
  but are excluded from the 2026 feature rows.

## Forbidden-Field Quarantine

Forbidden-field quarantine status:

`applied`

Detected and excluded from the feature snapshot export:

- `fantasy_points`
- `fantasy_points_ppr`
- EPA/model-like fields such as `passing_epa`, `passing_cpoe`, `rushing_epa`,
  `receiving_epa`, `pacr`, `racr`, and `wopr`
- `target_share`
- `air_yards_share`
- Current-pool rank/value fields such as `league_rank`, `official_rank`,
  `draft_value`, `market_value`, and `model_value`

No ADP, projections, public rankings, market/trade values, private score, or
RotoWire ranking/projection/outlook/value fields were emitted in the feature
snapshot rows.

## Identity Repair Result

Current pool:

- Total rows: 780.
- Modeled veteran QB/RB/WR/TE rows: 692.
- Rookie rows separated: 80.
- K rows not applicable: 8.

Identity repair results:

| Result | Count |
| --- | ---: |
| Matched to 2025 player stats | 520 |
| Unmatched | 168 |
| Ambiguous/manual review | 4 |

Matching tiers used:

- Existing GSIS ids on current rows.
- `sleeper_nflverse_identity_bridge.csv`.
- `dynastyprocess_db_playerids.csv`.
- Sleeper player id exports.
- Exact unique name/team/position fallback only when high confidence.

Low-confidence name-only matches were not silently accepted.

## Veteran Feature Snapshot Count

Output:

`current_2026_veteran_feature_snapshots.csv`

Rows:

| Snapshot status | Count |
| --- | ---: |
| Ready veteran feature snapshots | 517 |
| Blocked veteran rows | 175 |
| Total modeled veteran rows | 692 |

Breakdown:

| Source pool | Ready | Blocked |
| --- | ---: | ---: |
| Rostered players | 227 | 5 |
| Available veterans | 290 | 170 |

Ready rows include player identity, position, target season 2026, source season
2025, renamed prior-season feature fields, derived availability date, source
policy id, feature lineage, and explicit status. They do not include any
probability, rank/sort instruction, app display value, or model artifact.

## Veteran Rows Still Blocked

Blockers:

| Blocker | Rows |
| --- | ---: |
| `identity_unmatched_to_2025_stats` | 168 |
| `identity_position_mismatch` | 4 |
| `missing_2025_scored_row` | 4 |
| `missing_age_identity_metadata` | 3 |

Some rows have more than one blocker, so blocker counts can overlap.

Required follow-up:

- Repair unmatched identities using Sleeper, dynastyprocess, nflverse, and
  manual review.
- Review current position vs. 2025 stat position mismatches.
- Add legal DOB metadata for the small age-missing group or keep those rows
  blocked.

## Rookie Path Audit

Rookie rows:

- 80.
- Kept separate from veteran prior-season feature snapshots.
- Draft capital is available.
- 2025 CFBD college passing/rushing/receiving files are available for a future
  rookie schema design.
- Age/DOB availability is partial through identity files.

Rookie status:

`separate_rookie_model_design_can_start_later`

Do not force rookie rows through veteran prior-season features.

## Remaining Blockers

1. Identity repair is still needed for 168 unmatched veteran rows.
2. Four position-mismatch rows need manual review.
3. Four matched rows lack a usable modeled-position scored row.
4. Three otherwise matched rows lack legal DOB/age metadata.
5. Rookie path remains a separate future design.
6. Threshold model training, calibration, monotonicity, release gate, and display
   gate have not started.

## 5AW Decision

Sprint 5AW threshold model training should not start as a full training sprint
yet.

Why:

- The feature snapshot layer is useful and partially ready.
- Coverage is not complete: 517 of 692 modeled veteran rows are ready.
- The blocked identity/manual-review rows need HQ decision or repair before
  threshold model training proceeds.

Recommended next step:

Run an identity-repair sprint or approve a partial-coverage internal-training
policy before 5AW threshold model training.

## Confirmed Non-Actions

- No probabilities were created.
- No fake probabilities were created.
- No calibrated probabilities were created.
- No app probabilities were created.
- No app wiring was changed.
- No rankings or sorting were changed.
- No decision automation was created.
- No app-readable probability tables were created.
- No model artifacts were promoted.
- No push or deploy occurred.
