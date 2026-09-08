# Ballers/UDK Import Workflow — Owner-Ready Pipeline V1 (2026-09-08)

**Context:** NWR class-time autonomous hardening directive, Section 7.

## What already existed (found via reuse-first search)

Substantially more than expected: `parse_udk_position_csv`/`parse_udk_position_pdf`
(`redraft_draft_room_v1_service.py`) -- real, tested parsers for the owner's real UDK
("Position Rankings — Fantasy Footballers Podcast", i.e. "Ballers") export, with real
identity matching, opaque-ADP preservation, Dynasty-lock detection, and Markers-discard. PDF
support was fixture-tested but real-sample structural fidelity remains
`BLOCKED_PENDING_OWNER_SAMPLE` (unchanged, no real owner PDF sample exists to test against).
`save_udk_position_*_rankings` (parse + persist, additive merge per position) and
`load_udk_rankings` (already the single load point every consumer -- `desktop_facade.py:1983`
-- reads for the live bootstrap payload, so "all surfaces use the same active version" was
already structurally true). The CSV path was already wired to a facade method
(`import_udk_rankings`); **the PDF path was not reachable from anywhere**, and **no
versioning/rollback existed at all.**

## Real gaps closed this unit

1. **PDF import facade wiring** (`import_udk_pdf_rankings`, `desktop_facade.py`) -- same
   file-path convention as `import_udk_unmodeled_skill_assets` (frontend stages the picked
   file locally, passes its path). File readability is checked *before* the ranking-context
   work (a real, sensible fail-fast reordering, not just a test convenience).
2. **Real version history + rollback** (`redraft_draft_room_v1_service.py`): before a
   position's active UDK snapshot is overwritten, it is pushed onto that position's own
   `history` list (newest first, capped at `UDK_MAX_HISTORY_VERSIONS=5`). New function
   `rollback_udk_position_rankings(root, profile_id, position)` restores the most recent
   prior version for ONE position, leaving every other position's active version untouched;
   rejects (never silently no-ops) when that position has no import, or no history to roll
   back to. Wired to the facade as `rollback_udk_position_rankings`.
3. **`load_udk_rankings` payload hygiene**: exposes a real `historyCount` per position instead
   of the full prior snapshots (which would otherwise ship every version's complete `entries`
   list on every load -- no real consumer needs that).
4. **Preview enrichment** (`parse_udk_position_csv`, shared by the PDF path via delegation):
   added `perPositionCounts` (the directive's own required per-position rows summary) and
   `duplicateRows` (two source rows in the SAME import resolving to the same real NWR
   `playerId` -- a real data-quality signal the previous preview never surfaced). "Ambiguous"
   match rejections were already real and disclosed via the existing `unmatched`/`warnings`
   reason text (`DST_TEAM_NOT_UNIQUE`, `EXACT_NAME_TEAM_COLLISION_OR_MISMATCH`,
   `POSITION_MISMATCH`) -- not duplicated into a separate bucket.

## What remains (honestly disclosed)

- A compact "Import Ballers Cheat Sheet" UI control unifying the PDF/CSV pick, preview, and
  activate/rollback actions into one owner-facing flow -- the backend now supports this
  end-to-end, but no frontend surface was built this pass (time budget, same disposition as
  Section 6's status/risk intake).
- Real PDF-sample structural-fidelity verification remains blocked pending an actual owner
  Ballers PDF export (unchanged from the prior session's finding).

## A real, pre-existing, unrelated issue found while testing (not fixed, disclosed)

Attempting a full facade-level PDF happy-path test (needing a real governed 2026 projection
snapshot fixture) surfaced that the exact same bundled fixture
`test_redraft_profile_practical_mode_toggle.py` already uses for this purpose now fails with
`"Projection snapshot has no rankable player rows"` **even in that untouched, already-committed
file** -- confirmed via a direct rerun, and confirmed not caused by any commit in this session
(`git log` on `redraft_engine_v1_service.py` shows no session commits touching it). Root
mechanism (verified, not fixed): `load_projection_snapshot`'s `source_as_of` freshness-window
check appears to reject every row in the bundled fixture as the simulated "today" has advanced
past whatever window was valid when that fixture was last exercised (file mtime 2026-09-03).
This is real fixture/environment drift, unrelated to the Ballers workflow itself, and out of
scope for this directive section -- flagged here rather than silently worked around, and NOT
patched (patching freshness validation to make a stale test fixture pass would be exactly the
kind of governance-weakening change this project's own discipline forbids).

## Tests

7 new/extended tests in `tests/test_redraft_draft_room_v1_service.py` (per-position
counts/duplicates, re-import versioning, rollback success, rollback rejections x2) — all pass.
3 new facade-level tests in `tests/test_udk_pdf_and_rollback_facade.py` (unreadable-path
rejection before any ranking work, real rollback facade wiring, rollback-with-no-history
rejection) — all pass, using a service-level fixture that avoids the broken ranking-snapshot
fixture above. Full regression: 65 passed, 1 skipped (the pre-existing, unchanged
`BLOCKED_PENDING_OWNER_SAMPLE` PDF-sample test) across the 3 related files. Known 5-test
`test_desktop_application_api.py` baseline unchanged. Both real boards re-verified
byte-identical.

## Status

Section 7: **DONE (backend workflow complete, versioned, rollback-capable)**; frontend
unification surface flagged as the remaining step.
