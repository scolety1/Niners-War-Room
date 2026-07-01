# Full Sidecar Builder Contract

This packet does not build a full scoring sidecar. It defines the minimum contract a future builder must satisfy before label parity can be rerun.

## Required Source Inputs

- Use only the admitted `player_stats_weekly` and `player_stats_seasonal` receipts from `nflverse_player_stats_row_level_source_admission_v1_20260630`.
- Validate receipt row counts and SHA-256 before deriving any rows.
- Exclude quarantined fields.
- Use only safe identity joins already approved in tracked Data Hygiene packets.

## Required Output Grain

Primary grain: one row per observed player-week scoring component.

The future builder may emit explicit zero component rows only when:

- the player-week source row exists;
- the component field is present in the source schema;
- the component value is explicitly numeric zero;
- identity and review gates pass.

The builder must not create zero rows for missing player-week source rows.

## Required Flags

Every output row must preserve:

- `sidecar_review_allowed=true` only for rows passing source, schema, identity, and missingness gates;
- `label_truth_allowed=false`;
- `model_use_allowed=false`;
- `training_allowed=false`;
- `source_truth_allowed=false`.

## Required Blockers

Rows or components must remain blocked when:

- the field is quarantined;
- identity is not safe;
- the source row is missing;
- the field value is missing or non-numeric;
- special/return touchdown mapping would be ambiguous;
- a composite value cannot be summed exactly once.

## Required Handoff

A future full sidecar builder may proceed as a review-only derivation lane, but full Outcome scoring parity must remain unapproved until the builder output proves formula coverage, zero semantics, and special/return touchdown alignment.
