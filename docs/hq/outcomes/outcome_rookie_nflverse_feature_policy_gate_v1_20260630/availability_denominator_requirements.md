# Availability Denominator Requirements

Verdict: `YELLOW_DENOMINATOR_REQUIREMENTS_DEFINED_NO_MODEL_USE`

Availability denominator context remains display/review-only where already approved. This packet does not compute new denominators, infer missed games, create health scores, change Injury/Availability UI, or approve model use.

## Current Source Posture

The availability denominator source gate is `YELLOW_PARTIAL_DENOMINATOR_ARTIFACT_READY`.

Allowed display/review inputs in the prior lane included:

- `weekly_rosters`;
- `schedules`;
- `snap_counts`;
- `player_stats_weekly`;
- `nflverse_player_context_display_artifact.csv`.

Rows still needing identity review remain gated. Missing denominator fields stay `Not enough information`.

## Global Rule

Missing availability is not:

- healthy;
- clean;
- no-risk;
- played;
- missed;
- inactive;
- zero snaps;
- zero stats.

## Blocked Logic

`games_missed_while_rostered` is not approved. It must not be inferred from:

- roster absence;
- injury report presence;
- practice status;
- missing snap rows;
- missing stat rows;
- schedule context;
- current player status.

## Required Future Denominator Gate

Before any availability denominator field can be used for model/training consideration, a future lane must define:

- exact game eligibility denominator;
- rostered-at-game rule;
- injured reserve and practice squad handling;
- bye-week exclusion;
- active/inactive source hierarchy;
- snap/stat evidence role;
- schedule source and game cancellation handling;
- identity gate;
- missingness policy;
- historical replay;
- leakage audit;
- label interaction audit.

## Medical Guardrail

Availability denominator fields cannot create:

- injury risk;
- durability score;
- medical projection;
- recovery projection;
- comeback projection;
- health discount;
- rank or trade adjustment.

Any future display must continue to use `Not enough information` for missing or gated values.
