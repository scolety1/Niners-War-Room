# Dropped / Released Player Source Contract - 2026-06-09

## Purpose

This contract defines the future source file used to confirm which veterans/free agents become legally draftable after Roster Declaration Day.

The source is a legal draft-pool input, not a model-value input. It exists so Draft Prep and Live Draft Room can safely distinguish:

- confirmed dropped/released veterans;
- players still protected on rosters;
- players needing manual source review;
- rows that should remain blocked from confirmed legal draftability.

## Expected Source Timing

This file is expected after Roster Declaration Day, once teams have declared protected players and the league/user can identify officially released or dropped veterans.

Missing dropped-player files must not be interpreted as proof that no veterans are draftable. Until this source is supplied and validated, Draft Prep and Live Draft Room must continue to show `Legal Pool Pending`.

## Allowed Use

The dropped/released player source may be used for:

- legal draftable pool confirmation;
- Draft Prep candidate pool inclusion;
- Live Draft Room availability;
- source/status context;
- warning and data-needed explanations;
- manual review workflow for ambiguous rows.

## Blocked Use

This source must not be used for:

- NWR Dynasty Score;
- NWR Draft Value unless a separate admitted private scoring path approves that field;
- NWR Rank;
- formula components;
- VORP or replacement formulas;
- market/league gaps;
- final draft recommendations;
- any trade/cut/keep/buy/sell/defer/target instruction.

## Required Fields

The CSV must include:

- `player`
- `position`
- `nfl_team`
- `releasing_team_or_roster_owner`
- `release_status`
- `source_date`
- `source_file`
- `notes`
- `manual_review_required`
- `protected_status`
- `legal_draftable`
- `allowed_use`
- `blocked_use`

The starter template is:

`local_exports/model_v4/draft_prep/templates/dropped_released_players_template.csv`

## Optional Fields For Later

Future import passes may add optional fields such as:

- `sleeper_id`
- `canonical_player_id`
- `roster_id`
- `league_team_id`
- `release_source_url`
- `source_line_number`
- `source_confidence`
- `identity_match_method`
- `conflict_notes`

Optional fields must not bypass validation of the required fields.

## Validation Rules

The validator must:

- reject missing required columns;
- reject blank `player`;
- reject blank `position`;
- reject positions outside `QB`, `RB`, `WR`, `TE`, `K`;
- reject blank `source_date`;
- reject invalid `legal_draftable` values;
- reject invalid `manual_review_required` values when supplied;
- require `blocked_use` to forbid private value and final draft recommendations;
- write a validation report;
- never mutate active data packs;
- never merge rows into the draftable pool without a later explicit import task.

Validation report path:

`local_exports/model_v4/draft_prep/latest/dropped_released_players_validation_report.csv`

## Identity Matching Rules

Future import should match conservatively:

1. Exact canonical player id if supplied and already mapped in the repo.
2. Exact Sleeper id if supplied and already mapped in the repo.
3. Exact normalized full name plus position.
4. Exact player name plus current NFL team plus position.

Do not silently fuzzy-match ambiguous players. Near matches can be written to a manual review report only.

## Conflict Handling

If the dropped-player source conflicts with protected roster data:

- protected roster exclusion wins until manually resolved;
- keep `legal_draftable=false`;
- set `manual_review_required=true`;
- write a conflict warning;
- do not hide the row;
- do not create a private score change.

If identity is ambiguous:

- keep the row out of confirmed legal draftable status;
- keep `manual_review_required=true`;
- explain the needed identity/source evidence.

## Protected Roster Exclusion Rules

Players on protected rosters must not be marked confirmed legal draftable unless an official dropped/released source explicitly supersedes the protected roster record.

If a player appears both protected and dropped:

- classify as `protected_conflict_needs_review`;
- do not admit as legal draftable automatically;
- require manual confirmation from a league/source receipt.

## Manual Review Behavior

Rows with missing identity, conflicting protected status, unclear source date, or ambiguous release status should remain manual-review rows.

Manual review rows can appear in Draft Prep as `Source Limited` or `Needs Scouting` context, but not as confirmed legal draftable players.

## Draft Prep Feed

After a future approved import:

- confirmed rows can enter the Draft Prep candidate pool as `dropped_veteran_draftable`;
- source/status context should remain visible;
- warnings and data-needed notes should stay available in Advanced Audit;
- no private value should be changed by dropped-player status alone.

## Live Draft Room Feed

After a future approved import:

- confirmed rows can appear in Live Draft Room availability;
- protected/conflict rows must remain blocked or manual-review only;
- session/mock draft state must remain separate from source data;
- active data packs must not be mutated by marking a player drafted.

## Guardrail Summary

This contract prepares the import lane only. It does not supply any real dropped players, does not legalize preview veterans, and does not change Draft Prep, Live Draft Room, Rankings, Decision Board, or private model formulas.
