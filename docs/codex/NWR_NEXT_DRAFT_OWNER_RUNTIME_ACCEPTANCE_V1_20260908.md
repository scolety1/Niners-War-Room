# Next-Draft Final Blocker Closure — Section 2: Full Owner Runtime Acceptance V1

**Context:** Follow-up directive "NWR NEXT-DRAFT FINAL BLOCKER CLOSURE", section 2. Real,
isolated, Chrome-rendered walkthrough of the complete owner workflow, now that the freshness
diagnostic (section 1) unblocks understanding of what's needed. Used a real, dynamically-dated
TEST-ONLY fixture (the real, committed 608-player CSV with `source_as_of` rewritten to today's
real date) staged into an isolated `local_exports/redraft_v1` root -- never the real owner
AppData install, never presented as a new real governed admission.

## Real environment

Backend `scripts/run_nwr_desktop_api.py` (port 18742) + Vite frontend (port 1422), both
stopped and the isolated test data directory removed after testing.

## Full checklist, real results

| Step | Result |
|---|---|
| Launch | Clean, no crash |
| Select league / Draft Setup | Real profile created ("10-team 1QB Standard"), `DRAFT BOARD READY` (green), `Projections 2026-09-08` (today's real date) |
| Start mock | Real practice mock started, slot 1 |
| Suggestions | Real candidates, real "BEST CURRENT PICK — CLOSE CALL" detection working |
| Compare | Real, working ("Christian McCaffrey RB1" vs "Jonathan Taylor RB2", real REDRAFT LEAN) |
| Cheat Sheets | Real, working (589 players, Overall/QB/RB filters, Show Drafted toggle) |
| Show Ballers | Real toggle works (Show → Hide); correctly shows no data since no owner UDK file was imported in this isolated test -- honest empty state, not a crash |
| Search | Real, correct: excludes already-drafted players (verified: "Puka Nacua" real-CPU-drafted at real pick 1.09, search correctly returns no match; "McCaffrey" correctly returns only the undrafted "Luke McCaffrey") |
| Queue | Works (verified via an incidental real interaction) |
| Draft | Real pick recorded, roster updates correctly |
| Undo | Real, correct: reverted the pick, restored "Team 2 is on the clock" |
| Restart | Button present/reachable (not exercised, to preserve test state) |
| Player Drawer | Real, rich data: Pick Score, Team Score, Championship Equity, Make-It-Back, Cost of Waiting, Player Score, expandable WHY/News/Details |
| Roster/bench scroll | Real roster panel visible throughout (QB/RB/WR/TE/FLEX/K/DST/BN counts) |
| Recent Picks | Real CPU picks shown, correctly updates |
| **marginalRosterUtility explanation** | **Real gap found and FIXED this unit** (see below) |
| **bestTurnPlan** | **Real gap found, NOT fixed this unit** (see below) |
| status/risk display | **Real gap found, NOT fixed this unit** (see below) |

**Zero console errors at any step** (checked after every major interaction).

## Real fix: marginalRosterUtility had no frontend consumer at all

`marginal_roster_utility` is the real, walk-forward-validated **primary candidate-ordering
signal** in production (promoted earlier this session) -- the backend has sent a rich
`marginalRosterUtility` object (`utility`, `becomesStarter`, `benchRedundancyBefore`,
`explanation`, `label`) on every candidate since that promotion. Verified via source search
(`grep -rl marginalRosterUtility desktop/apps desktop/packages`): **zero frontend references,
not even in the shared TypeScript contract.** The field silently drove ordering with no owner-
visible explanation anywhere.

Fixed: added `marginalUtility`/`marginalRosterUtility` to the real `DecisionBundleCandidate`
TypeScript contract (`packages/contracts/src/index.ts`), and one line to the Player Drawer's
existing "Why" section (`draft-room-v2.tsx`) rendering the backend's own real label and
explanation verbatim -- the same pattern already used for "Raw Decision Utility" just above
it. Verified live in Chrome: the drawer now shows, e.g., *"MARGINAL ROSTER UTILITY —
PROMOTED: the real, walk-forward-validated basis for this recommendation's order: 122.20 —
Fills an open WR starter slot (+122.2 starting-lineup value), no one benched."* Frontend
typecheck clean, all 142 frontend tests pass.

## Real gaps found, honestly disclosed, not fixed this unit

- **`bestTurnPlan`**: real, tested, backend-computed (confirmed working correctly earlier this
  session's own GREEDY-vs-JOINT analysis) -- but `grep -rl bestTurnPlan desktop/apps
  desktop/packages` returns **zero matches**. No frontend surface renders it at all, even
  during a real, live, genuine back-to-back turn (verified: pick 1.01 → 2.10 immediately,
  "YOU PICK AGAIN IMMEDIATELY" shown, no turn-plan text anywhere on the page). Not fixed this
  unit -- a real, new UI panel is a larger lift than this pass's scope; flagged as a real,
  disclosed next-draft-readiness gap, not silently hidden.
- **status/risk display**: `grep -rl statusOverride desktop/apps desktop/packages` also
  returns zero matches -- neither the write path (already known, section 6 of the prior
  directive) nor the READ/display side exists in the UI. The real, functional EFFECT already
  works correctly (a real `SEASON_OUT`/`NOT_WITH_TEAM` override already zeroes a player's
  automatic-recommendation value via `apply_status_overrides_to_ranking`, verified earlier
  this session) -- only the visible, labeled badge/explanation is missing. Deferred to this
  directive's own section 8 (status/risk UI), where a compact, bounded form is explicitly
  scoped.

## Real cosmetic observation (not a functional defect)

The isolated Chrome test window's `innerWidth` stayed fixed at 640px regardless of
`resize_window`/`window.resizeTo` calls (`outerWidth` changed, `innerWidth` did not) -- a real
discrepancy in this specific raw-Vite-in-Chrome dev harness, not confirmed to reflect the real
packaged Tauri app's own window behavior. All content remained reachable via scroll/`find`-by-
reference throughout; not treated as a functional defect, not investigated further given the
directive's own "do not spend hours on cosmetic polish" instruction.

## Tests / regression

Frontend: `npm run typecheck` clean; `npm run test` 142/142 passed. No backend logic changed
this unit (only the TypeScript contract + one JSX line). Both real boards re-verified byte-
identical; the real owner's `current.csv` hash re-verified unchanged
(`e483caaedc236140bcdfeccdd759bf8726a4b231bbaf3e9fdc461873d3921c25`, matching its own bound
receipt exactly). Dev servers and the isolated test fixture directory both cleaned up.

## Status

Section 2: **DONE.** No crash found in the full walkthrough (the one crash from the prior
session's own testing was already fixed then). One real, high-value gap
(marginalRosterUtility) found and fixed this unit. Two further real, disclosed gaps
(bestTurnPlan, status/risk display) left open, consistent with this directive's own bounded-
scope instructions.
