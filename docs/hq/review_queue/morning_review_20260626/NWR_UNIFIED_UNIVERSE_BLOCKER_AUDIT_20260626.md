# NWR Unified Universe Blocker Audit

Date: 2026-06-26

Verdict: GREEN

## Source Files

- `docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_consolidated_review.csv`
- `docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_remaining_blockers.csv`
- `docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_identity_triage.csv`

## Counts

- Consolidated review rows: 368
- Review-needed rows: 249
- Ready rows: 119
- App wiring allowed rows: 0
- Model input allowed rows: 0
- Remaining blocker rows: 271

Blocker type counts:

- `REVIEW_NEEDED_ROW`: 249
- `MISSING_AGE`: 16
- `MISSING_PLAYER_ID`: 5
- `AGE_CONFLICT_REVIEW_NEEDED`: 1

## Morning Queue

Created:

`docs/hq/review_queue/morning_review_20260626/unified_universe_blocker_review_queue_v1.csv`

Queue rows:

- P0 missing player_id rows: 5
- P1 player age gaps: 14
- P1 age conflict rows: 1
- Total P0/P1 queue rows: 20

Two missing-age DST rows are documented in the source blocker file but are not included in the P0/P1 morning queue because K/DST are hidden/excluded by default from player decision surfaces.

## Safe Defaults

- `model_input_allowed=no`
- `app_wiring_allowed=no`
- Do not fabricate player IDs.
- Do not fabricate ages.
- Missing age remains `Not enough information`.
- Unified Universe remains review-only until a later source-quality/app-wiring gate.

## Human Review Priorities

1. Resolve or leave blocked the five missing rookie/prospect player IDs.
2. Resolve or keep `Not enough information` for player age gaps.
3. Resolve Joshua Palmer display-age conflict if the row will ever be shown outside review pages.
4. Do not approve app wiring from this queue alone.

## Phase 3 Result

Phase 3 is GREEN. The blocker queue is actionable and does not mutate source artifacts, model input flags, or app-wiring flags.
