# Draft Readiness Gate

`GREEN_NWR_ROOKIE_DRAFT_CLASS_COMPLETE_WITH_MANUAL_REVIEW_ASSETS`

The gate loads all official drafted QB/RB/WR/TE rows, verifies unique picks and stable
asset IDs, then independently reconciles the IDs that survive Registry, Detail,
Search, shared selection, Compare, Trade, Rookie Board, and Draft Cockpit composition.
It reports exact per-surface exception lists and rejects duplicate surface IDs.

- Official: 80
- QB/RB/WR/TE: 10 / 12 / 36 / 22
- Scored: 73
- Manual review: 7
- Unresolved: 0
- Missing registry: 0
- Missing draftable: 0
- Duplicate stable IDs: 0
- Validated surfaces: compare, detail, draft_cockpit, draftable, registry, rookie_board, search, selectable, trade
- Surface gaps: none

Any official asset silently absent or nonselectable makes the release unsafe. A visible,
selectable manual-review asset does not fail readiness merely because it is unscored.
