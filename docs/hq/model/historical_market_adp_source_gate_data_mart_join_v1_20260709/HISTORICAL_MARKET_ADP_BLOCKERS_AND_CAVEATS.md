# Historical Market / ADP Blockers and Caveats

## Primary Blocker

No historical/as-of-safe market or ADP data source was proven. The lane found current-context market data and display-only ADP packages, not a historical player-season market panel.

## Specific Caveats

- DynastyProcess is a useful public current market baseline, but the available local package is a `2026-06-19` scrape / `2026-06-23` fetch and is explicitly display-only.
- Sleeper ADP is a 2026 display-context candidate from an undocumented endpoint and is explicitly not approved for model training, rankings, hidden sort, or final recommendations.
- Current value receipts and final-board exports are current-board artifacts and cannot be used as historical Formula Data Mart inputs.
- Empty `player_market_inputs.csv` templates prove only schema intent; they do not provide source values.
- Rookie market overlay rows explicitly state that no admitted local player-level ADP/market source was loaded.

## Classification Counts

- `CURRENT_ONLY_BLOCKED_FOR_HISTORICAL`: `28`
- `CURRENT_ONLY_DISPLAY`: `60`
- `NOT_ENOUGH_INFORMATION`: `112`
- `SOURCE_GATE_REQUIRED`: `20`

## Tests Not Run

Component, formula x ingredient, and ingredient-combination tests were blocked because a clean market/ADP sidecar was not built.
