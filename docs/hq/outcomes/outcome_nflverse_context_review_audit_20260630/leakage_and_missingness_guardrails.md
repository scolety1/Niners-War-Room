# Leakage And Missingness Guardrails

## As-Of Date Requirements

Every future model or display feature must declare:

- board as-of date
- feature source as-of date
- season/week coverage
- whether the data existed before the prediction anchor

No feature can use production, games, snaps, awards, roster/depth context, or
career information from after the target anchor.

## Pre-Draft vs Post-Draft

Pre-draft rookie modeling cannot use post-draft roster status, depth charts,
snap counts, player_stats, injuries, games, awards, or career length as input
features.

Post-draft review context can display factual current context only if it is
clearly labeled review/display-only.

## Injury / Availability Missingness

Missing injury context is not healthy, clean, low-risk, or recovered.

Allowed:

- injury context available
- report/practice status display
- availability caveat
- not enough information reason

Blocked:

- injury risk score
- medical risk
- recovery projection
- comeback probability
- health discount

## Depth Chart Leakage

Depth charts can be current review context. They are high leakage risk for
pre-draft or historical models unless an as-of gate proves the depth chart was
available at the prediction time.

Missing depth context is not no-role.

## Snap / Production Leakage

Snap counts and player_stats are factual production/usage context. For future
modeling, they require anchor-aligned windows. Future production cannot be used
as an input for earlier predictions.

Missing snap or production context is not zero usage.

## Schedule Context

Tracked schedule context has zero current/future rows for the 2026-06-30 as-of
date. Next game, opponent, and bye context must remain `Not enough information`
until a current/future schedule gate exists.

## Identity Review

Rows with `NEED_IDENTITY_REVIEW` cannot expose player-level context values as
truth. They may show review status only until Data Hygiene approves and rebuilds
the artifact.

## Draft Capital And UDFA

Missing draft capital is not confirmed UDFA.

Draft absence, roster appearance, stats appearance, depth chart appearance, or
snap appearance cannot confirm UDFA status.

## Global Missingness Rule

Missing data must display as:

`Not enough information`

Never:

- `0%`
- false
- healthy
- clean
- no role
- no usage
- no injury
- low risk
- confirmed UDFA
