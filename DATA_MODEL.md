# Data Model

V1 uses local CSV data packs loaded into SQLite.

Canonical CSV files:

- `dim_players.csv`
- `fact_rosters.csv`
- `fact_official_rankings.csv`
- `fact_future_picks.csv`
- `fact_pick_values.csv`
- `fact_market_values.csv`
- `fact_player_features.csv`
- `model_outputs.csv`
- `owner_notes.csv`
- `metadata_sources.csv`

SQLite tables mirror these inputs:

- `players`
- `teams`
- `owners`
- `rosters`
- `official_rankings`
- `future_picks`
- `pick_values`
- `market_values`
- `player_features`
- `model_outputs`
- `owner_notes`
- `metadata_sources`
- `import_errors`

The app loads one active data pack at a time.
