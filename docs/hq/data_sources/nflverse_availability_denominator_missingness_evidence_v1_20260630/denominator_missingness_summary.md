# Availability Denominator Missingness Summary

Verdict: `YELLOW_AVAILABILITY_MISSINGNESS_EVIDENCE_READY_HEALTH_INFERENCE_BLOCKED`

## Source State

- Base HEAD: `a35c2c1c7339d7a745d5d90e8af8d0624155a85c`
- Denominator artifact rows: 588
- Denominator season anchors: 2024, 2025
- Denominator `SAFE_NOW_DISPLAY_ONLY` player-season rows: 437
- Denominator gated player-season rows: 151
- Player context rows: 294
- Player context identity-safe rows: 281
- Player context gated rows: 13

## Field Policy Summary

- Fields audited: 14
- Display-capable fields with caveats: 13
- Fields blocked for value display: 1
- Health inference approved fields: 0
- Model approved fields: 0
- Training approved fields: 0
- Source-truth approved fields: 0

## Current Status Counts

- BLOCKED_NOT_ENOUGH_INFORMATION: 1
- DISPLAY_ONLY_CONTEXT_STRING: 1
- DISPLAY_ONLY_REVIEW_CAVEAT: 4
- DISPLAY_ONLY_SAFE_FOR_IDENTITY_SAFE_ROWS: 2
- DISPLAY_ONLY_SAFE_FOR_SUPPORTED_ROWS: 3
- DISPLAY_ONLY_SAFE_WHEN_PRESENT: 3

## Core Finding

Availability denominator fields are useful as display/review context for supported identity-safe rows, but they are not safe for health inference, model input, training input, or source truth. Missing availability remains `Not enough information`.

`games_missed_while_rostered` remains blocked. The current tracked artifacts do not provide a safe point-in-time game-status hierarchy that can distinguish a missed game from a missing snap row, missing stat row, roster-data gap, schedule gap, inactive status ambiguity, injury-report absence, bye week, or other censoring case.
