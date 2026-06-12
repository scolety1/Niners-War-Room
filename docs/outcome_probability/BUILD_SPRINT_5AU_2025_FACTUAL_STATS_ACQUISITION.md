# Build Sprint 5AU: 2025 Factual Stats Acquisition

## Verdict

`registered_2025_player_stats_direct`

Sprint 5AU resolved the missing 2025 factual player-stats source blocker. The
official nflverse player-week 2025 CSV was found under the changed
`stats_player` release tag, downloaded locally, audited, and registered as a
completed prior-season factual source for local/internal 2026 veteran feature
snapshot work.

No probabilities, fake probabilities, app wiring, rankings/sorting changes,
decision automation, app-readable probability tables, promoted artifacts, push,
or deploy occurred.

## Local Outputs

Local-only Sprint 5AU outputs were written under:

`local_exports/outcome_probability/sprint_5au_2025_factual_stats_acquisition/`

Created files:

- `nflverse_2025_stats_url_audit.csv`
- `nflverse_2025_pbp_availability_audit.csv`
- `pbp_2025_component_derivation_audit.csv`
- `player_stats_2025_source_audit.csv`
- `player_stats_2025_component_audit.csv`
- `player_stats_2025_forbidden_field_audit.csv`
- `player_stats_2025_source_registration.csv`
- `remaining_2025_data_blockers.csv`
- `summary_sprint_5au.json`
- `README_SPRINT_5AU.md`

Registered local source files:

- `local_exports/truth_set_lab/v3/downloads/player_stats_2025.csv`
- `local_exports/truth_set_lab/v3/downloads/player_stats_2025_source_metadata.json`
- `local_exports/truth_set_lab/v3/reports/player_stats_2025_player_season.csv`

The player-season report is regular-season only. The raw downloaded file is
kept intact and includes both regular-season and postseason rows.

## Direct Player-Stats URLs Checked

The audit checked plausible 2025 player-stats assets under three release tags:

- `player_stats`
- `stats_player`
- `stats_player_week`

Checked asset names included:

- `player_stats_2025.csv`
- `stats_player_week_2025.csv`
- `stats_player_week_2025.parquet`
- `stats_player_week_2025.rds`
- `stats_player_reg_2025.csv`
- `stats_player_reg_2025.parquet`
- `stats_player_reg_2025.rds`
- `stats_player_regpost_2025.csv`
- `stats_player_regpost_2025.parquet`
- `stats_player_regpost_2025.rds`

Results:

| Release tag | Result |
| --- | --- |
| `player_stats` | Release API status 200, but all checked 2025 player-stat direct URLs returned 404. |
| `stats_player` | Release API status 200, and 9 checked 2025 player-stat assets returned 200. |
| `stats_player_week` | Release tag not found; checked URLs returned 404. |

Winning source:

`https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_2025.csv`

Download metadata:

- HTTP status: 200.
- Bytes: 7,311,978.
- Last modified: Thu, 12 Feb 2026 10:00:51 GMT.
- SHA-256:
  `64252ba423652b9c6ce6f20d8fc3e3e501b1fabea0b111df77c41a4640c20bcf`

## Source Audit

Downloaded source:

`local_exports/truth_set_lab/v3/downloads/player_stats_2025.csv`

Source profile:

| Metric | Value |
| --- | ---: |
| Rows | 19,421 |
| Season coverage | 2025 only |
| Regular-season rows | 18,539 |
| Postseason rows | 882 |
| Week range | 1-22 |
| Unique player ids | 2,024 |
| Rows missing player id | 22 |
| Duplicate player-week keys | 0 |
| Teams | 32 |

Regular-season player-season aggregation:

`local_exports/truth_set_lab/v3/reports/player_stats_2025_player_season.csv`

Aggregation profile:

| Metric | Value |
| --- | ---: |
| Rows | 2,020 |
| Scope | Regular season only |
| Duplicate player-season keys | 0 |

## Component Audit

Required factual components are present in the direct 2025 source, with a few
mapping notes:

| Component | Status |
| --- | --- |
| Games / active games | Present, but policy/mapping required. Distinct player-week rows can derive games with recorded stats; true active games may need participation or roster source. |
| Passing yards | Present direct. |
| Passing TD | Present direct. |
| Interceptions | Present as `passing_interceptions`; map to internal `interceptions` naming. |
| Rushing yards | Present direct. |
| Rushing TD | Present direct. |
| Rushing first downs | Present direct. |
| Receptions | Present direct. |
| Receiving yards | Present direct. |
| Receiving TD | Present direct. |
| Receiving first downs | Present direct. |
| Fumbles lost | Present as split fields; sum `sack_fumbles_lost`, `rushing_fumbles_lost`, and `receiving_fumbles_lost`. |
| 2PT components | Present as passing/rushing/receiving split fields. |
| Return yards | Present as punt and kickoff return yards. |
| Return TDs | Partial via `special_teams_tds`; PBP may be needed if split punt/kick attribution matters. |

## Forbidden-Field Audit

Fields detected and quarantined:

- `fantasy_points`
- `fantasy_points_ppr`
- EPA/model-like fields: `passing_epa`, `passing_cpoe`, `pacr`,
  `rushing_epa`, `receiving_epa`, `racr`, `wopr`
- Share fields: `target_share`, `air_yards_share`

No ADP, rankings, projections, market/trade values, or RotoWire blocked fields
were detected in the direct source. Quarantined fields must not be used as
prediction features or labels.

## PBP Availability

2025 PBP is available under the official `pbp` release tag:

| Asset | Status |
| --- | --- |
| `play_by_play_2025.csv` | Listed, HTTP 200 |
| `play_by_play_2025.csv.gz` | Listed, HTTP 200 |
| `play_by_play_2025.parquet` | Listed, HTTP 200 |
| `play_by_play_2025.rds` | Listed, HTTP 200 |
| `play_by_play_2025.qs` | Listed, HTTP 200 |

The alternate `play_by_play` release tag was not found.

PBP derivation was not performed because direct official player-week stats were
acquired. The PBP header audit indicates fallback derivation is plausible for
the main factual components, with additional attribution tests needed for
fumbles lost, 2PT conversions, and return touchdowns.

## Source Registration

Registration decision:

`registered_2025_player_stats_direct`

Registered use:

`yes_for_local_internal_feature_snapshot_building`

This registration does not release probabilities. It only makes the 2025
factual source available for the next local/internal feature snapshot build.

## Remaining Blockers

1. Component mapping is required before building 2026 veteran feature snapshots.
   The 2025 schema uses `team` and `passing_interceptions`, and split fumble/2PT
   fields need explicit mapping.
2. Current-pool identity repair is still required. The recovered data-pack rows
   have 628 of 692 modeled veteran rows without GSIS/nflverse id.
3. Rookie rows remain separate. There are 80 rookie draftables that should not
   be forced into veteran prior-season features.
4. Probability training/release gates remain blocked. No model training,
   calibration, monotonicity, release gate, display gate, or app display was
   created in Sprint 5AU.

## 2026 Veteran Feature Snapshot Decision

Sprint 5AU unblocks the missing 2025 source. Sprint 5AV / 2026 veteran feature
snapshot work can start, but it must begin with component mapping and current
pool identity repair.

Actual probabilities, training output, app display, and sorting remain blocked.

## Confirmed Non-Actions

- No probabilities were created.
- No fake probabilities were created.
- No calibrated probabilities were created.
- No app wiring was changed.
- No rankings or sorting were changed.
- No app-readable probability tables were created.
- No decision automation was created.
- No model artifacts were promoted.
- No push or deploy occurred.
