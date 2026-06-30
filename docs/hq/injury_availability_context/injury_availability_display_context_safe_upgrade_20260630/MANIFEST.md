# Injury Availability Display Context Safe Upgrade Manifest

Date: 2026-06-30

Lane: `work/lane-injury-availability-denominator-followup-20260630`

Worktree: `C:\NWR\Niners-War-Room-lane-injury-availability-denominator-followup-20260630`

Base checked after fetch:

`13dc684d5173f20230708126b6b82d121cbc3ed0`

## Verdict

`GREEN_AVAILABILITY_DENOMINATOR_DISPLAY_READY`

This follow-up activates safe display-only denominator fields from the merged
Data Hygiene denominator artifact while preserving identity, schedule, model,
rank, and source-truth guardrails.

## Tracked Artifacts Consumed

- `docs/hq/data_sources/nflverse_player_context_display_20260630/`
- `docs/hq/data_sources/nflverse_availability_denominator_display_v1_20260630/`
- `docs/hq/data_sources/nflverse_schedule_context_display_gate_v1_20260630/`
- `docs/hq/data_sources/nflverse_player_context_identity_approval_v1_20260630/`

## Files In This Packet

- `MANIFEST.md`
- `DEEP_RESEARCH_PROPOSAL_CLASSIFICATION.md`
- `INJURY_AVAILABILITY_SOURCE_GATE.md`
- `NFLVERSE_INJURY_AVAILABILITY_DATASET_COVERAGE.csv`
- `DISPLAY_CONTEXT_SCHEMA.md`
- `UI_COPY_AND_GUARDRAILS.md`
- `MODEL_RANK_SOURCE_TRUTH_NON_MUTATION_REPORT.md`
- `TEST_RESULTS.md`
- `FINAL_VERDICT.md`
- `nflverse_availability_context_activation_summary.md`
- `nflverse_availability_field_map.csv`
- `nflverse_availability_guardrail_audit.md`

## Code Artifacts

- `src/services/injury_availability_context_service.py`
- `tests/test_injury_availability_context_service.py`

## Scope Confirmation

Allowed and completed:

- Preserve existing factual `nflreadpy.load_injuries` review-only context.
- Consume tracked NFLVerse player context and denominator artifacts.
- Add Player Compare display rows for safe denominator fields.
- Keep missing injury or availability context as `Not enough information`.
- Explain season-total report-week counts versus per-game denominators.

Still not activated:

- `games_missed_while_rostered`.
- Identity-review or identity-recommendation rows as approved joins.
- Schedule-derived health or availability inference.
- Any model, rank, trade, pick, source-truth, recommendation, or hidden-sort use.
