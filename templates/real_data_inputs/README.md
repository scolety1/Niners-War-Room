# Real Data Input Templates

These templates are the safe starting point for real LVE data. They are header-only on purpose:
copy the folder you need into `local_exports/` or another ignored working area, fill rows there,
then build/score from the copy. Do not type real draft-day edits directly into `sample_data/`.

## Folders

- `data_pack/`: the app-ready V1 data pack shape used by Import Review, Team, War Board,
  Trade Central, Draft Room, and League Intel.
- `veteran_model/`: normalized veteran model inputs used to generate real `model_outputs.csv`.
- `rookie_model/`: rookie source inputs used by the rookie normalization and scoring flow.
- `historical_replay/`: calibration-only replay inputs for old rookie drafts, as-of model
  rows, separated hindsight outcomes, source catalog rows, and replay audit notes.
- `public_sources/`: raw projection, market, role, injury, bio, and normalized backfill
  intake files used before public data is allowed to affect veteran scores.
- `nflverse_stats_upgrade/`: nflverse player stats, snap counts, participation,
  depth charts, injuries, identity, projection, opportunity, and normalized-feature
  headers for the stats-first veteran model upgrade.

## Workflow

1. Refresh Sleeper into `local_exports/sleeper/`.
2. Merge league ranks from the league-rank document/PDF.
3. Fill or import veteran model inputs from real local sources.
4. Run the veteran model to generate real model outputs.
5. Build/promote a data pack from the refreshed local outputs and model output.
6. Review warnings before using any decision page.

Historical replay has a separate safety rule: as-of files may contain only information that
was knowable at that historical draft date. Hindsight outcomes belong in
`historical_outcomes.csv` and should never be copied into `model_replay_inputs.csv`.

Public-source intake has the same rule in current form: raw source rows are only
evidence. They must validate, match rostered Sleeper players, and be normalized into
`normalized_veteran_feature_backfill.csv` before they can become veteran feature scores.
The public-source templates follow the Phase 11 report contract: `player_key`
is the source-intake player join key, source references are domain-specific
fields such as `projection_source_id` and `market_source_id`, and the normalized
backfill file is wide by player with one column per veteran feature.
Before normalizing real imports, create a public-source snapshot under
`local_exports/public_source_snapshots/`. A snapshot copies every public-source
CSV and writes `source_snapshot_manifest.json` with row counts, validation
status, and SHA-256 checksums. Snapshot creation is blocked when source
validation is blocked.
Player matching is review-first. Source rows match roster/player records by
`player_key` or platform IDs before falling back to normalized `player_name` plus
position. Ambiguous or unmatched rows must be fixed before normalization; the app
will not guess between candidates.

The nflverse stats-upgrade folder is a stricter future lane for the same idea:
raw nflverse exports and projection imports become reviewable local CSVs first,
then derived LVE scoring, role, opportunity, injury, and normalized veteran
features can be generated in later phases. Phase 1 only commits the schemas and
docs. It does not fetch nflverse data, score players, or mutate live model
outputs.

League rank is only the summer/declaration rule input. It should never be used as a
private value, keeper score, drop score, or rookie score.
