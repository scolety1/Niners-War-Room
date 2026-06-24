# NWR Frozen Board Baseline Demotion - 20260623

## Verdict
GREEN.

## Decision
The 66-row `FINAL_DRAFT_BOARD_V1_FROZEN.csv` is no longer presented in the app as the draft-day source of truth or full draftable-player universe.

It remains a protected **Frozen Baseline / checkpoint**:

- preserve `final_board_rank` for reference;
- preserve the frozen CSV unchanged;
- use the frozen rows as baseline context in tables;
- use the expanded draftable pool and runtime draft state for on-clock availability.

## Why
The frozen 66-row artifact was created from a pinned rookie/prospect plus dropped-veteran checkpoint. It is structurally useful, but it is not the complete draftable league universe after verified free-agent overlays and runtime draft events.

## App Contract
- `Final Board Rank` remains visible as a frozen baseline rank.
- `Frozen Baseline` replaces `Source of truth` in source badges.
- Unified player-board source coverage now says `Frozen Baseline only` or `Full Dynasty source + Frozen Baseline`.
- Live Draft Room copy says the active table is the expanded draftable pool, not the frozen board alone.
- PDF/free-agent overlays remain draftable display/runtime overlays and do not mutate the frozen CSV.

## Guardrails
- No Frozen Final Draft Board V1 mutation.
- No `final_board_rank` change.
- No Dynasty Rank overwrite.
- No model/value/ranking logic change.
- No latest candidate/latest approved update.
- No pinned snapshot mutation.
- No `C:\NWR_SHARED_DATA` tracking.

## Remaining Work
Future source-accountability lanes should define the durable line of truth as an active draftable-player pool contract, likely combining Sleeper league/free-agent truth, verified PDF fallback, full dynasty/NWR player source, and runtime draft events.
