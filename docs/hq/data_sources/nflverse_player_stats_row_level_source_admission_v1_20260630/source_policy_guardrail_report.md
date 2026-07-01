# Source Policy Guardrail Report

## Result

PASS: review-only source receipt admitted without raw tracking.

## Confirmed Guardrails

- Raw shared/cache player_stats files were not staged or tracked.
- The approved NFLVerse safe runner was used with only `player_stats_weekly` and `player_stats_seasonal`.
- The runner did not write candidates, `latest_candidate`, or `latest_approved`.
- `label_truth_allowed=false` everywhere.
- `model_use_allowed=false` everywhere.
- `training_allowed=false` everywhere.
- `source_truth_allowed=false` everywhere.
- Missing data remains `Not enough information`.
- Player_stats remains sidecar substrate only, not label truth.

## Quarantined Fields

The runner quarantined these fields from private value/hidden sorting/model use:

`air_yards_share, fantasy_points, fantasy_points_ppr, headshot_url, pacr, passing_cpoe, passing_epa, racr, receiving_epa, rushing_epa, target_share, wopr`

They are marked `allowed_for_review=false` in the schema manifest.
