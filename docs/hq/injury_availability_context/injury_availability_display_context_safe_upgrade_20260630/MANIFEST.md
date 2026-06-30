# Injury Availability Display Context Safe Upgrade Manifest

Date: 2026-06-30

Lane: `work/lane-injury-availability-upgrade-20260630`

Worktree: `C:\NWR\Niners-War-Room-lane-injury-availability-upgrade-20260630`

Base checked after fetch:

`e598249a2a9915366fc2087991bb0519be7c8403`

## Verdict

`YELLOW_PARTIAL_AVAILABILITY_CONTEXT_GATED`

This rerun activates safe direct display of tracked NFLVerse player availability
context where the merged artifact and schema allow it.

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
- Add safe tracked-artifact service/schema/docs/tests for availability display context.
- Add Player Compare display rows for safe NFLVerse identity rows.
- Keep missing injury or availability context as `Not enough information`.
- Explain season-total report-week counts versus future per-game denominators.

Not activated:

- `weekly_rosters`, `rosters`, `schedules`, `snap_counts`, and `player_stats`
  denominator computations.
- Dynamic season-anchor computation.
- Any model, rank, trade, pick, source-truth, or hidden-sort use.
