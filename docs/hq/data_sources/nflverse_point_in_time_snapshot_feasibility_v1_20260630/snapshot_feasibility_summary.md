# Snapshot Feasibility Summary

Verdict: `YELLOW_POINT_IN_TIME_SNAPSHOT_FEASIBILITY_READY_NO_REPLAY_APPROVAL`

## Source State

- Base HEAD: `9dafea81b3316a02f8a051762b9d53dc84791fc7`
- Player context artifact rows: 294
- Player context safe display rows: 281
- Player context gated rows: 13
- Availability denominator rows: 588
- Availability denominator safe player-season rows: 437
- Availability denominator gated rows: 151
- Feature families audited: 12

## Feasibility Counts

- Feature families with some tracked date/week/source-as-of evidence: 10
- Feature families with any as-of-like field: 1
- Feature families with season/week/season-anchor fields: 7
- Feature families with historical snapshots available: 0
- Replay-safe now: 0
- Experiment-safe now: 0
- Model/training/source-truth approved now: 0

## Current-Only Risk

- high: 8
- medium: 4

## Finding

Tracked NFLVerse display artifacts include useful display-time context and some season/week/date fields, but they do not include a complete point-in-time snapshot manifest. Current display safety does not imply historical replay safety. No audited feature family is safe for replay, experiment, model, training, or source-truth use now.
