# Games Missed While Rostered Blocker Report

## Status

`games_missed_while_rostered` remains blocked and must display as `Not enough information`.

## Evidence

- Source artifact: `docs\hq\data_sources\nflverse_availability_denominator_display_v1_20260630\availability_denominator_display_artifact.csv`
- Total denominator rows: 588
- Missing `games_missed_while_rostered` rows: 588
- Safe value rows: 0
- Display approval: `false` for computed missed-game values
- Health inference approval: `false`
- Model/training/source-truth approval: `false`

## Why It Is Blocked

The current approved artifacts can show rostered-game denominators and observed snap/stat participation for supported rows, but they cannot safely prove that a player missed a game while rostered. Absence of snaps or stats may reflect missing source data, role, inactive status, bye/schedule handling, game status ambiguity, or dataset coverage gaps. Injury report absence is also not healthy or available.

A future gate must define and test a point-in-time game-status hierarchy before this field can move beyond `Not enough information`.
