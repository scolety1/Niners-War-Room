# Model v4 Confidence Cap Identity / Missingness Validation

## Identity Result

`PASS_GSIS_PLAYER_ID_PRESENT`

- Duplicate player-season-position keys: `0`
- Blank player IDs: `0`
- Positions: `QB=754, RB=1429, TE=1211, WR=2124`
- Seasons: `2013-2025`

## Missingness Result

`PASS_CLASSIFIED_UNKNOWN_NOT_TRUE_ZERO`

- `component_missingness_present`: `28`
- `source_columns_present`: `5490`

True zero is not inferred from absent component source columns. Missing or empty component coverage is classified as unknown component missingness.
