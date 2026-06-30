# Player Compare NFLVerse Context Activation Summary

Date: 2026-06-30

Branch: `work/lane-player-compare-upgrade-20260630`

Base HQ consumed: `origin/work/hq-parallel-control` at
`2070a2f4ffa6b6ae83bd6ca1529880f67dd6cab0`.

## Source Artifacts

Player Compare consumes only tracked repo artifacts:

- `docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv`
- `docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_schema_manifest.csv`
- Supporting HQ source-policy, join-health, identity-review, schedule-audit, and refresh-health docs.

It does not read raw shared nflverse cache files.

## Observed Artifact Coverage

- Player context artifact rows: `294`
- Safe display rows: `240`
- Identity review rows: `54`
- Identity proposal rows in the tracked proposal artifact: `54`
- Safe current/future schedule rows for next game/opponent/bye: `240`

The packet referenced 43 proposal rows, but the current tracked HQ artifact
contains 54 proposal rows. Player Compare treats all proposal rows as
manual-review-only and does not consume them as approved joins.

## Activated In Player Compare

The `/player-compare` page now includes an `NFLVerse Player Context` tab with
dense context in expanders:

- Identity / Join Transparency
- Recent Production / Activity Context
- Usage / Role Context
- Availability Timeline
- Roster-Window Context
- Schedule Context
- Dataset Freshness / Coverage Badges
- Deferred / Manual Review Items

Rows are joined by `nwr_player_id` only. Player-level context displays only when
`identity_join_status=SAFE_NOW_DISPLAY_ONLY`, `review_required=false`, and the
field is `SAFE_NOW_DISPLAY_ONLY` in the schema manifest with all model, source
truth, rank logic, hidden sort, trade value, and pick value flags set to false.

`NEED_IDENTITY_REVIEW` rows show only `Needs identity review` status. They do
not expose NFLVerse detail fields.

## Missing Data Rules

Missing values display as `Not enough information`. Missing data is not treated
as zero, no-role, healthy, clean, safe, bad, or confirmed UDFA.

## Current Schedule Context

- Next game / opponent / bye context is displayed only for rows that pass the
  same `SAFE_NOW_DISPLAY_ONLY`, `review_required=false`, and schema-manifest
  guardrails as the rest of the NFLVerse context.

## Deferred

- Identity proposals remain manual-review-only and are not approved joins.
- `ff_rankings` remains blocked by source policy and unused.

## Guardrail Verdict

No model score, hidden sort, player recommendation, market/ADP decision logic,
injury-risk score, medical projection, comeback projection, trade value, pick
value, rank mutation, source-truth promotion, or Live Draft / Mock Draft behavior
change was implemented.
