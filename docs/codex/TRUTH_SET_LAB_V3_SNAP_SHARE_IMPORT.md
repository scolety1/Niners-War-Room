# Truth Set Lab v3 Phase 4: Snap Share Import

## Status

Review-only preview data has been generated from official nflverse snap-count
files. This phase does not overwrite active rankings, model scores, roster
decisions, draft boards, or readiness gates.

## Source

| item | value |
|---|---|
| source | nflverse snap counts |
| direct file pattern | `https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_{season}.csv` |
| seasons imported | `2022`, `2023`, `2024` |
| local cache | `local_exports/truth_set_lab/v3/downloads/snap_counts_{season}.csv` |
| source status | `imported_real_data` |
| scraping required | no |

The importer uses existing local snap-count files when present and downloads
official nflverse files only when a season is missing from the v3 cache.

## Outputs

| output | path |
|---|---|
| player-week snap preview | `local_exports/truth_set_lab/v3/reports/truth_set_v3_snap_share_player_week.csv` |
| player-season snap preview | `local_exports/truth_set_lab/v3/reports/truth_set_v3_snap_share_player_season.csv` |
| missing-player report | `local_exports/truth_set_lab/v3/reports/truth_set_v3_snap_share_missing_players.csv` |
| summary | `local_exports/truth_set_lab/v3/reports/truth_set_v3_snap_share_summary.csv` |

## Generated Summary

| metric | value |
|---|---:|
| truth-set players | 40 |
| matched players with nflverse IDs | 35 |
| missing players | 5 |
| snap rows seen | 79,536 |
| player-week rows | 1,214 |
| player-season rows | 83 |
| identity warning rows | 0 |

The missing players are current incoming/young players without matched 2022-2024
nflverse production IDs in the existing truth-set production preview:

- Jayden Higgins
- Oronde Gadsden II
- Kaleb Johnson
- Luther Burden
- Ashton Jeanty

No fake snap rows were created for them.

## Imported Fields

The preview keeps the fields needed for real snap-share evidence:

- `season`
- `week`
- `game_id`
- `team`
- `position`
- `player_id`
- `pfr_player_id`
- `gsis_id` where the PFR identity bridge is available
- `sleeper_id` where the PFR identity bridge is available
- `offense_snaps`
- `offense_pct`
- `snap_share`
- `game_with_offensive_snaps`
- `source_status`
- `source_url`
- `source_date`

Season rows aggregate games, games with offensive snaps, total offensive snaps,
and average offensive snap share.

## Important Labeling Rule

This phase imports **snap share only**. It explicitly does not estimate:

- routes run
- route participation
- targets per route run
- yards per route run

Every generated row carries the note
`snap_share_only_not_route_participation` or
`season_average_snap_share_only_not_route_participation`.

## Identity Mapping

Official nflverse snap-count rows expose `pfr_player_id`. The preview enriches
those rows with `gsis_id` and `sleeper_id` when the local identity map has a
ready PFR match. It also attaches the nflverse `player_id` from the v3 production
preview using deterministic name/position/team matching.

The generated run had zero identity warning rows. Future runs can emit:

- `missing_pfr_player_id`
- `pfr_id_not_in_identity_map`
- `identity_map_not_ready`

## Safety

- Active rankings overwritten: false
- Model scores changed: false
- Readiness labels changed: false
- Review-only status retained: true
