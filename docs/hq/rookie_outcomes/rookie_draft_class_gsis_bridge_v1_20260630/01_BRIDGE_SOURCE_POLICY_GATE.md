# Bridge Source-Policy Gate - 2026-06-30

## Verdict

`PARTIAL_BRIDGE_SOURCE_POLICY`

The bridge may use public structured nflverse draft-picks data for
review-only historical drafted-player bridge rows. This is partial because
it covers drafted players only, has a small number of missing GSIS IDs,
and does not approve any model/training/source-truth use.

## Approved Review-Only Source Candidate

- Source: `https://github.com/nflverse/nflverse-data/releases/download/draft_picks/draft_picks.csv`
- Dictionary: `https://nflreadr.nflverse.com/reference/dictionary_draft_picks.html`
- Fields used: season, round, pick, team, gsis_id, pfr_player_id,
  cfb_player_id, pfr_player_name, position, college.

## Counts

- Drafted QB/RB/WR/TE rows: 1025
- Rows with GSIS/player_stats ID: 1020
- Rows linked to Outcome V2 labels: 919

## Guardrails

- `review_only=true`
- `model_use_allowed=false`
- `training_allowed=false`
- No rookie probabilities.
- No Rankings/app wiring.
- Missing data remains `Not enough information`, never `0%`.
