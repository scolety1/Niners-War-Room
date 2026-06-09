# NFLVerse Player Stats Import Contract

## Status

This is a review-only source contract. Importing these rows does not mutate keeper,
drop, draft, trade, or forced-release scores. A row can affect rankings only after it
is transformed into the local raw CSV, normalized into feature rows, previewed,
audited, and explicitly applied to a copied data pack.

## Primary Source

| item | value |
|---|---|
| source | nflverse player stats |
| direct CSV | https://github.com/nflverse/nflverse-data/releases/download/player_stats/player_stats.csv |
| docs | https://nflreadr.nflverse.com/reference/load_player_stats.html |
| schedule docs | https://nflreadr.nflverse.com/articles/nflverse_data_schedule.html |
| access | direct CSV release, no scraping |
| local target | `nflverse_player_stats_weekly.csv` |
| confidence | 95 |

## Additional Official Context Sources

| source | direct CSV pattern | local target | identity note | confidence |
|---|---|---|---|---:|
| nflverse snap counts | `https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_{season}.csv` | `nflverse_snap_counts_weekly.csv` | Uses `pfr_player_id`; enrich with reviewed identity map when possible. | 88 |
| nflverse depth charts | `https://github.com/nflverse/nflverse-data/releases/download/depth_charts/depth_charts_{season}.csv` | `nflverse_depth_chart_weekly.csv` | Provides `gsis_id` and `espn_id`; still review ambiguous rows. | 78 |

## Fields Verified For LVE

The official player-stats release carries the fields needed to compute historical LVE
weekly production and several stats-first role/earning features:

- Passing: `passing_yards`, `passing_tds`, `interceptions`, `passing_first_downs`,
  `passing_epa`
- Rushing: `carries`, `rushing_yards`, `rushing_tds`, `rushing_first_downs`,
  `rushing_epa`, `rushing_fumbles_lost`
- Receiving: `targets`, `receptions`, `receiving_yards`, `receiving_tds`,
  `receiving_first_downs`, `receiving_air_yards`, `receiving_epa`,
  `receiving_fumbles_lost`
- Earning/role evidence: `target_share`, `air_yards_share`, `wopr`
- Identity: `player_id`, `player_name`, `player_display_name`, `recent_team`,
  `position`

## Current Limitations

- `player_stats.csv` does not solve Sleeper identity matching by itself. Use the
  identity bridge and manual review for ambiguous players.
- nflverse snap-count releases are useful for role security, but the public CSV uses
  `pfr_player_id` rather than the same weekly `player_id` carried by player stats.
  Do not attach snap counts to model features until the identity bridge maps that
  PFR ID to the local player row.
- This source is historical production and usage evidence. It does not replace
  projections, current injuries, route participation, or depth chart role.
- nflreadr schedule docs note current injury-data limitations after the prior injury
  source ended, so injury availability must remain a separate reviewed source.

## Implementation Notes

- Use `src.services.nflverse_player_stats_import_service` to transform official
  nflverse player-stat, snap-count, and depth-chart rows into local raw contracts.
- Player-stats command-line helper:
  `python scripts/import_nflverse_player_stats.py --input player_stats.csv --season 2025 --output local_exports/nflverse/raw/nflverse_player_stats_weekly.csv`
- Snap-count command-line helper:
  `python scripts/import_nflverse_snap_counts.py --input snap_counts_2025.csv --season 2025 --output local_exports/nflverse/raw/nflverse_snap_counts_weekly.csv --identity-map local_exports/nflverse/raw/nflverse_identity_map.csv`
- Depth-chart command-line helper:
  `python scripts/import_nflverse_depth_charts.py --input depth_charts_2025.csv --season 2025 --default-week 0 --output local_exports/nflverse/raw/nflverse_depth_chart_weekly.csv --identity-map local_exports/nflverse/raw/nflverse_identity_map.csv`
- Keep unsupported positions as raw context only; the scored model supports QB, RB,
  WR, and TE. Kickers remain excluded.
- Use regular season (`season_type=REG`) by default for fantasy model inputs.
- Market data remains excluded from private/stat value. These football fields are
  the preferred replacement for any hidden market influence.
