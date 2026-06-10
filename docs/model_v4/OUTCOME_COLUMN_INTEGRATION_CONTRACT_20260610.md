# Outcome Column Integration Contract - 2026-06-10

## Purpose

This contract defines the landing zone for the future outcome-column package. It does not implement, invent, backfill, or display outcome probabilities. Until a real outcome package is supplied and integrated, Rankings must continue to show outcome fields as blank, `--`, or in development.

This work must not duplicate draft/rookie research or create a new outcome model from scratch.

## Current Active Model Baseline

- Active full-board CSV: `local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv`
- Expected active latest hash after WR/QB v2 and old-pocket QB guardrail:
  `263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4`
- Active rows: `240`
- Scored QB/RB/WR/TE rows: `232`
- Unscored kickers: `8`
- Expected active watch rows:
  - CeeDee Lamb around `#20`
  - Justin Jefferson around `#22`
  - Patrick Mahomes around `#67`
  - Matthew Stafford around `#91`
  - Chase Brown around `#24`

## Expected Package Landing Zone

When supplied, unzip the outcome package under:

`local_exports/model_v4/outcomes/incoming/<package_id>/`

Recommended normalized output folder after validation:

`local_exports/model_v4/outcomes/latest/`

Expected files:

- `outcome_player_probabilities.csv`
- `outcome_model_manifest.json` or `outcome_model_manifest.csv`
- `outcome_guardrail_report.csv`
- `outcome_missing_player_report.csv`
- `outcome_stale_probability_report.csv`
- Optional: `outcome_source_receipts.csv`

Do not merge into Rankings directly from `incoming/`. Validate first, normalize into `latest/`, then merge only through an approved loader.

## Required Identity Columns

At least one deterministic identity lane must be present:

- `player_id`, preferred if it matches the active full-board `player_id`.
- `canonical_player_key`, preferred if it matches `nfl:<normalized>:<position>`.
- `normalized_player_name` plus `position`.

Optional disambiguation fields:

- `player_name`
- `nfl_team`
- `age`
- `source_player_id`

Matching rules:

1. Exact `player_id`.
2. Exact `canonical_player_key`.
3. Exact `normalized_player_name` plus exact `position`.
4. Do not fuzzy-match into active probabilities.
5. Near/fuzzy matches can go only to `outcome_missing_player_report.csv` for human review.

## Required Probability Columns

Initial expected column names:

- `top_6_2026_prob`
- `top_12_2026_prob`
- `top_24_2026_prob`
- `top_36_2026_prob`
- `top_48_2026_prob`
- `top_6_2027_prob`
- `top_12_2027_prob`
- `top_24_2027_prob`
- `top_12_next_5y_prob`
- `useful_starter_prob`
- `bust_prob`

If the supplied package uses different names, create a reviewed mapping table before integration.

Validation rules:

- Values must be numeric probabilities between `0` and `1`, or blank for unavailable.
- Percent-like values such as `42` must not be silently treated as `42%`; require explicit package metadata or reject.
- Display should round honestly, preferably whole percentages or one decimal place at most.
- Do not invent precision.

## Required Confidence and Provenance Columns

Required:

- `outcome_confidence`
- `outcome_model_version`
- `outcome_generated_at`

Strongly recommended:

- `outcome_model_hash`
- `training_data_as_of`
- `feature_cutoff_date`
- `scoring_format_id`
- `league_format_id`
- `allowed_use`
- `blocked_use`
- `source_path`
- `source_column`

`outcome_generated_at` should be parseable ISO-8601 with timezone, or the manifest must provide a package-level generated timestamp.

## Guardrail Report Requirements

The package must include or allow generation of `outcome_guardrail_report.csv` with:

- `gate`
- `status`
- `observed_value`
- `threshold_or_expected`
- `details`

Required gates:

- banned input count is `0`
- no ADP/market/league/public rank/consensus/projection/trade calculator input
- no RotoWire rankings/projections input
- no prior draft history input
- no legacy active-pack `private_score` input
- no roster/team tag scoring input
- no active NWR score overwritten by outcome model
- legal draft pool remains pending
- 2026 5.04 remains no-baseline/manual watchlist/no exact equivalence
- Keenan Allen legacy `82.4` remains comparison-only
- Darius Slayton legacy `78.88` remains comparison-only

## Missing-Player Report

`outcome_missing_player_report.csv` should include:

- `player`
- `position`
- `provided_identity_fields`
- `match_attempted`
- `match_status`
- `reason`
- `recommended_next_action`

Missing rows must display `--` / in development in the app. Missing outcome rows must not block existing NWR score/rank display.

## Stale Probability Behavior

If `outcome_model_version`, `outcome_model_hash`, `feature_cutoff_date`, or `outcome_generated_at` does not match the active ranking/model context:

- show a stale/out-of-sync warning;
- do not hide the player;
- do not replace probabilities with guessed values;
- keep source receipts collapsed by default;
- allow human review before activation.

## Display Rules

If the probability file is missing:

- display `--` or `In development`;
- do not show fake probabilities;
- detail cards should say outcome model data is not available.

If the probability file is present but a player is unmatched:

- display `--`;
- add row to missing-player report.

If the probability model is stale or mismatched:

- show probabilities only if explicitly approved for review mode;
- show a stale warning near detail/receipts;
- do not present as final model certainty.

If probabilities are valid:

- use display-only probability columns;
- keep NWR rank/score sorting independent unless a later approved model explicitly changes that;
- include model version/hash/generated-at in collapsed receipts;
- do not create trade/cut/keep/draft/buy/sell/defer/target/start-sit recommendations.

## Blocked Use

Outcome columns cannot be used to alter:

- NWR Dynasty Score
- NWR Rank
- WR/QB v2 scoring
- old-pocket QB guardrail
- Draft Prep legal draftable status
- Decision Board actions
- pick baselines
- VORP/replacement
- market/league gaps

Any future scoring use requires a separate reviewed production patch.

## What To Send When The Zip Is Ready

Send a zip containing:

1. `outcome_player_probabilities.csv`
2. `outcome_model_manifest.json` or CSV manifest
3. `outcome_guardrail_report.csv`, if already generated
4. source/receipt documentation explaining inputs used
5. any column-name mapping notes if names differ from this contract

Do not send credentials, cookies, browser session files, or account secrets.
