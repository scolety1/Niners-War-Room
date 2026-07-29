# NWR Outcome Columns V3 RC1

Release identifier: `NWR_OUTCOME_COLUMNS_V3_RC1`

## Outcome

The release is a field-level hybrid built from nested chronological out-of-fold
evaluation. It upgrades only challengers that pass every gate, retains C0 where
it remains strongest, and emits `Not enough information` for blocked or
unsupported applicable fields.

- governed fields: 72
- schema rows: 79 (72 governed + 7 aliases)
- challenger upgrades: 7
- C0 retained: 36
- directional holds retaining C0: 5
- weak-calibration blocks: 16
- low-sample blocks: 8
- current players with complete admitted feature evidence: 184/240
- governed integration rows: 17280
- numeric applicable display rows: 2528

## Horizons

Internal horizons are relative: `THIS_YEAR`, `NEXT_YEAR`, `T_PLUS_2`,
`WITHIN_3Y`, `WITHIN_5Y`, and `TWO_OF_NEXT_3Y`. For this board they render as
2026, 2027, 2028, Within 3 Years, Within 5 Years, and Two Qualifying Seasons
Within 3 Years. The two-of-three head is exposed only in expanded Player Compare.

## Guardrails

Outcome is display-only and cannot drive rank, sort, trade value, pick value,
draft order, or model input. Historical and current joins use exact IDs.
Wrong-position is `N/A`; insufficient or blocked applicable evidence is
`Not enough information`. Finished V1 remains byte-identical.
