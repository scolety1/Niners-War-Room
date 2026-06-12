# Build Sprint 5AT: 2025 Player Stats Registration

## Verdict

`BLOCKED_BY_MISSING_2025_PLAYER_STATS`

Sprint 5AT did not register completed 2025 NFL factual player stats because no
canonical 2025 player-stats source was available from the approved local/package
routes or the official nflverse player-stats release assets.

No placeholder file was created. No 2024 data was substituted for 2025. No
probabilities, app wiring, rankings/sorting changes, decision automation,
app-readable probability tables, promoted artifacts, push, or deploy occurred.

## Local Outputs

Local-only outputs were written under:

`local_exports/outcome_probability/sprint_5at_2025_player_stats_registration/`

Created files:

- `player_stats_2025_source_audit.csv`
- `player_stats_2025_component_audit.csv`
- `player_stats_2025_forbidden_field_audit.csv`
- `player_stats_2025_registration_decision.csv`
- `current_2026_veteran_feature_coverage_after_2025.csv`
- `current_2026_rookie_path_after_2025.csv`
- `remaining_2026_probability_blockers.csv`
- `summary_sprint_5at.json`
- `README_SPRINT_5AT.md`

## Source Acquisition Audit

Approved routes checked:

| Route | Result |
| --- | --- |
| `nflreadr::load_player_stats(...)` | Not available locally; `R`/`Rscript` were not on PATH. |
| Python nflverse equivalent | Not available locally; `nfl_data_py`, `nflreadpy`, and `sportsdataverse` were not installed in the repo venv. |
| Official nflverse GitHub release API | Queried successfully for `nflverse-data` tag `player_stats`. |
| Direct `player_stats_2025.csv` release URL | Not listed in official release assets. |
| Direct `stats_player_week_2025.csv` release URL | Not listed in official release assets. |

Official release audit:

- Source: `https://github.com/nflverse/nflverse-data/releases/tag/player_stats`
- API: `https://api.github.com/repos/nflverse/nflverse-data/releases/tags/player_stats`
- Asset count: 1,822.
- 2025 player-stats CSV assets found: 0.
- Max player-week asset found: `stats_player_week_2024.csv`.
- Existing recovered local canonical `player_stats.csv` max season: 2024.

Expected 2025 destination:

`local_exports/truth_set_lab/v3/downloads/player_stats_2025.csv`

Status:

`not_created_no_2025_source_acquired`

## Existing Canonical Aggregate

The recovered/local canonical aggregate remains useful for historical labels,
but it does not unblock 2026 veteran features.

| Path | Rows | Season coverage | Weekly rows | 2025 rows |
| --- | ---: | --- | --- | ---: |
| `local_exports/truth_set_lab/v3/downloads/player_stats.csv` | 134,470 | 1999-2024 | yes | 0 |

## Component Audit

Because no 2025 source was acquired, the 2025 component audit is
`not_evaluable_no_2025_source`.

The historical nflverse schema contains the main required component fields:

- Passing yards, passing TDs, interceptions.
- Rushing yards, rushing TDs, rushing first downs.
- Receptions, receiving yards, receiving TDs, receiving first downs.
- 2PT conversion components.
- Fumble-lost components split across passing/sack, rushing, and receiving
  fumbles lost.

Return-yard support remains not present in the historical schema. Return TD
support is partially represented through `special_teams_tds`. If a future 2025
source lacks first downs or return components, supplements must come only from
legal factual sources with documented lineage, such as official nflverse
play-by-play, and must not use projection/ranking/market/value sources.

## Forbidden-Field Audit

The historical schema includes fields that must be quarantined from prediction
features and labels:

- `fantasy_points`
- `fantasy_points_ppr`
- EPA/model-like fields such as `passing_epa`, `rushing_epa`, `receiving_epa`,
  `dakota`, `pacr`, `racr`, and `wopr`
- Share fields such as `target_share` and `air_yards_share`

Those fields were not used. They are excluded from any future 2026 feature
builder/registration mapping unless separately approved by source family and
field policy.

## Registration Decision

`BLOCKED_BY_MISSING_2025_PLAYER_STATS`

The source was not registered as completed prior-season factual data.

Reason:

No official canonical 2025 NFL player-stats CSV/package output was available
locally or in the official nflverse `player_stats` release assets at audit time.

Next action:

Acquire and register completed 2025 NFL player stats, then rerun this Sprint 5AT
registration audit.

## 2026 Veteran Feature Coverage

Recovered current 2026 pool:

| Row family | Rows |
| --- | ---: |
| Rostered players | 240 |
| Available veterans | 460 |
| Rookie draftables | 80 |
| Total | 780 |

Veteran coverage after 5AT:

| Metric | Count |
| --- | ---: |
| Modeled veteran QB/RB/WR/TE rows | 692 |
| Veteran rows with legal 2025 prior-season features | 0 |
| Veteran rows missing 2025 prior-season features | 692 |
| Modeled veteran rows with GSIS/nflverse identity blocker | 628 |
| K rows not applicable | 8 |

Coverage remains zero because the 2025 prior-season factual scoring source was
not registered. App board ranks, market/value fields, RotoWire fields, and 2024
stats were not used as substitutes.

## Rookie Path Update

Rookie rows:

- 80 rookie draftables.
- 2026 draft-capital file is present.
- 2025 CFBD college stats are present for rookie-path schema design.
- Age/DOB availability remains incomplete in the rookie draftable file without
  an additional identity/DOB source.

Rookie status:

`design_only_not_training_ready`

Rookies remain separate from the veteran prior-season feature path. Do not force
rookies into veteran features.

## Remaining Blockers

1. Canonical completed 2025 NFL player stats are missing.
2. Required 2025 scoring components cannot be validated without the source file.
3. Legal 2026 veteran feature coverage remains 0 of 692 modeled veteran rows.
4. Current-pool GSIS/nflverse identity still needs reconciliation.
5. Rookie schema/model head remains design-only.
6. No threshold probabilities, calibration, monotonicity, release gate, or
   display gate exists.

## 5AU Decision

Sprint 5AU 2026 veteran feature snapshots should not start yet.

Start 5AU only after a canonical completed 2025 NFL player-stats source is
acquired, component-mapped, forbidden-field quarantined, and registered as
completed prior-season factual data.

## Confirmed Non-Actions

- No probabilities were created.
- No fake probabilities were created.
- No app probabilities were created.
- No app wiring was changed.
- No rankings or sorting were changed.
- No app-readable probability tables were created.
- No decision automation was created.
- No model artifacts were promoted.
- No push or deploy occurred.
