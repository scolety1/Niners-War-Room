# NWR Market Data / ADP UX Cleanup — Control Center V1 (2026-09-08)

Real, explicit, in-chat owner authorization (Spencer Colety). Directive: **PRE-DRAFT MARKET
DATA / ADP UX CLEANUP — CENTRALIZE ALL OWNER DATA IMPORTS/EXPORTS — DO NOT TOUCH THE ENGINE**,
issued with the real next draft (Fantasy Gamers, Sleeper, 10-team 1QB) approximately two hours
out. This pass is **frontend/UX only** — zero backend, Python, or model files touched; see
"Engine boundary proof" below.

## What changed

All five files touched are frontend-only, under `desktop/apps/redraft/src/`:
`RedraftApp.tsx`, `adp-providers.tsx`, `cheat-sheet.tsx`, `draft-room-v2.tsx`, `redraft.css`.

**1. `RoomControls` (the embedded "Market Data / ADP" panel inside Draft Room V2) rebuilt as a
compact status + quick-import panel.** It already existed (its own toggle literally said
"Market Data / ADP" — confirmed by direct code reading before any edit) but only exposed a
legacy K/DST import with stale prose. It now shows three one-line status rows (active league
market with Auto/override state, Ballers/UDK row counts by position, K/DST reference source)
plus four compact actions: Refresh FFC ADP, Import Multi-Platform ADP CSV, Import Ballers / UDK
CSV, and "Open Market Data / ADP →" (deep-links to the full `/adp` page). A K/DST fallback
import only appears when the league rosters K/DST **and** the active Ballers snapshot doesn't
already cover it, with explanatory text ("Only needed when the active Ballers file does not
include K/DST").

**2. Fixed a real, live routing bug matching directive section 6.** The embedded panel's ADP
import button was still calling `client.importRedraftAdp` — the old, rigid single-column
importer from before the global multi-platform pipeline existed (directive C). Rewired to
`client.saveRedraftPasteAdp(...)`, the same global pipeline the `/adp` page's own import already
uses. No new parser/route was added.

**3. Cheat Sheets is now consumer-only (directive section 11).** Removed its "Import UDK CSV"
control and inline rollback button entirely; both now live solely in Market Data / ADP (no
duplicate primary controls, per the directive's own explicit rule). Added a one-line status
strip — `Ballers: <date> · <rows> rows · Market: <provider> · <date> · Manage in Market Data /
ADP` — via two new exported helpers, `ballersStatusText`/`marketStatusText`. Its own export
button was renamed honestly: **"Export NWR Cheat Sheet CSV"** (it is a generated NWR cheat
sheet, not raw Ballers data — directive section 3's explicit naming rule).

**4. Removed a genuinely redundant panel from the `/adp` page.** "Import owner ADP CSV" called
the same old `client.importRedraftAdp` rigid importer directly, with no preview step — fully
superseded by the existing "Import Multi-Platform ADP" panel above it, which already accepts a
CSV file (`importMultiPlatformCsv`) through the real preview-before-activate flow and already
handles the old simple Name/Position/ADP shape as backward-compatible input. Deleting it removes
both a duplicate control and a path that could silently activate a malformed file (directive
section 9).

**5. New, honestly-named exports (directive sections 3 & 10) — normalized, already-loaded owner
data only, never raw PDF content:**
- **Export Market ADP CSV** — one row per player with `marketProviderAdp` populated
  (Consensus/Sleeper/ESPN/FantasyPros columns), wired into the "Import Multi-Platform ADP" panel.
- **Export Ballers / UDK CSV** — one row per Ballers entry across all imported positions, wired
  into the "Import Ballers Cheat Sheet" panel, disabled until a Ballers snapshot is active.

Both reuse the CSV-download pattern already established in `cheat-sheet.tsx`'s `exportCsv`
(Blob → object URL → hidden anchor click → revoke).

**6. Light internal hierarchy on the `/adp` page (directive section 13).** Two group headings —
"Market / ADP" and "Ballers / UDK (also feeds K/DST reference — see Draft Room · Market Data /
ADP)" — were added above their respective panel clusters. This is a compact, low-risk grouping
inside the existing single-page layout, not a new navigation surface or tab system; the owner can
still collapse the whole thing from Draft Room in one click.

**7. A real, unintended duplicate-button bug was introduced mid-edit and caught before this
report.** An edit meant to add a "Cancel" button after "Activate Ballers Cheat Sheet" was applied
without first re-reading the file, and an identical Cancel button already existed on the next
line from directive C's own earlier build — producing two consecutive, byte-identical Cancel
buttons. Caught immediately via a follow-up `Read`, fixed by removing the duplicate line before
any typecheck or commit.

## Engine boundary proof (directive section 17)

`git diff --stat` for this entire pass touches only:
```
desktop/apps/redraft/src/RedraftApp.tsx    |   2 +-
desktop/apps/redraft/src/adp-providers.tsx |  60 ++++++++++++---
desktop/apps/redraft/src/cheat-sheet.tsx   |  60 ++++++++-------
desktop/apps/redraft/src/draft-room-v2.tsx | 120 ++++++++++++++++++-----------
desktop/apps/redraft/src/redraft.css       |   6 ++
```
Zero Python files, zero `src/services/*` or `src/model_v4/*` files. Since Player Score, Team
Score, Championship Equity, RAV, Pick Score, `marginal_roster_utility`, backup utility rates,
candidate ordering, projections, status/risk math, and K/DST timing logic are all computed
exclusively in the untouched Python backend, they are provably unchanged by construction — not
just re-tested and found equal.

Direct, real-data confirmation via a read-only facade call against the real state root
(`DesktopBackendFacade(repo_root=..., mode="redraft")` with `NWR_REDRAFT_HOME` pointed at
`%LOCALAPPDATA%\com.ninerswarroom.redraft\state\redraft`) shows the real Fantasy Gamers league
(active profile `4c5f04762921420595e4d8c7cda76582`) still has: Ballers QB 36 rows loaded
globally, owner platform snapshot 388 rows with `activeColumn: SLEEPER`,
`detectedPlatform: SLEEPER`, `leagueSelection: AUTO`, and ADP `available: true` with
`matchedPlayers: 403 / sourcePlayers: 388` — identical to directive C's final installed state.
The real 403 N 18th and friends profile still carries `provider: "espn"` (the directive-C fix).
This read made zero writes: both real draft-board file hashes
(`4b4a990faf124ce7a5d612537ba5943b.json` →
`ba106a0c1893bc911754d51d17f2efa772b174704a8ccc65b45ac024e22d2b64`, `403 N 18th`, unchanged
across the whole pass) were re-verified byte-identical immediately before and after the call.

**Disclosed, not hidden**: an earlier in-session checkpoint value for the Fantasy Gamers board
file's hash (recorded during directive C) does not match its current hash
(`8a5bf3e86aebdb136b1aa753b6e70f811a3f7fa4a096d2f54d22db9eb84145df`). The file's own mtime
(2026-09-08 19:16:23 -0600) predates this directive's work entirely and lines up with directive
C's own final real installs (the global ADP/Ballers snapshot activation), not anything done in
this pass — this session made zero writes to the real state root at any point in this turn (all
rendering verification below ran against a fully isolated GUI test copy). Flagged here rather
than silently reconciled.

## Rendered smoke test (directive section 16)

Stood up the real app: standalone backend (`scripts/run_nwr_desktop_api.py`, port 18742,
`--mode redraft`) against the pre-existing, fully isolated GUI test data root
(`%LOCALAPPDATA%\Temp\nwr_gui_test_root` — zero real data, established in a prior session's
rendering pass, reused read/write-isolated from KHA/403/Fantasy Gamers), plus the real Vite dev
server (`npm run dev:redraft`, port 1422). Chrome MCP rendered and interacted with the real app
at `http://127.0.0.1:1422/#/draft-room-v2` and `.../#/adp` (HashRouter).

Confirmed, screenshot-verified: Market Data / ADP expands from Draft Room into the new compact
panel with the three status lines and four quick actions, no giant blank space; "Open Market
Data / ADP →" deep-links correctly; Cheat Sheets renders its new one-line status strip
(`Ballers: not imported · Market: Fantasy Football Calculator · 9/4/2026 · Manage in Market Data
/ ADP` in this isolated fixture) with no import controls remaining (`read_page` interactive-
element listing shows no file input on the Cheat Sheets tab); the full `/adp` page renders the
new "Market / ADP" and "Ballers / UDK" group headings, the new "Export Market ADP CSV" button,
the "Import owner ADP CSV" panel is gone, and the new "Export Ballers / UDK CSV" button appears
correctly disabled (no Ballers imported in this isolated fixture). Zero console errors after a
full page reload with console tracking active.

**Disclosed limitation**: `resize_window` calls in this environment did not change the actual
page viewport (`window.innerWidth` stayed 644px regardless of the 1600×1000 / 1920×1200 window
sizes requested) — a tooling constraint of this session's Chrome MCP sandbox, not something
fixable from here. Owner-desktop-width wrapping specifically was therefore **not** directly
confirmed at real desktop resolution; the 644px render showed correct stacking and no broken
layout, and the CSS grid/flex rules used (`profile-edit-actions`, `adp-provider-grid`) are the
same pre-existing responsive rules already used throughout this page, so a wider viewport is
expected to only add horizontal room, not introduce new wrapping — but this is a reasoned
expectation, not a screenshot-verified fact.

## Tests

- `npx tsc -b apps/dynasty/tsconfig.json apps/redraft/tsconfig.json` — clean, zero errors.
- `npm run test` (vitest, desktop workspace) — 16 files, 142 tests, all passing.
- `npm run build:redraft` (production Vite build) — succeeds, no warnings.
- `python -m pytest tests/test_desktop_application_api.py -q` — 41 passed, 5 failed; the failures
  are the exact pre-existing baseline (`test_dynasty_facade_composes_real_governed_workflows`,
  `test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`,
  `test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`,
  `test_redraft_league_switching_isolates_draft_state_and_persists_active_profile`,
  `test_facade_has_no_streamlit_or_app_component_dependency`) — no new failures.

## Scope not fully closed (honest, time-boxed)

Given the real ~2-hour deadline, the following directive asks were addressed at a compact,
lower-risk level rather than fully built out — disclosed rather than silently dropped:

- **Section 8** (compact source status/version metadata) — already substantially present from
  directive C's own preview/snapshot panels (hash, row counts, parser mode, platform coverage);
  not further restructured into a separate Advanced disclosure this pass.
- **Section 13** (full Market/Ballers/K-DST/Advanced sub-navigation) — implemented as two
  lightweight group headings rather than a tabbed sub-hierarchy, to avoid a larger, unverified
  structural change this close to the real draft.
- **Section 15** (the owner's described full 380-row Ballers file: QB 36/RB 95/WR 131/TE 54/
  K 32/DST 32) — as already disclosed in directive C, this combined file does not exist on the
  owner's machine; only the real 36-row QB file has ever been imported. Not fabricated here
  either. The real 388-row multi-platform ADP file remains verified active and matched.
- **403 N 18th's own live ADP-selector re-verification** — not re-toggled this pass (it is a
  completed, real league with an owner-set `DISABLED` platform selection); its `provider: espn`
  field was re-confirmed correct via direct file read instead.

## Final verdict

**GREEN_MARKET_DATA_CONTROL_CENTER_V1** — the requested consolidation is real, live in the
product's frontend, typechecked, tested, and rendered; the engine is provably untouched. No
push, no merge, no deploy.
