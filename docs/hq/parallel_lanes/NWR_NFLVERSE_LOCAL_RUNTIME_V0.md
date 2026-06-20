# NWR nflverse Local Runtime V0

Date: 2026-06-20

Owner: Master/Main HQ

## Executive Summary

An existing local-only nflverse scratch dependency folder was found and reused. No install was performed.

`nflreadpy 0.1.5` is available at:

```text
C:\NWR_SHARED_DATA\vendor_spikes\nflverse\scratch\pydeps\
```

The Master repo runtime can use it by setting `PYTHONPATH` for the command only. This keeps `nflreadpy` outside all NWR repos and avoids changes to `pyproject.toml`, `uv.lock`, requirements files, package files, or repo virtual environments.

## Runtime Found

Existing local-only runtime/dependency source:

```text
C:\NWR_SHARED_DATA\vendor_spikes\nflverse\scratch\pydeps\nflreadpy
C:\NWR_SHARED_DATA\vendor_spikes\nflverse\scratch\pydeps\nflreadpy-0.1.5.dist-info
```

Runtime verification:

```text
nflreadpy version: 0.1.5
```

No new install was required.

## Safe Run Command

Use the bundled Python runtime plus local-only `PYTHONPATH`:

```powershell
$python = "C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$env:PYTHONPATH = "C:\NWR_SHARED_DATA\vendor_spikes\nflverse\scratch\pydeps"

& $python scripts/nflverse_scheduled_pull_v0.py `
  --seasons 2024 2025 `
  --datasets rosters weekly_stats snap_counts
```

This command writes only under:

```text
C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\
```

It does not create Lane Exchange packages, does not update `latest_candidate`, does not update `latest_approved`, and does not approve stats for private value.

## Live Limited Pull

A limited live pull was run from the committed V0 puller using the existing local-only `nflreadpy` dependency folder.

Snapshot:

```text
C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\20260620_212500_live_limited_committed\
```

Report:

```text
C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\20260620_212500_live_limited_committed\nflverse_pull_report.md
```

Datasets:

| Dataset | Status | Rows | Columns | SHA256 |
| --- | --- | ---: | ---: | --- |
| `rosters` | ok | 6,353 | 36 | `431a7e50554727e864ff988b3bbca53a04d2d2b4ef84ce07937e4615f360e816` |
| `weekly_stats` | ok | 38,402 | 115 | `4c890a16b4a09b38e2e8c04a5e94d6ce6d4cc47ccccd912f6c192bb12d00d59f` |
| `snap_counts` | ok | 53,227 | 16 | `b16c952551b0b5c2344ed31136da2369d77687a6e72ed02502bf47a999c01054` |

## Field Summaries

`rosters` includes identity and roster context fields such as:

```text
season, team, position, depth_chart_position, jersey_number, status, full_name,
first_name, last_name, birth_date, height, weight, college, gsis_id, espn_id,
sportradar_id, yahoo_id, rotowire_id, pff_id, pfr_id, fantasy_data_id,
sleeper_id, years_exp
```

`weekly_stats` includes player, team, week, passing/rushing/receiving, targets, first down, and advanced fields such as:

```text
player_id, player_name, player_display_name, position, position_group, season,
week, season_type, team, opponent_team, completions, attempts, passing_yards,
passing_tds, passing_interceptions, carries, rushing_yards, receptions,
targets, receiving_yards, receiving_tds
```

`snap_counts` includes:

```text
game_id, pfr_game_id, season, game_type, week, player, pfr_player_id, position,
team, opponent, offense_snaps, offense_pct, defense_snaps, defense_pct,
st_snaps, st_pct
```

## Identity Match Summary

The `rosters` and `weekly_stats` datasets matched 12 of 13 sample names:

```text
Drake Maye, Jaylen Warren, Darren Waller, Brock Purdy, Dak Prescott,
Zay Flowers, Keenan Allen, Chris Olave, Rashee Rice, Jameson Williams,
Brian Thomas Jr, Alec Pierce
```

`Brian Thomas` without suffix was missing because nflverse uses `Brian Thomas Jr` in these pulled datasets.

`snap_counts` returned a `player` name field. The follow-up puller polish now inspects `player` as a name field, so future reports can match snap-count identities without changing raw data.

## Quarantined Field Warnings

Quarantined fields were detected and must stay blocked from private value, hidden ranking, hidden sorting, model training, final draft-day decisions, simulations, and recommendations.

`rosters`:

```text
years_exp
```

`weekly_stats`:

```text
air_yards_share, fantasy_points, fantasy_points_ppr, pacr, passing_cpoe,
passing_epa, racr, receiving_epa, rushing_epa, target_share, wopr
```

`snap_counts`:

```text
none detected
```

## Full-Dataset Follow-Up

The committed V0 puller is validated for `rosters`, `weekly_stats`, and `snap_counts` with the existing local runtime.

During runtime inspection, `nflreadpy 0.1.5` exposed these useful method names:

```text
load_player_stats
load_rosters
load_rosters_weekly
load_snap_counts
load_participation
load_ff_opportunity
```

The follow-up puller compatibility polish added support for:

- `season_stats`: use `load_player_stats(..., summary_level="reg")`
- `weekly_rosters`: include `load_rosters_weekly`
- `opportunity`: include `load_ff_opportunity`
- `snap_counts` identity matching: include the `player` field
- structured identity reporting for original query, matched source name, source field, and exact-vs-alias match type
- Brian Thomas / Brian Thomas Jr report-only alias matching
- likely player ID/name/team/season/week/position field-role summaries

This is report/puller compatibility only; it does not create Lane Exchange packages or approvals.

## Install Plan If Runtime Is Missing Later

If the local-only `pydeps` folder is lost, install outside Git only:

```powershell
$python = "C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
New-Item -ItemType Directory -Force C:\NWR_SHARED_DATA\vendor_spikes\nflverse\scratch\pydeps
& $python -m pip install --target C:\NWR_SHARED_DATA\vendor_spikes\nflverse\scratch\pydeps nflreadpy==0.1.5
```

Do not install into any NWR repo virtual environment unless Tim/Master explicitly approves a separate dependency policy.

## Guardrails

- No repo dependency files were changed.
- No `pyproject.toml`, `uv.lock`, requirements file, package file, or lockfile was changed.
- No `.env`, key, or secret was created.
- No raw nflverse data was committed.
- No `C:\NWR_SHARED_DATA` content was committed.
- No Lane Exchange package was created.
- No `latest_candidate` or `latest_approved` pointer was changed.
- No private value, `veteran_private_values`, hidden sort/rank, model behavior, simulation, deployment, or scheduled task was created.

## Master Verdict

GREEN for local-only runtime reuse, limited live-pull validation, and puller compatibility polish.

YELLOW for full scheduled nflverse coverage until a full all-dataset pull is reviewed.
