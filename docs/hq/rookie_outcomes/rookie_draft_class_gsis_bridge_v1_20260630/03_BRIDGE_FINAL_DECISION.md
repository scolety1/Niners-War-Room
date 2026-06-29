# Draft-Class / GSIS Bridge Final Decision - 2026-06-30

## Verdict

`PARTIAL_DRAFT_CLASS_GSIS_BRIDGE`

A review-only historical drafted-rookie bridge now exists under shared data.
It connects draft year/round/pick/team to GSIS/player_stats IDs and Outcome
V2 target-label availability for drafted QB/RB/WR/TE rows from 2012-2024.

## Counts

- Bridge rows built: 1025
- Rows linked to Outcome V2 labels: 919
- Rows missing GSIS/player_stats ID: 5
- Historical rookie probability rows built: 0
- Rankings/app wiring rows built: 0

## Gate C Retry

Gate C can be retried for a partial drafted-player historical label build.
It must keep UDFA and unlinked rows blocked, preserve right-censoring, and
keep all rows review-only unless a later gate explicitly approves more.

## Remaining Blockers

- No UDFA/free-agent rookie-entry bridge.
- No current 2026 CFBD-to-GSIS bridge.
- Some drafted rows lack outcome-label linkage.
- No model/training/source-truth promotion.
