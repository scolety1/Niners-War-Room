# NWR NFLVerse Dataset-Level Refresh Health Safety Report

Date: 2026-06-30

## Scope

This lane is Refresh/Data Health visibility only. It does not approve nflverse data for
model input, rank logic, source truth, hidden sort, trade value, pick value, draft
decisions, or app-facing probability logic.

## Guardrails

Kept blocked:

- Dynasty Rank changes
- tier changes
- Final Board Rank changes
- frozen board mutation
- pinned snapshot/hash mutation
- `latest_candidate` writes
- `latest_approved` writes
- model/source-truth gate changes
- hidden sort changes
- Live Draft / Mock Draft changes
- runtime draft-state changes
- raw/shared/generated CSV tracking

## Missing Data Policy

For every nflverse dataset row:

- missing source metadata means `Not enough information`
- unsupported runner coverage means `NOT_CONFIGURED`
- missing usage is not `0`
- missing injury context is not clean health
- missing depth chart context is not no-role
- missing roster/status context is not clean availability
- missing row counts are not fabricated

## Dataset Safety Status

Configured dataset health rows can become GREEN only when local snapshot metadata has
rows and required schema/coverage/freshness/missingness checks pass.

Not currently configured in the Safe Refresh runner:

- `pbp`
- `injuries`
- `depth_charts`
- `draft_picks`
- `schedules`
- `ff_playerids`

These rows are visible as YELLOW/`NOT_CONFIGURED` rather than hidden.

## Required Human Interpretation

GREEN means the refresh-health checks for that local snapshot passed. It does not mean
the dataset has been promoted into any ranking, model, trade, pick, or source-truth
decision.

YELLOW or `NOT_CONFIGURED` means review is required before relying on the dataset. It
does not imply a negative player state.
