# Leakage Blocker Report

Verdict: `YELLOW_LEAKAGE_BLOCKERS_DEFINED_NO_EXPERIMENT_APPROVAL`

This lane finds no feature family safe for model experiment now. The blockers below must be cleared by later evidence lanes before sandbox or shadow experiments can be considered.

## Blocking Themes

## Current-State Backfill

Current display values cannot be backfilled into historical rows. Roster, injury, practice, depth chart, schedule, snap, last-active, contract, and identity fields all need source snapshots tied to the historical prediction anchor.

## Roster Cut And Survival Leakage

Roster and weekly roster fields can encode whether a player survived cutdowns, stayed active, or returned to a roster after the prediction date. This is especially dangerous for rookie and post-draft evaluation.

Blocked families:

- roster status;
- weekly roster status;
- depth chart role;
- availability denominator fields;
- games_missed_while_rostered.

## Injury And Practice Timing Leakage

Injury and practice fields require publication timing. A late-week injury report cannot be used for an earlier-week prediction, and no injury field may become injury risk, durability, medical projection, or comeback projection.

Blocked families:

- injury report status;
- practice status;
- availability denominator fields;
- games_missed_while_rostered.

## Depth Chart Timing Leakage

Depth chart role can reveal opportunity after camp, cuts, injuries, or performance. It is not a pre-draft feature and is not UDFA proof.

Blocked family:

- depth chart role.

## Usage And Activity Leakage

Snap recency, snap sample, last active season, and last active week can reveal future production, game participation, or career survival.

Blocked families:

- snap recency / sample;
- last active season / week;
- player_stats sidecar.

## Schedule Timing Leakage

Schedule next game, opponent, and bye context require a schedule-as-of snapshot. They cannot become recommendation, matchup strength, start/sit, playoff odds, or trade timing signals.

Blocked family:

- schedule next game / opponent / bye.

## Draft And Entry Leakage

Draft capital is only a post-draft candidate. Combine data needs event-date availability. Missing draft capital does not confirm UDFA, and UDFA modeling remains blocked.

Blocked or gated families:

- draft capital;
- combine;
- UDFA status.

## Source Policy Blocks

Some sources are blocked before replay is even considered.

Blocked families:

- CFBD joins;
- UDFA status;
- `ff_rankings`;
- market / ADP / DynastyProcess.

## Experiment Status

`safe_for_model_experiment_now=false` for all audited families.
