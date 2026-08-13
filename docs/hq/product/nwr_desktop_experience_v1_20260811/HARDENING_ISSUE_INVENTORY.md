# NWR Desktop V1 - Hardening Issue Inventory

This inventory records owner-visible findings from the first runnable Dynasty and Redraft native
candidates. Analytical rankings, projections, Outcome V3 values, Rookie Review values, market
values, and decision rules are frozen throughout this work. Status is not considered closed until
the focused test and native replay both pass.

## Priority definitions

- P0: crash, corruption, or unusable core workflow.
- P1: major owner workflow, trust, privacy, or release defect.
- P2: confusing, slow, inaccessible, or materially annoying behavior.
- P3: polish that does not block useful owner work.

## Current release gates

| ID | Priority | App / screen | Owner action | Expected | Observed first candidate | Reproducibility | Status |
|---|---|---|---|---|---|---|---|
| PKG-01 | P1 | Both installers | Install either product | Only immutable, mode-required governed resources ship | First candidate bundled broad trees | Every candidate package | Closed: exact 10-file Dynasty / 3-file Redraft allowlists; denylist and extracted-package audit pass |
| DYN-01 | P1 | Compare | Run a comparison, then change an asset | Old result disappears and an in-flight response cannot overwrite new inputs | First candidate retained previous result | Deterministic; race with delayed response | Closed: result invalidation and request serialization verified |
| DYN-02 | P1 | Trade | Evaluate, then edit either side or team window | Old decision clears; exact asset cannot appear on both sides | First candidate retained a ghost decision | Deterministic | Closed: stale clearing and cross-side exclusion verified |
| DYN-03 | P1 | Trade | Save, reopen, and export the known owner trade | Atomic local save/reopen and source-consistent export are available | First candidate exposed evaluate only | Every run | Closed: exact owner case save/reopen/export replay passed |
| DYN-04 | P1 | Planning | Edit one module, save another | Unsaved work in other modules remains intact | First candidate replaced local drafts | Deterministic | Closed: merge-only save and locked navigation tested |
| ALL-01 | P1 | Global search | Find veteran, rookie, blocked prospect, future pick, and lower Redraft rank | Every existing governed asset is searchable by exact ID-backed result | First candidate used truncated indexes | Every run | Closed: full governed indexes; Puka, 2027 1st, De'Zhaun, and Redraft #578 replayed |
| ALL-02 | P1 | Data refresh | Reload after a bounded backend failure | Stale data is labeled and Retry is obvious | First candidate hid the failure | Deterministic | Closed: visible stale banner/retry and startup failure surface |
| ALL-03 | P1 | Rankings / Market | Sort numeric columns and reset composed filters | Stable numeric sort; missing values last both directions; accessible headers; reset | First candidate headers were display-only | Every run | Closed: stable missing-last sort, aria-sort, team filters, reset |
| ALL-04 | P1 | Native window | Snap or use common 125/150 percent scaling | Compact layout remains usable | First candidate minimum was 1100×720 | Every constrained display | Closed: minimum 720×560; seven-size matrix has no document overflow |
| API-01 | P1 | Both apps | Receive malformed/null contract payload | Owner-friendly failure with a technical diagnostic, never blank/undefined | First candidate lacked bootstrap guards | Deterministic with malformed fixture | Closed: mode-specific guards, tests, and top-level error boundaries |
| DYN-05 | P1 | Team tools | Use personal board, roster/picks, scenarios, and decision tracking | Existing local services are reachable through understandable desktop workflows | First candidate exposed only Planning | Every run | Closed for V1: My Board, Decision Tracker, future-pick assets, scenarios, backup/check-restore, and read-only Draft Cockpit |
| RED-01 | P1 | Profile & Scoring | Duplicate profile and edit scoring | Existing validated/atomic Redraft profile services are available | First candidate allowed create/activate only | Every run | Closed: duplicate/edit/activate and restart persistence verified |
| RED-02 | P1 | Cheat Sheet | Open/export profile-specific cheat sheet | Current governed ranking DTO is available in a print/export surface | First candidate lacked route | Every run | Closed: profile-specific 608-player route and CSV export |
| STATE-01 | P1 | Dynasty persistence | Adopt Desktop while retaining established Streamlit workspace | Explicit, create-only migration/backup path prevents silent divergence | First candidate had no adoption path | Every existing workspace | Closed: confirmed checksum-validated import refuses non-empty destination and never mutates source |

## Verified strengths from the first candidate

- No P0 was reproduced in the first native Dynasty/Redraft launch and navigation pass.
- The products have distinct executable identities, titles, navigation, accent treatment, and
  mode-scoped LocalAppData roots.
- The known owner trade resolves all seven exact governed assets and the existing evaluator returns
  `COUNTER`, `Your current side`, and `MEDIUM`; the gap is workflow/persistence presentation, not a
  requested change to trade rules.
- Dynasty Home renders the accepted 240-player Finished V1 board.
- Redraft first-run evidence keeps the two conflicted rookies visible as blocked without ranking
  them.
- Sticky table headers, visible focus, reduced-motion support, command-palette arrow/Enter handling,
  and serialized Redraft draft mutations are present.
- The Rust host uses loopback-only ephemeral listeners, launch-bound startup proof, exact
  process/job/image verification, and mode-scoped state.

## P2 / annoyance queue

| ID | App / screen | Finding | Planned disposition |
|---|---|---|---|
| UX-01 | Dynasty Player Detail | Personal context link was absent | Closed: direct My Board context link added; rank authority unchanged |
| UX-02 | Rookie Review | Rows did not open exact-ID detail | Closed: exact-ID detail navigation; blocked decision actions remain disabled |
| UX-03 | Redraft Draft Room | `recoveredFromBackup` was not announced | Closed: owner-language recovery notice added |
| UX-04 | Both shells | Some normal pages exposed developer words | Closed for primary routes: owner copy translator and simplified badges/labels applied |
| UX-05 | Command palette | Initial dialog lacked complete keyboard behavior | Closed: arrow/Enter, Escape, focus containment/restoration, and 720p palette layout tested |
| UX-06 | Long boards | Initial routes rendered every row by default | Closed for V1: bounded selectable depths, sticky context, full access, measured no horizontal overflow |

## Owner acceptance replays required before release

1. Player research: veteran, rookie, blocked prospect, and future pick through Ctrl+K and direct
   detail, with back/state preservation.
2. Rankings: repeated numeric sorts, composed position/team/search filters, reset, missing values,
   sticky headers, and exact player navigation.
3. Compare: veteran/veteran, rookie/veteran, rookie/rookie, with stale-response rejection.
4. Trade: exact known seven-asset case, team-window change, duplicate prevention, save, reopen, and
   export.
5. Rookie Review: Carnell Tate, KC Concepcion, and De'Zhaun Stribling status clarity.
6. Team tools: personal context, roster/pick planning, keeper/drop/deadline planning, scenario, and
   decision tracking.
7. Redraft: create, duplicate, edit scoring, activate, rankings, compare, cheat sheet, draft/undo,
   concurrent Dynasty isolation, close, and restart.
8. Packaging: fresh extraction from a path containing spaces, exact allowlist, owner-state denylist,
   no Python source, correct icons/names, offline launch, and no checkout-path dependency.
9. Lifecycle: repeated concurrent launch/close, abnormal host termination, bounded backend failure,
   no orphan/listener, and unrelated Python processes untouched.
10. Visual/desktop: 1280 x 720 through 2560 x 1440 where feasible, half-screen snap, 100/125/150
    percent scaling, keyboard-only command palette, and visible focus.
