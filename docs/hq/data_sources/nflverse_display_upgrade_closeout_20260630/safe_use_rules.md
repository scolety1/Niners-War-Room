# NFLVerse Display Safe-Use Rules

These rules apply to every app, docs, review, and future feature-policy lane that reads
the merged NFLVerse display artifacts.

## Required Row Gates

Use player-level context only when all are true:

- Join by `nwr_player_id`.
- `identity_join_status=SAFE_NOW_DISPLAY_ONLY`.
- `review_required=false`.
- `display_only=true`.
- `model_use_allowed=false`.
- `training_allowed=false`.
- `source_truth_allowed=false`.
- `rank_logic_allowed=false`.
- `hidden_sort_allowed=false`.
- `trade_value_allowed=false`.
- `pick_value_allowed=false`.
- Field/schema status allows display.

## Missingness Rules

- Missing data displays as `Not enough information`.
- Missing data is never zero, false, clean, healthy, safe, no-role, no-usage, neutral,
  favorable, confirmed undrafted, or low-risk.
- Identity-review rows expose no detailed context.
- Identity recommendations are not approved identities.

## Blocked Uses

NFLVerse display artifacts must not be used for:

- model input
- model training
- source truth
- rank logic
- hidden sort
- recommendations
- trade value
- pick value
- start/sit
- schedule strength
- opponent difficulty
- injury risk
- durability score
- medical or comeback projection
- rookie/veteran active outcome probabilities
- Gate G activation

## Raw Data Rule

App pages must not read raw `C:\NWR_SHARED_DATA`, `local_exports`, raw cache, vendor,
Gmail, runtime JSON, or secret paths. App pages should read only tracked compact display
artifacts and approved service helpers.
