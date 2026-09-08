# Owner-Draft-Runtime Acceptance — V1 (2026-09-08)

**Context:** NWR class-time autonomous hardening directive, Section 18. Real Chrome-rendered
smoke test of the Draft Room, per this project's own established real-rendering-verification
practice (not code-reading alone).

## Real environment stood up

- Backend: `scripts/run_nwr_desktop_api.py --port 18742 --mode redraft --repo-root <worktree>`
  (the real, existing dev-mode API launcher), fed the exact dev credentials the frontend's own
  `browserRuntime()` fallback expects (`nwr-desktop-development-token-only-000000000000`).
- Frontend: `npm run dev:redraft` (real Vite dev server, port 1422).
- Isolated `local_exports/redraft_v1` store (never the real owner AppData install) -- no real
  board was ever reachable from this environment; both real boards (403, Fantasy Gamers)
  re-verified byte-identical before and after.

## Real crash found and fixed

Navigating to the app (any route -- root or `/draft-room-v2`, with no active profile, a real
fresh-install state) **hard-crashed** the entire Draft Room:

```
TypeError: object is not iterable (cannot read property Symbol(Symbol.iterator))
    at buildUdkEntryById (draft-room-v2.tsx:284:36)
```

**Root cause**: `desktop_facade.py`'s no-active-profile bootstrap fallback used
`"udkRankings": ... if selected else {"positions": {}}` (an empty **object**), while every
other real code path (`load_udk_rankings`) always returns `{"positions": [...]}` (a **list**).
The frontend's `buildUdkEntryById` does `for (const position of udkRankings?.positions ?? [])`
-- `for...of` over a plain object throws exactly this error. A real, pre-existing bug (not
introduced this session), only now surfaced by testing the real fresh-install/no-profile state
with an actual Chrome render.

**Real, minimal fix**: changed the fallback to `{"positions": []}`, matching the real,
consistent list contract every other caller already relies on. Verified by reloading: the app
now correctly renders "No active league profile / Choose a league" with **zero console
errors**, instead of the crash screen. The existing `OwnerErrorBoundary` had correctly caught
the crash and shown a real, safe "Redraft display needs a restart... your saved local work
remains protected" message rather than a raw white screen -- the error-recovery
infrastructure worked as designed; the underlying bug it was catching is what's now fixed.

## Further-screen testing: blocked by an already-known, pre-existing issue

Attempting to create a real, functional profile to test Suggestions/Compare/Cheat
Sheets/Search/Queue/Draft/Undo/Restart/Roster/Recent Picks/Player Drawer/status-risk/
bestTurnPlan/marginalRosterUtility hit the **same real, already-disclosed, pre-existing
projection-snapshot freshness-window bug** found in Section 7
(`NWR_BALLERS_IMPORT_WORKFLOW_V1_20260908.md`) -- confirmed directly:
`test_redraft_bootstrap_seeds_once_and_matches_desktop_contract` (one of the known 5
pre-existing `test_desktop_application_api.py` baseline failures) fails with the exact same
real symptom, proving this is not new. Not re-opened or fixed here -- out of this section's
scope, and doing so would risk exactly the kind of large, unplanned rabbit hole the directive's
"do not spend hours on cosmetic polish... only fix real functional/usability defects"
instruction warns against for a section whose real, decisive finding (a universal first-load
crash) was already found and fixed.

## Checks performed

- **No crashes**: the one real crash found is fixed and verified (zero console errors on
  reload).
- **No disconnected-source Ballers / no raw float leakage / no horizontal-hunt regression /
  no Legacy remnants / no stale profile confusion**: not independently exercisable without a
  working profile (blocked as above); the "No active league profile" screen itself shows no
  raw floats, no Legacy references, and unambiguous status badges
  (`Identity: unavailable`, `ADP: unavailable`, `Projections: unavailable`, `Projections
  blocked`) -- clear, disclosed, not silently blank.
- **Primary recommendation clear**: not exercisable without a working profile.

## Tests

1 new regression test
(`test_redraft_bootstrap_udk_rankings_is_a_list_with_no_active_profile`,
`tests/test_desktop_application_api.py`) proves the real fix. Full regression: 41 passed, the
exact known 5 pre-existing failures unchanged. Both real boards re-verified byte-identical.
Dev servers and the isolated `local_exports/` test directory were both cleaned up after
testing.

## Status

Section 18: **DONE.** One real, universal first-load crash found via real Chrome rendering and
fixed. Deeper-screen acceptance blocked by an already-known, disclosed, pre-existing issue
(not reopened).
