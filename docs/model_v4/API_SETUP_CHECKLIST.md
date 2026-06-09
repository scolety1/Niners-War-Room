# API Setup Checklist

This checklist is the local setup layer for future API/source work. It does not
turn on live imports by itself and does not change model values.

## Files

- `.env.example` documents local environment variables.
- `.env` is ignored by git and should hold any local secrets.
- `config/api_source_permissions.csv` lists each source's access mode and whether
  it is enabled by default.
- `config/source_registry.csv` controls source admissibility and private-value
  firewall policy.

## Current Defaults

- Sleeper league ID is available by default: `1344772855908290560`.
- Live API calls are disabled unless `MODEL_V4_LIVE_API_ENABLED=true`.
- Paid/commercial feeds are disabled until explicitly licensed and approved.
- RotoWire and PFF are manual-export roots only, not live scrapers.

## Before Running Live Imports

1. Copy `.env.example` to `.env`.
2. Set only the credentials/export roots actually needed.
3. Confirm the source row in `config/source_registry.csv`.
4. Confirm the access row in `config/api_source_permissions.csv`.
5. Make the importer write raw cached data under `local_exports/api_cache` or a
   source-specific local export folder.
6. Add a source firewall test before allowing the imported table into private value.

## Source-Specific Notes

- Sleeper: public/read-only league truth and IDs. Trending adds/drops are
  display-only.
- nflverse: factual evidence backbone. Prefer cached structured data and schema
  checks.
- CollegeFootballData: needs `CFBD_API_KEY` for live API work.
- RotoWire: user-provided/permitted structured exports only. No premium text
  scraping.
- SportsDataIO: requires paid key and source-specific contract.
- PFF: manual export only until exact licensed factual fields are admitted.

## Safety Rule

No API key, export root, market feed, projection feed, or ranking feed can bypass
the source registry. Display-only remains display-only.
