# Label Parity Validator Summary

Verdict: `YELLOW_LABEL_PARITY_PARTIAL_ROW_LEVEL_BLOCKERS`

## Executive Summary

The NFLVerse player_stats sidecar is valid as review-only comparison substrate, but label parity cannot be fully computed from tracked artifacts.

The sidecar is row-level weekly first-down evidence. The tracked Outcome V2 label evidence is a field-level decision table summarizing complete rows, validation rows, calibration, and blocked fields. It does not expose row-level player-season labels with player IDs, seasons, outcome hits, and censoring status.

Therefore:

- sidecar substrate validation is GREEN;
- label parity is PARTIAL;
- `parity_ready=false` for every matrix row;
- no matched-player counts are fabricated;
- no label truth, model, training, or source-truth approval is granted.

## Sidecar Coverage

- Rows: `13,628`
- Unique NWR players: `233`
- Dataset: `player_stats_weekly`
- Seasons: `2024-2025`
- Weeks: `1-22`
- Positions: `K, QB, RB, TE, WR`
- Stat heads: `passing_first_downs`, `receiving_first_downs`, `rushing_first_downs`
- Quarantined fields used: `false`

## Outcome Label Coverage Available

Tracked Outcome V2 validation evidence by position:

| Position | Existing Label Complete Row Sum | Sidecar Rows | Sidecar Unique Players | Parity Status |
|---|---:|---:|---:|---|
| QB | 6,130 | 2,708 | 28 | Partial, no row-level labels |
| RB | 20,316 | 4,884 | 79 | Partial, no row-level labels |
| WR | 30,152 | 4,522 | 93 | Partial, no row-level labels |
| TE | 8,632 | 1,512 | 32 | Partial, no row-level labels |
| K | 0 | 2 | 1 | No Outcome label family |

## Primary Blocker

No tracked row-level Outcome label artifact exists at a comparable grain. A future parity gate needs row-level player-season labels with identity keys, season, position, label family, hit status, and censoring status.

## Guardrail Posture

Existing labels remain evaluation targets, not input features. The sidecar remains comparison substrate only.
