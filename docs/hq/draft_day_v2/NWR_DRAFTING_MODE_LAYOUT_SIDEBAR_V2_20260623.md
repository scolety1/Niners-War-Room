# NWR Drafting Mode Layout / Your Team Sidebar V2 - 2026-06-23

## Verdict

GREEN for Phase 3 implementation.

Drafting Mode now has a more useful left-side Your Team runtime panel without mutating any roster, rank, source-truth, pinned, or frozen-board artifact.

## What Changed

- The Your Team sidebar now shows compact runtime summaries for:
  - live picks recorded,
  - trade events recorded,
  - last autosave timestamp,
  - owned current picks after local trade events,
  - drafted players from local runtime state,
  - future picks mentioned in trade events.
- Sidebar expanders now expose:
  - current owned picks,
  - drafted players,
  - future picks,
  - trades made during draft,
  - runtime status and source paths.
- Drafting Mode top entry paths are clearer:
  - `/live-draft-room`
  - `/mock-draft`
  - `/cheat-sheets`
- The page keeps Drafting Mode tabs focused:
  - Cheat Sheets,
  - Draft Board,
  - Trade Lab,
  - Player Compare,
  - Search,
  - Settings / Data Health.

## Proof Scenario

Using local-only runtime state under `C:\NWR_SHARED_DATA\draft_day_runtime\v2_phase_1_3_acceptance_20260623`:

- A live pick assignment for Jameson Williams at `1.01` appears in the Your Team sidebar.
- A trade event where NWR sends `1.04` and receives `2.03 + 2028 1st` appears in sidebar trade/future-pick context.
- Owned current picks reflect local trade-event ownership updates.

## Guardrails

- No source-truth mutation.
- No frozen board mutation.
- No rank/model/value logic change.
- No latest candidate or latest approved update.
- Runtime data remains local-only under `C:\NWR_SHARED_DATA\draft_day_runtime\`.
- Current NWR roster remains `Not enough information` because no approved roster source was wired in this UI pass.

## Remaining Caveats

- This sidebar is a runtime draft cockpit, not a full roster-management screen.
- A future lane can wire an approved current roster source if one is provided and validated.
