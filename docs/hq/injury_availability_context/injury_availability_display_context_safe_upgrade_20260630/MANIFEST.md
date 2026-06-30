# Injury Availability Display Context Safe Upgrade Manifest

Date: 2026-06-30

Lane: `work/lane-injury-availability-upgrade-20260630`

Worktree: `C:\NWR\Niners-War-Room-lane-injury-availability-upgrade-20260630`

Base checked after fetch:

`e598249a2a9915366fc2087991bb0519be7c8403`

## Verdict

`YELLOW_WAITING_FOR_NFLVERSE_REFRESH_HEALTH_GREEN`

This lane adds safe display-context prep for injury and availability transparency. It
does not activate refreshed NFLVerse roster, schedule, snap, stat, or dynamic-anchor
computations because the current completion gate still lists `nflverse pull/status`
as `YELLOW`.

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

## Code Artifacts

- `src/services/injury_availability_context_service.py`
- `tests/test_injury_availability_context_service.py`

## Scope Confirmation

Allowed and completed:

- Preserve existing factual `nflreadpy.load_injuries` review-only context.
- Add safe service/schema/docs/tests for future availability denominator context.
- Keep missing injury or availability context as `Not enough information`.
- Explain season-total report-week counts versus future per-game denominators.

Not activated:

- `weekly_rosters`, `rosters`, `schedules`, `snap_counts`, and `player_stats`
  availability computations.
- Dynamic season-anchor computation.
- Any model, rank, trade, pick, source-truth, or hidden-sort use.
