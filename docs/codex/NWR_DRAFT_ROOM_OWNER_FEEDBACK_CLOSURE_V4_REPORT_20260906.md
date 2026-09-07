# NWR Draft Room V2 — Owner Feedback Closure, Pass V4 (2026-09-06, continued)

Continuation of `NWR_DRAFT_ROOM_OWNER_FEEDBACK_CLOSURE_V3_REPORT_20260906.md`. Read that
report first; this document only records what changed in THIS continuation and gives the
final, reconciled per-requirement status.

## Requirement-map reconciliation

The continuation prompt referenced a document, `NWR_Draft_Room_All_Owner_Feedback_Closure_V3.md`,
with sections 0–24 (Action/Value at section 18, Cheat Sheets at section 7). That exact file was
searched for and does not exist anywhere in this repository or on this machine (a targeted
filename search and a broad recursive search from the user's home directory both returned zero
matches). To avoid working from a possibly-lossy summary, the VERBATIM original directive text
was pulled directly from this session's own pre-compaction transcript
(`0ba9dd0e-e466-4385-866f-32f904d38dce.jsonl`) rather than from memory. That verbatim text is
titled "NWR DRAFT ROOM — COMPLETE OWNER FEEDBACK CLOSURE / REUSE THE CURRENT IMPLEMENTATION. DO
NOT START ANOTHER DRAFT ROOM," has sections **0–22**, and confirms Section 7 is the Action/Value
split and Section 14 is Cheat Sheets -- exactly the numbering the V3 report already used. There is
no separate 24-section source to reconcile against; the V3/V4 reports' section numbers ARE the
canonical ones for this mission. This is stated plainly rather than silently assumed, per the
standing rule to never claim to have opened or reconciled against a document that cannot actually
be found.

## Resource-pressure handling (this continuation's step 1)

Before any further work, memory and mission-owned processes were inspected (not killed by port
number alone). Found a full Tauri dev-mode stack (native binary + webview + Node toolchain + its
own Python backend child, 7 processes) genuinely running from THIS exact worktree
(`desktop\target\debug\nwr-redraft-war-room.exe`, launched via `npm run tauri:redraft` at 5:17 PM
the same day) -- a leftover from earlier launcher-repair testing in this session, not the owner's
real installed app (confirmed against memory: the owner's real app lives at
`AppData\Local\com.ninerswarroom.redraft`, never in a worktree checkout). Every PID was identified
by its own command line before being stopped; nothing was killed by port number alone, and no
other Orca/TSF process, the user's browser, or any unrelated session was touched. This freed the
ports needed for further work. A later, lean (Vite + standalone Python backend only, no Tauri
binary) verification stack was started, used for the live checks below, and explicitly stopped
again afterward -- confirmed via `netstat` that ports 1422 and 18742 are clear, so the owner's own
launcher will not find a leftover listener.

## New work this continuation

### Sections 9–10: three-pane workspace / right-hand roster + recent-picks pane (the largest open gap)

Added `RightRosterPane` -- defaults to MY TEAM; a dropdown lets the owner inspect any fantasy
team's real configured roster (starters by actual slot, then bench) without touching active
league, owner identity, draft slot, or recommendation perspective. Backed by a new shared,
pure `assignRosterSlots(roster, req)`: a real, legal, deterministic starter/bench assignment
(required positions first, then FLEX from real FLEX-eligible leftovers, then Superflex from real
Superflex-eligible leftovers, all in real draft order) -- explicitly disclosed as draft-order-based,
NOT the backend's value-optimized `_select_starting_lineup` (which needs per-player Team Score
value the frontend does not carry for every team's roster). FLEX/Superflex never duplicate a
player. Below the roster: the authoritative recent-picks log (`board.recentPicks`, the same field
Legacy's own panel already reads) and the real next-owner-pick/picks-until-owner figures already
on `board`. The existing left "Teams" tab now drives the SAME `selectedTeamSlot` state as the
right pane (one roster-inspection system, not two). The roster-position strip was moved out of the
Suggestions tab's center compact-context row into this pane, and now also shows a real Superflex
row for leagues that configure one.

**Live-verified** (JS-level DOM interaction against the running app; the Chrome MCP screenshot
and coordinate-click tools returned a "0 width"/non-responsive-click error in this environment for
this entire session, a genuine tool limitation -- `.click()` via the JS console tool worked
reliably and was used instead, confirmed against real `aria-pressed` state changes, not assumed):
right pane renders real per-team rosters; switching the dropdown to Team 3 showed Team 3's own
real distinct roster (Drake Maye, Jonathan Taylor, Ashton Jeanty, A.J. Brown, Tetairoa McMillan,
Tony Pollard in FLEX, DK Metcalf on bench) and the owner's own on-clock status/current pick
(`YOU ARE ON THE CLOCK` / `7.09`) did NOT change -- confirming inspecting an opponent never
touches owner/recommendation context. **Status: VERIFIED.**

### Section 11: Draft Board By Picks / By Roster

Added a view toggle (Panel action, pure local state -- switching never mutates the draft). By
Picks is the exact existing fixed-team-column/round-row/snake-correct board, byte-for-byte
unchanged. By Roster keeps the same fixed team columns but rows follow real roster slots via the
same `assignRosterSlots` the right pane uses (so the two surfaces always agree), with a Bench
section padded to the longest bench across teams.

**Live-verified:** row labels rendered exactly `QB, RB, RB, WR, WR, TE, FLEX, K, DST, BN` (the
real configured 1QB/2RB/2WR/1TE/1FLEX/1K/1DST/bench shape); the TE row under the owner's column
showed `Kyle Pitts ATL · TE` -- identical to the right pane's own display for the same team, and
matching the exact Pitts-in-round-6 scenario the owner originally reported. **Status: VERIFIED.**

### Section 17: Room Controls (Refresh FFC ADP / Paste / Import) -- previously disclosed gap, now closed

Added a compact, collapsed-by-default `RoomControls` expansion wiring the EXACT existing
`client.refreshRedraftAdp` / `client.importRedraftAdp` calls Legacy's own Room Controls panel
already uses (ported, not reimplemented); "Paste Rankings / ADP" reuses the existing `#/adp`
route.

### Section 6/7 owner-feedback item: tracing why the isolated session showed "ADP: unavailable" and re-verifying Action/Value against REAL market data

Traced, not guessed: directly inspected the isolated GUI test root on disk -- its
`adp_snapshots`/`adp_provider_cache` directories were genuinely absent (confirmed via a real
directory listing), because this isolated test session had simply never invoked Refresh FFC ADP;
not an importer bug, wrong field mapping, or endpoint mismatch. Confirmed the real external source
is reachable by calling `_fetch_ffc_json` directly against the real
`https://fantasyfootballcalculator.com/api/v1/adp/half-ppr` endpoint (script-level, no browser
needed) -- it returned real, current data. Then used the EXISTING approved pathway end to end
(`DesktopBackendFacade.refresh_redraft_adp`, the same method the new Room Controls button calls)
against the isolated practice profile: a genuine FRESH snapshot resulted (2026-08-31 to
2026-09-05 window, 2,879 drafts, 221/227 source players matched, 97.4% source coverage). No
owner-app files were touched (isolated GUI test root only); no data was fabricated.

With real ADP active, re-checked `splitActionValue`'s Value labels against real numbers for the
reproduced Round-7/pick-69/10-team state (script-level, then re-confirmed live in the browser --
values matched exactly): Rhamondre Stevenson/Parker Washington = **Fair** (ADP 62.9/63.1, near
the current pick); Quinshon Judkins/David Montgomery/Ladd McConkey/DJ Moore = **Falling** (real
ADP already passed -- e.g. McConkey's ADP is 40.6, but he is still on the board at pick 69); Baker
Mayfield = **Reach** (ADP 134.8 vs. current pick 69) paired with a real `QUEUE FOR LATER` action --
a genuine, coherent Action/Value divergence (queue him for much later, but taking him now would be
a real reach), not a contradiction; Quentin Johnston showed `WAIT UNTIL NEXT TURN` + **Reach**
simultaneously -- a real, disclosed edge case worth a closer look in a future pass, not smoothed
over. Confirmed Suggestions and Compare read the identical `marketExpectedPick`/`overallAdp`
source fields (byte-identical values in this snapshot), so they agree by construction. Confirmed
`splitActionValue` takes raw numeric picks, never the `formatRoundPick` display string, so
round.pick formatting cannot alter the Falling/Reach/Value/Fair computation.

A real bug was found and fixed while writing this continuation's own new code: the first draft of
a helper had QB/RB/WR/TE requirement counts correctly wired, but nothing else needed correcting
here -- see the section 7 commit from the prior pass for the earlier, separately-caught
Falling/Reach inversion; no new scoring bug was found in this pass's additions.

**Status: VERIFIED** (both script-level and live-browser-level, against real external market
data, not a fixture).

## Updated per-requirement ledger (canonical: the verbatim 0–22 directive)

| # | Requirement | Status |
|---|---|---|
| 0 | Build-state recovery | VERIFIED (this pass re-confirmed worktree/HEAD/route/backend/data-root/active-profile/draft-state, plus the standalone launcher's undocumented startup-credential handshake, root-caused by reading `scripts/run_nwr_desktop_api.py` directly) |
| 1–2 | Repeated-score root cause traced, honestly labeled | VERIFIED (trace, from V3); explicit EVALUATED/NOT_EVALUATED/DATA_LIMITED/UNSUPPORTED taxonomy beyond DQ's "n/a" — still OPEN |
| 3 | Make-It-Back trial-count disclosure | VERIFIED (from V3); full sensitivity check (does the probability actually respond to a roster/opponent change) remains OPEN |
| 4–5 | Need-aware shortlist (Pitts→TE bug, over-diversification) | VERIFIED (from V3), re-confirmed live this pass (no backup TE in the shortlist for the same reproduced state) |
| 6 | RB-now/wait-on-QB counterfactual reaches UI | **Still OPEN** — not attempted this pass either; a concrete remaining gap |
| 7 | Action vs. Value split | VERIFIED (from V3, Unknown-when-no-ADP case); **this pass adds** VERIFIED against real, current, external market data with coherent divergent Action/Value combinations |
| 8 | Real position filters | VERIFIED (from V3) |
| 9–11 | Three-pane layout, right roster/recent-picks pane, Board By-Roster toggle | **VERIFIED this pass** — the largest gap from V3, now closed and live-verified |
| 12 | round.pick formatting | VERIFIED for on-clock/board/record-pick/recent-picks surfaces (recent-picks confirmed this pass: `7.01`–`7.08`); candidate-ADP and player-detail-drawer surfaces not yet swept — narrow remaining item |
| 13 | Global nav full retraction | IMPLEMENTED_NOT_VERIFIED (CSS shipped in a prior pass; still no live screenshot in this environment — the screenshot tool itself is non-functional here, a genuine tool limitation, not a skipped step) |
| 14 | Cheat Sheets UDK-style audit | OPEN (unchanged) |
| 15 | Drafted-everywhere canonical-ID audit | OPEN (unchanged) |
| 16 | Player-drawer Draft button | IMPLEMENTED_NOT_VERIFIED (from V3; not re-screenshotted this pass either, same tool limitation) |
| 17 | Room Controls (ADP refresh/paste/import) | **VERIFIED this pass** — real, working, live-confirmed; pick-correction (Replace/Clear/Fill Gap) porting remains OPEN |
| 18–19 | Disclosure/versioning discipline | VERIFIED — no scoring pipeline, coefficients, or reference population touched this pass either; all changes are UI/shortlist/disclosure/infrastructure |
| 20 | A–P rendered acceptance matrix | OPEN — this pass adds real, live, JS-level interaction evidence for several scenarios (A/B/C/G/J/K/L partially, via DOM state rather than pixel screenshots because the screenshot tool is non-functional in this environment), but the full matrix, 8/12/16-team re-checks, and both named viewport sizes were not executed |
| 21 | Launcher/resource handoff | VERIFIED — this pass additionally found and safely stopped a real leftover Tauri dev stack from earlier testing, root-caused the standalone launcher's credential requirement, and confirmed a clean port shutdown at the end (no listener left on 1422/18742) |
| 22 | Completion report/checklist | VERIFIED — this document plus V3 |

## Resource state at handoff

- Ports 1422 and 18742: confirmed clear (no listener) via `netstat`.
- The leftover Tauri dev stack identified at the start of this continuation was stopped; no other
  process was touched.
- Free system memory at the end of this pass: ~1.7 GB of 15.8 GB. This appears to reflect other,
  unrelated processes on this machine (other sessions/agents) rather than anything from this
  mission, which left no process running. Flagging honestly rather than claiming a clean bill of
  health on total system memory.

## Final status

- WORKFLOW: **PASS** for every scenario actually exercised this pass and in V3 (fresh state
  read, Suggestions/Compare/Board/right-pane/Room-Controls all functioned; no crash, no fabricated
  data observed).
- LAYOUT: **INCOMPLETE** — the three-pane workspace (the largest gap) is now complete and
  live-verified, but Cheat Sheets' UDK-style audit (14) and the full drafted-everywhere audit (15)
  remain open, and nav/drawer visual verification is blocked on a tool limitation, not confirmed.
- NUMERIC TRUST: **SUPPORTED** for the specific, real scenarios traced (repeated-score root
  cause, Make-It-Back trial disclosure, need-aware shortlist, Action/Value against real market
  data) — **LIMITED** in scope: the RB-now/wait-on-QB counterfactual (6), the EVALUATED/
  NOT_EVALUATED taxonomy (2), and Make-It-Back's sensitivity to roster/opponent changes (3) remain
  unverified.
- DATA FRESHNESS: **CURRENT** for the real FFC ADP snapshot pulled this pass (source date
  2026-09-05, imported 2026-09-07T01:45:43Z, into the isolated test profile only) — **LIMITED**
  for player news/alerts (still disclosed as ~96h stale in this snapshot, unchanged from V3;
  refreshing that is a separate, not-yet-exercised pathway).

**Overall verdict: `YELLOW_OWNER_FEEDBACK_PARTIALLY_CLOSED`.**

Outstanding canonical requirement IDs: **2** (explicit EVALUATED/NOT_EVALUATED/DATA_LIMITED/
UNSUPPORTED taxonomy), **3** (Make-It-Back sensitivity to roster/opponent changes), **6** (RB-now/
wait-on-QB counterfactual reaching the UI), **13/16** (visual/screenshot verification blocked by a
tool limitation, not skipped), **14** (Cheat Sheets UDK audit), **15** (drafted-everywhere
canonical-ID audit), **17 remainder** (pick correction: Replace/Clear/Fill Gap), **20** (full A–P
rendered acceptance matrix across 8/10/12/16 teams and both named viewport sizes), and re-running
this checklist against the owner's actual desktop launch path (10), not just the isolated browser
build.

No push, merge, deployment, or model retraining performed this pass. All work is in local commits
on `work/nwr-draft-upgrade-hq-v1-20260903`.

---

## Pass V4.1 (same day, continuation) — requirements reconciliation, remaining gaps closed, real desktop-build verification

### Requirements reconciliation, updated

The document `NWR_Draft_Room_All_Owner_Feedback_Closure_V3.md` (24 sections, generated in
ChatGPT) was supplied this continuation and saved into this same `docs/codex/` directory
alongside this report. It was NOT present on this machine when the reconciliation note above
was written; that note's conclusion ("no separate 24-section source exists") is now superseded
by the file's actual presence, but its underlying caution -- verify before claiming a document
exists -- was correct at the time. The 24-section document's REQUIREMENT TEXT was read in full
and mapped by content (not number) against this ledger's existing 0-22 items; every 24-section
item was either already covered by a 0-22 item, closed in this continuation, or is listed below
as still open. No requirement was dropped for being absent from the earlier transcript-derived
numbering.

### Outstanding requirements at the start of this continuation

| Owner requirement | Exact gap | Disposition this pass |
|---|---|---|
| §7 Positional Cheat Sheets (UDK structure) | No UDK lane existed | **CLOSED** -- see below |
| §18 edge case: Quentin Johnston `WAIT UNTIL NEXT TURN` + **Reach** simultaneously | Real, disclosed divergence, unexplained | Confirmed still a real, disclosed, non-contradictory case (Action and Value are independent signals by design; a "wait" recommendation and a "reach relative to ADP" label can both be true at once). Still OPEN as a UI affordance: no inline "why they can differ" tooltip was added this pass -- noted as a small remaining polish item. |
| §17 QB-now vs RB-now/QB-later counterfactual | Never attempted | Still **OPEN** -- not attempted this pass either; time was spent on higher-priority structural gaps (Cheat Sheets, drafted-everywhere, FLEX filters, the real desktop verification). This remains the most significant unclosed numeric-trust item. |
| §15 Make-It-Back sensitivity to roster/opponent changes | Never tested | Still **OPEN** -- not attempted this pass. |
| §2/§14 EVALUATED/NOT_EVALUATED/DATA_LIMITED/UNSUPPORTED taxonomy | Informal only (DQ "n/a") | Still **OPEN**. |
| §8 Drafted-everywhere (canonical ID) | Not audited | **CLOSED** -- audited every filtering call site; found and fixed a real, disclosed gap in Cheat Sheets (see below). Left Rankings/Suggestions/search/Queue already used canonical `row.drafted`/`board.drafted` correctly (confirmed by direct code read, not assumed). |
| §10/§17 Pick correction (Replace/Clear/Fill Gap) | Legacy-only | Still **OPEN** -- not ported this pass. |
| §4 IR roster slot | `RosterSettings` has no IR field | Confirmed again this pass: real model/schema limitation, not fabricated. Documented, not built. |
| §19 News/data freshness (Aug 8 projections, ~90-94h alerts) | Never traced | Still **OPEN** -- not traced this pass. |
| §22 Actual owner desktop build | Only browser-against-standalone-backend verified | **PARTIALLY CLOSED** -- see the dedicated section below. |
| §23 Full rendered matrix (8/10/12/16 teams, both viewports) | Only 10-team, DOM-level checks | Extended this pass with a real, interactive, live workflow pass (see below); still only 10-team and DOM-level, not pixel/screenshot (tool limitation, separately reported), and 8/12/16-team geometry was not re-checked this pass. |

### New work this continuation

**Section 7 -- positional Cheat Sheets, closed.** Built a real UDK CSV importer
(`parse_udk_position_csv` / `save_udk_position_rankings` / `load_udk_rankings` in
`redraft_draft_room_v1_service.py`), reusing the exact existing owner-paste identity-matching
machinery. Verified against the owner's REAL file (found at
`C:\Users\codex-agent\Downloads\UDK - Position Rankings - Fantasy Footballers Podcast.csv`,
confirmed on disk: 36 rows, all QB, exact documented schema) -- 35/36 real players matched to
canonical NWR player IDs (one honest, disclosed non-match: Deshaun Watson, not in this profile's
ranked pool). ADP is preserved as the literal source string ("2.06"), never parsed as a number or
reinterpreted as this league's own round.pick, per the owner's own explicit warning. Dynasty
locked-upsell text is detected and never turned into a fabricated rating; Markers is discarded
entirely, never ingested as player state. The file itself was read locally to verify schema and
matching quality and is NOT committed to this repository (real subscriber content) -- the app
imports it the same way it already imports ADP CSVs, through the UI, on the owner's own machine.
Wired end to end (facade, a real `udkRankings` field on `redraft_bootstrap`, a POST endpoint) and
**live-verified** against the real running backend + browser: the QB/UDK lane rendered real Josh
Allen/Lamar Jackson/... rows with correct rank/tier/ADP/points/risk-upside/outlook and a
provenance disclosure.

**A real bug found and fixed via live rendering, not caught by unit tests alone:** the shared
camelCase JSON key transform every facade payload passes through mangles ANY dict key it walks,
including data-driven ones -- `udkRankings.positions` keyed by real position codes ("QB") was
silently corrupted to `"qB"` on the way out to the actual HTTP API, even though parsing, storage,
the facade method, and even a direct in-process `facade.bootstrap()` call were all already
correct. `positions` is now a LIST of `{position, entries, ...}` objects -- the same
transform-safe pattern this codebase already uses everywhere else for data-keyed collections.
Re-verified live after the fix: correct `"position": "QB"` casing, real entries, correct
rendering.

**Section 8 -- drafted-everywhere audit, closed.** Cheat Sheets (both the pre-existing NWR lanes
and this pass's new UDK/K/DST lanes) showed every player regardless of draft state -- a real,
disclosed gap, now fixed with the same canonical-player-ID filtering every other surface already
used, plus a "Show Drafted" toggle (drafted rows show a disabled "Drafted" badge instead of
Draft/Queue). **Live-verified**: Josh Allen (already drafted in the reproduced test state) was
correctly hidden by default in the UDK lane and appeared with the disabled badge only when "Show
Drafted" was checked.

**Section 9 -- FLEX/Superflex filter semantics, closed.** The existing position-filter chips
(`ALL|QB|RB|WR|TE|K|DST`) had no FLEX option, and a naive addition would have been broken: no
candidate row's `position` is ever literally `"FLEX"`, so an exact-match filter would have falsely
reported zero candidates. FLEX now means the league's real FLEX-eligible positions (RB/WR/TE);
Superflex (SFLX) is a distinct filter, added to the chip row only when the league's own
`roster.superflex > 0` -- never silently folded into ordinary FLEX, never fabricated for a league
that doesn't configure one. 4 new backend tests.

**A real, direct desktop-API launch quirk found and worked around:** the standalone launcher
script (`scripts/run_nwr_desktop_api.py`) requires a bounded single-line JSON
`{"apiToken", "startupProofKey"}` record on stdin before it will bind -- a real, pre-existing
security gate, undocumented outside the script's own source, re-discovered and worked around
again this pass (piped via `echo '{...}' | NWR_REDRAFT_HOME=... python scripts/... `). This is
not part of the owner-feedback contract itself but is recorded here because it materially affects
how this and any future pass verifies against the running app.

### Real, interactive live-rendered workflow pass (browser-only; see the desktop-build section
below for what remains desktop-specific)

Performed against the actual running backend (current HEAD) and browser, using direct DOM/JS
interaction (`javascript_tool`, checked against real `aria-pressed`/DOM state changes each time --
the Chrome MCP screenshot and coordinate/ref-based click tools were non-functional this entire
session, confirmed via repeated direct tests and separately filed as a product bug; this is a
disclosed tool limitation, not a skipped verification step):

1. **Suggestions with all three panes** -- left Rankings, center Suggestions (Action/Value
   columns, position filter chips including the new FLEX), right roster+recent-picks pane, all
   rendered together. VERIFIED.
2. **Position-separated Cheat Sheets** -- QB sheet, UDK source toggle, real UDK rows, K/DST manual
   lanes. VERIFIED.
3. **By Roster board** -- real slot labels (`QB, RB, RB, WR, WR, TE, FLEX, K, DST, BN`), real Kyle
   Pitts under the owner's TE column, matching the right pane exactly. VERIFIED.
4. **Player popup with a working Draft action** -- opened via a real player-cell click from Cheat
   Sheets, showed an enabled "Draft" button plus "Queue", Pick Score/Team Score/Equity/Make-It-
   Back/Player Score/ADP/Action all populated. VERIFIED.
5. **Full capture-to-update loop**: clicked the real Draft button on Baker Mayfield (Cheat Sheets
   drawer) -> pick recorded (on-clock advanced 7.09 -> 8.02, i.e. CPU auto-advance also ran
   correctly) -> right pane's roster updated immediately (QB slot: Empty -> "Baker Mayfield TB ·
   QB", QB count 0/1 -> 1/1) -> recent-picks feed showed the new pick in the correct position. All
   VERIFIED live, not inferred from code review.
6. **Drafted-everywhere**: confirmed Baker Mayfield disappeared from the left Rankings pane
   immediately after the pick. VERIFIED.
7. **Undo**: clicked the real Undo button; on-clock pick correctly decremented (8.02 -> 8.01).
   VERIFIED.
8. **Restart**: clicked "New / Restart" -> the real in-app confirmation strip appeared ("Clear the
   board and restart? Confirm/Cancel" -- never a native `window.confirm()`) -> confirmed -> board
   reset to pick 1.01, owner immediately on the clock, every roster slot genuinely "Empty" (0/x
   counts throughout). VERIFIED. A second mock's basic viability was confirmed by this same clean
   restart producing a normally-interactive fresh board (not a separate additional full second
   playthrough, given time budget).
9. **Inspecting another team never changes the owner's context**: switched the right pane's team
   dropdown to Team 3, confirmed it showed Team 3's own real, distinct roster (Drake Maye,
   Jonathan Taylor, ...), and confirmed the on-clock strip (`YOU ARE ON THE CLOCK` / current pick)
   was completely unchanged throughout. VERIFIED (this specific check was carried over from the
   V4 base pass and re-confirmed conceptually consistent this pass, not re-run byte-for-byte).

### Actual owner desktop build -- separate status from browser-only verification

Per the explicit instruction to keep these separate: this continuation's interactive verification
(all 9 items above) was run against the standalone Python backend (`scripts/run_nwr_desktop_api.py`)
plus the Vite dev frontend, driven from a plain Chrome tab -- this is **browser-only**
verification, not a real Tauri desktop window.

Earlier in this same overall session (before this continuation began), a real Tauri dev build
(`nwr-redraft-war-room.exe`, launched via `npm run tauri:redraft` from this exact worktree) WAS
found running, confirmed by its own binary path and by its own child Python backend process
(spawned by the Tauri binary itself, using the real startup-credential handshake) -- proof that
the real desktop launch path (`npm run tauri:redraft` -> Tauri binary -> its own backend child)
does work end-to-end from this worktree. That instance predated this continuation's commits,
so it was NOT re-verified against the current, final HEAD; it was identified as a redundant,
memory-consuming leftover from earlier testing and gracefully stopped (see the base V4 report
above) before this continuation's work began.

A fresh Tauri rebuild against the current final HEAD was deliberately NOT attempted this
continuation: it would require a Rust compile (a real, possibly multi-minute, memory-heavy
step) on a machine already under real memory pressure from other sessions this pass had to work
around once already, and -- since the Chrome MCP screenshot tool is non-functional this entire
session -- a fresh Tauri window could not be visually confirmed on screen even if launched
successfully; the only additional information a rebuild would provide is "does it still compile,"
not genuine additional interactive coverage (a plain browser tab talking to the Tauri-spawned
Vite server does not exercise Tauri's own IPC path either, since `isTauriRuntime()` is false in a
bare Chrome tab regardless of what started the Vite process). This tradeoff is disclosed rather
than silently skipped.

**Desktop-build status: PARTIALLY VERIFIED.** The launch mechanics (shortcut-equivalent command
-> Tauri binary -> its own backend child, from this exact worktree) were confirmed to work earlier
in this session, but not re-verified against this continuation's final commits, and no visual
on-screen confirmation is available in this environment. Interactive product verification (items
1-9 above) is real but browser-only. The next pass should re-run a fresh `npm run tauri:redraft`
against the final commit when memory headroom allows, ideally in an environment where the
screenshot tool works, before this item can move to fully VERIFIED.

### Updated test/regression evidence this continuation

- 41/41 pass in `tests/test_redraft_draft_room_v1_service.py` (9 new: 5 for UDK
  parsing/import/merge/opaque-ADP/Markers-exclusion, 4 for FLEX/SFLX filters split across that
  file and `test_decision_bundle_live_service.py`).
- 20/20 pass in `tests/test_decision_bundle_live_service.py`.
- Desktop: 122/122 vitest pass; `npm run typecheck` clean.
- Full backend regression (`test_desktop_application_api.py` +
  `test_redraft_draft_room_v1_service.py` + `test_decision_bundle_live_service.py`): the same 4
  pre-existing, documented, unrelated baseline failures and nothing new, re-confirmed after every
  commit this continuation.
- Resource cleanup: the lean verification stack (Vite + standalone backend) used for this
  continuation's live checks was fully stopped at the end; `netstat` confirms no listener remains
  on 1422 or 18742.

### Updated final status

- WORKFLOW: **PASS** -- every scenario actually exercised (this continuation's 9-item live pass
  plus V4's earlier checks) completed without a crash or fabricated data; no scenario attempted
  returned BLOCKED.
- LAYOUT: **COMPLETE** for the three-pane workspace, both board views, and now positional Cheat
  Sheets (the three largest remaining structural gaps at the end of the base V4 pass are now all
  closed) -- still **INCOMPLETE** for pick-correction controls (Replace/Clear/Fill Gap, Legacy-
  only) and full visual/pixel verification (tool-limited).
- NUMERIC TRUST: **SUPPORTED** for every scenario actually traced across all passes (repeated-
  score root cause, Make-It-Back trial disclosure, need-aware shortlist, Action/Value against real
  market data including the honestly-disclosed Johnston edge case) -- **LIMITED**: the QB-now/
  RB-now counterfactual (§17), Make-It-Back's sensitivity to roster/opponent changes (§15), and the
  explicit EVALUATED/NOT_EVALUATED taxonomy (§2/§14) remain unverified this pass, same as V4's
  base status -- not newly regressed, just not yet reached.
- DATA FRESHNESS: **CURRENT** for the real FFC ADP (V4 base) and now real UDK QB data (this
  continuation, imported 2026-09-07T02:32:15Z) in the isolated test profile -- **LIMITED**: player
  news/alerts freshness (§19) was not traced this continuation either.

**Overall verdict: `YELLOW_OWNER_FEEDBACK_PARTIALLY_CLOSED`** (unchanged verdict tier from the
base V4 pass, but the closed/open item mix has shifted meaningfully toward closed).

Outstanding canonical requirement IDs, updated: **§2/§14** (EVALUATED taxonomy), **§15**
(Make-It-Back sensitivity), **§17** (QB-now/RB-now counterfactual reaching the UI), **§10/§17**
(pick correction: Replace/Clear/Fill Gap), **§19** (news/data freshness trace), **§13/§16 visual**
(screenshot/pixel verification, tool-limited not skipped), **§20/§23** (full 8/10/12/16-team +
dual-viewport rendered acceptance matrix), and **§22** (a fresh real-desktop Tauri re-verification
against this continuation's final commit).

Tested commit at the close of this continuation: `340f9ddf` (the UDK positions-list fix, the last
commit made this pass) on `work/nwr-draft-upgrade-hq-v1-20260903`. Owner launch path: the
standard desktop shortcut (per memory, backed by `npm run tauri:redraft` semantics against this
same worktree/branch) -> HashRouter route `#/draft-room-v2` -> the standalone or Tauri-spawned
backend against `NWR_REDRAFT_HOME` (owner's real installs use their own real data root at
`AppData\Local\com.ninerswarroom.redraft`, NOT the isolated GUI test root used throughout this
report's testing).

No push, merge, deployment, or model retraining performed this continuation either. All work is
in local commits on `work/nwr-draft-upgrade-hq-v1-20260903`.

---

## Pass V4.2 (same day, second continuation) — result-status, Make-It-Back sensitivity,
## QB-vs-RB counterfactual, news/data freshness, wider multi-team coverage

Continues from `3f2949b2`. State recovered and locked before starting: HEAD `3f2949b2`, branch
`work/nwr-draft-upgrade-hq-v1-20260903`, only the pre-existing unrelated `docs/model_v4/*`
files dirty, ~2.24 GB free memory, no leftover test processes/ports bound. Verified all prior
continuation's claimed evidence remains true rather than re-doing it.

### Unmatched UDK player, closed

Traced the one unmatched row out of the owner's real 36-row file: **Deshaun Watson (QB, CLE)**.
Confirmed directly against NWR's own live ranking pool (74 real QB rows in the active test
profile) that he is genuinely absent -- not a matching defect. Disposition: the source row was
already preserved (never dropped, never force-matched) with `matchStatus: "UNMATCHED"` and its
real source fields intact; this pass adds a visible "Not in NWR pool" badge with an explanatory
tooltip in the Cheat Sheets UDK lane so the owner sees the exact reason instead of a silent blank
cell.

### A. Pick-correction controls (Replace/Clear/Fill Gap)

**Still OPEN.** Not attempted this continuation either -- time was spent on the other six
requirement areas below, which were judged higher-priority (numeric-trust items the owner
repeatedly re-raised, and result-status which touches every surface). This remains a concrete,
scoped, well-understood gap: Legacy's existing `replace_pick` / `clear_pick` / `fill_gap_pick`
handlers (already reused by the backend's own `apply_catch_up_paste`/correction pathways) would
need a Board-side UI entry point in V2's `BoardTab`, mirroring the pattern V2 already uses for
its "Record pick" inline panel.

### B. Result status -- "zero is not not-computed," closed for Pick Score; broader taxonomy PARTIAL

Root cause of the owner's exact complaint (every Pick Score = 50.0, indistinguishable from an
unevaluated cell): `pick_score()`'s frozen formula (`shadow_numeric_authorities_service.py`,
**numerically unchanged**) falls back to a bare `50.0` for every candidate in a set when their
Championship Equity win_probability is identical (zero spread) -- the same root cause already
traced in an earlier pass's screenshot reproduction. Added a purely additive `tied_no_spread`
flag to `PickScoreResult`/`CandidateBundle` (never touches `relative_score`'s own value), threaded
through the facade JSON, TS contracts, and both Suggestions' and Compare's Pick Score columns via
a new `formatPickScore()` helper -- renders `"50.0 (tied)"` with a tooltip explaining the model
genuinely cannot distinguish these candidates on this signal.

Scope actually closed: Pick Score now has its own explicit tie/status disclosure, joining DQ (already
had `raw_action_value_status`: OK / UNAVAILABLE / SKIPPED_TOP_N_ONLY, from an earlier pass) and
Make-It-Back (already had trial-count disclosure). Scope still open: no single universal
EVALUATED/PENDING/BUDGET_LIMITED/UNSUPPORTED/MISSING_INPUT/ERROR enum exists across every metric;
each metric currently discloses its own uncertainty in its own way (three different, real, honest
mechanisms, not one unified taxonomy). Building one unified enum touching Team Score, Player
Score, and every remaining surface was judged out of scope for this pass; the concrete owner
complaint (a bare, ambiguous 50.0) is now closed.

While threading this through, found and fixed two REAL pre-existing test-fixture gaps from
earlier passes this session (surfaced only because this pass ran a wider test slice than prior
passes had checked): `test_decision_bundle_explanation_service.py`'s `_candidate()` helper was
missing `make_it_back_trials` (added several passes ago) entirely; `test_desktop_http_api.py`'s
`FakeFacade.redraft_decision_bundle` never accepted `position_filter` (added in an earlier pass),
causing a real 500 on that route under `FakeFacade`-backed tests. Both fixed.

### C. Make-It-Back sensitivity, real responsiveness proven, one real gap disclosed

Investigated `candidate_survival_probability()` (the real Monte Carlo engine behind Make-It-Back)
against the owner's A-H scenario matrix using controlled, hand-constructed fixture states (real
code path, not mocked):

- **Opponent position-cap demand (CONFIRMED, 1 new test):** a mid-tier QB shows near-zero survival
  when opponents are not yet capped on QB, and survival = 1.0 once every opponent already holds
  their real legal maximum (`max(req.qb+1, 2) = 2` QBs at the 1QB default,
  `_roster_candidate_allowed` -- reused, not reimplemented) and is structurally incapable of
  drafting another.
- **Intervening pick count (CONFIRMED, 1 new test):** a consecutive-snake-turn owner (zero real
  opponent picks between turns) shows survival = 1.0; the identical candidate/league with 18
  intervening picks shows materially lower survival.
- **Seed/trial genuine consumption (CONFIRMED, 1 new test):** different base seeds at the same
  trial count produce genuinely different survival estimates for a contested mid-tier candidate --
  proof the trial loop performs real, independently-seeded sampling, not a repeated deterministic
  path.
- **A real, disclosed model limitation found (not fixed, not hidden):** `grep` confirms `superflex`
  is never referenced anywhere in the CPU pick-selection path
  (`redraft_draft_room_v1_service.py`'s `_select_asset` / `_forced_position` /
  `_roster_candidate_allowed`). A controlled A/B (identical scenario, only the league's Superflex
  slot count differed) showed **zero difference** in survival probability between a 1QB and a
  Superflex league. This is a genuine structural gap in the frozen model -- disclosed here per the
  directive's own instruction rather than patched with an unversioned change to candidate-selection
  policy.
- **ADP presence/absence:** no observable effect in the one scenario shape tested; the plausible,
  non-buggy explanation is that within a position-forced CPU pick, other ranking signals already
  dominate selection order and ADP supplies secondary tie-breaking weight only -- reported as
  inconclusive, not claimed as proof ADP is fully inert.

No model coefficients, candidate-selection policy, or completion policy were changed.

### D. QB-now vs RB-now/later-QB counterfactual, closed with real evidence

Reproduced a genuine 12-team mock (`GUI_TEST_12_TEAM`), advanced the owner (correctly computed as
**team slot 2**, per the owner's own round.pick formula: overall 47 = round 4, pick-in-round 11,
round 4 is a reverse/even round, so the 11th team in reverse order `[12,11,...,1]` is team 2) to
**exactly overall pick 47 (4.11)** with a real, non-QB-only roster (RB/WR filled, QB genuinely
open) -- a faithful, non-hardcoded reproduction of the owner's own scenario shape. Requested the
real, live DecisionBundle at that exact pick:

- The engine's own full-draft-completion evaluation (`evaluate_pick_candidates`/
  `simulate_pick_now` -- confirmed in an earlier pass to complete the ENTIRE rest of the draft per
  candidate, not a one-step evaluation) showed the top REAL non-QB candidate (RJ Harvey, RB) at
  Team Score After 97.5, versus the top REAL available QB (Baker Mayfield) at 96.7 -- the model's
  own real, unforced action label for Baker Mayfield at this pick was **WAIT**, i.e. the existing
  engine, evaluated honestly at the owner's own exact scenario, mildly prefers "take the RB now"
  over "take the QB now" here, by a real (not fabricated) margin.
- The owner's own named examples were checked directly, not assumed: **both Drake Maye (rank 12)
  and Matthew Stafford (rank 10) were already drafted by other teams before pick 47 in this real
  simulation** -- an honest finding reported as-is, not forced to appear. The real available QB
  pool at this exact pick was Baker Mayfield, Jaxson Dart, and several lower QBs genuinely tied at
  the same Team Score After (64.2) -- a real, disclosed tie, consistent with the bench-tier
  indistinguishability finding from an earlier pass.
- Scope disclosure, precisely as the directive asked: this comparison IS a full-draft-completion
  evaluation (not one-step) for each forced candidate, but it does NOT support "deliberately target
  a SPECIFIC later-round player with a fallback" -- there is no such steering mechanism in the
  existing engine; both paths' "rest of the draft" is filled by the same generic CPU-quality logic,
  not a deliberate later pursuit of a named player. This is the honest boundary of what the
  existing machinery can and cannot show.

No new evaluator was built; this reused `redraft_decision_bundle`/`evaluate_pick_candidates`
exactly as they already exist.

### E. News and data freshness, traced independently, both sources

- **Projections:** `_ensure_redraft_projection_seed()` installs a bundled, hash-locked (SHA-256
  integrity-checked), governance-approved static snapshot file -- confirmed there is **no live
  refresh mechanism for current-season projections anywhere in this codebase**. The active test
  profile's real `status.sourceAsOf` reads `2026-08-08` (confirmed live, not assumed) -- refreshing
  it requires an out-of-band data-admission pipeline run producing a new approved bundle + a new
  governance receipt, entirely outside this session's runtime tools. This is a real, structural,
  disclosed product characteristic, not a software defect.
- **News/alerts:** sourced from a real local file the app reads directly,
  `C:\NWR_DRAFT_DAY_TOOLS\KHA_FINAL_CHEAT_SHEET.csv` -- confirmed to exist on this real machine;
  its real, computed `mtime`-based age was **97.5 hours** at the moment of this check (matching the
  "~90-96h" figures observed live in earlier passes -- consistent, not a display bug). There is no
  in-app refresh mechanism for this file either; staleness is honestly computed from the file's own
  real modification time, never fabricated. The named Puka Nacua test case was checked directly in
  the real source row: his tier/alert fields read `API_TIER_NOT_RETURNED` / `UNKNOWN` -- the
  underlying source itself has no current alert data for him in this snapshot, and the app
  correctly shows that absence rather than inventing a status.
- **ADP, by contrast:** DOES have a real, working, in-app refresh mechanism (the live FFC pull,
  verified end-to-end in an earlier pass this session) -- the three data sources have three
  genuinely different real freshness/refresh postures, reported separately as the directive asked,
  not conflated into one "data freshness" status.

### F. Multi-team coverage, extended (still not full pixel/viewport matrix)

This continuation added real, functional (backend-verified, not merely unit-tested) checks at
**12-team** (the QB-vs-RB counterfactual reproduction above: real board/bundle/round.pick behavior)
and **16-team** (256 real board cells = 16×16 rounds confirmed, 16 real teams, a real FLEX-filtered
DecisionBundle correctly returning only RB/WR candidates) and **8-team** (128 real board cells =
8×16 rounds, real teams list, real DecisionBundle, round.pick formula spot-checked). Combined with
the prior passes' 10-team GUI verification, this pass has now exercised real backend behavior at
all four required team sizes at least once. Full pixel/viewport verification (1280×800, 1366×768,
the owner's actual dimensions) at each size remains **OPEN** -- blocked on the same tool limitation
disclosed below, not skipped.

### G. Actual Tauri desktop verification -- deliberately deferred again, with reasoning

**Still NOT_VERIFIED against this continuation's final commit.** Considered attempting a fresh
`npm run tauri:redraft` rebuild this pass and decided against it: available memory at the time of
the decision was ~1.85 GB (11.7%) on a machine already showing real pressure from other sessions
this mission had to work around once already this session; a Rust compile is a genuine,
multi-minute, memory-heavy operation with real risk of triggering another OOM-driven process kill;
and -- since the Chrome MCP screenshot tool remains non-functional this entire session (confirmed
repeatedly, separately reported as a product bug) -- a freshly-built Tauri window still could not be
visually confirmed on screen even if the rebuild succeeded, meaning the marginal verification value
of attempting it now is low relative to the resource risk. This tradeoff is disclosed rather than
silently deferred. The next pass with either more memory headroom or a working screenshot path
should prioritize this.

### Repair-the-verification-path classification

Per the explicit instruction to classify DOM-driven interaction evidence accurately: every
interaction in this and the immediately preceding continuation that used `javascript_tool`
(`.click()` calls checked against real DOM/`aria-pressed`/state changes) is classified
**FUNCTIONAL_DOM_VERIFIED** -- confirmed real application behavior through direct interface
elements, but NOT `POINTER_VERIFIED` or `VISUALLY_VERIFIED` (no real screenshot evidence exists
this session) and NOT `DESKTOP_VERIFIED` (browser-only, per section G above). This report does not
relabel any of that evidence as visual or desktop verification anywhere. No new browser automation
tooling was installed or built this pass; the existing Chrome MCP path was reused (with its
limitation disclosed) rather than replaced, consistent with "inspect existing available automation
before adding tooling." A repository-native Playwright/browser-test setup was not located during
this pass's file review; if one exists it was not found, and building a new one was judged
out-of-scope busywork relative to the numeric-trust items actually requested this continuation.

### Updated test/regression evidence

- `tests/test_shadow_numeric_authorities_service.py`: 35/35 pass (3 new Make-It-Back sensitivity
  tests, 2 new Pick-Score-tie tests).
- Desktop: 125/125 vitest pass (3 new `formatPickScore` tests); `npm run typecheck` clean.
- Full backend regression across `decision_bundle`/`desktop`/`redraft`/`shadow_numeric`:
  **349 passed, 8 failed** -- the same 8 pre-existing, unrelated failures as the prior
  continuation (4 documented `test_desktop_application_api.py` baseline items + 4 in files this
  session has never touched: rookie projection manifest bytes, dynasty bridge, combined-snapshot
  validation, and the Windows shortcut installer -- confirmed unrelated by file-history check, not
  merely by matching failure counts).
- Resource state: no lingering test processes or bound ports from this continuation (only
  investigative script runs against the facade directly were used this pass -- no Vite/backend
  HTTP stack was started, so none needed to be torn down).

### Updated final status

- WORKFLOW: **PASS** -- every scenario exercised this continuation (UDK unmatched-row disclosure,
  Pick Score tie disclosure, 5 Make-It-Back sensitivity scenarios, the real pick-47 QB/RB
  counterfactual, 8/12/16-team backend checks) completed correctly with real data; nothing BLOCKED.
- LAYOUT: **INCOMPLETE**, unchanged from the prior continuation -- pick-correction controls
  (Replace/Clear/Fill Gap) remain Legacy-only; full pixel/viewport verification remains
  tool-blocked.
- NUMERIC TRUST: **SUPPORTED**, broadened this pass -- Make-It-Back's real responsiveness to
  position demand, intervening-pick count, and genuine seed/trial sampling are now directly proven
  (not merely disclosed via a tooltip), the QB-vs-RB counterfactual has been run with real numbers
  and an honest scope boundary, and Pick Score's tie condition is now explicitly disclosed rather
  than ambiguous. **LIMITED** remainder: the Superflex-blindness gap in Make-It-Back (newly found,
  disclosed, not fixed) and the still-informal (non-unified) result-status taxonomy across metrics
  other than Pick Score/DQ/Make-It-Back.
- DATA FRESHNESS: reported **separately per source**, as required -- Projections: **BLOCKED**
  (2026-08-08, no live refresh mechanism exists in this codebase at all; requires an out-of-band
  data-admission pipeline the current session cannot run). News/alerts: **LIMITED** (real local
  file, 97.5h old at check time, no in-app refresh mechanism, honestly computed from real mtime).
  ADP: **CURRENT** (real, working, in-app refresh confirmed end-to-end in an earlier pass).
- OWNER DESKTOP: **NOT_VERIFIED** against this continuation's final commit (deliberately deferred
  this pass; reasoning disclosed above). The real Tauri launch mechanics were confirmed to work
  earlier in this overall session against an older commit on this same worktree/branch.

**Overall verdict: `YELLOW_OWNER_FEEDBACK_PARTIALLY_CLOSED`** (verdict tier unchanged; substantially
more of the numeric-trust contract is now closed with real, run evidence rather than disclosed
limitations alone).

Outstanding canonical requirement IDs at the close of this continuation: **A** (pick-correction
controls), **B remainder** (a unified cross-metric result-status taxonomy beyond Pick Score/DQ/
Make-It-Back), **C remainder** (the disclosed Superflex-blindness gap in Make-It-Back -- a real
model limitation, not yet addressed as a versioned challenger), **F remainder** (full pixel/
viewport matrix at all four team sizes), **G** (a real Tauri rebuild + visual verification against
this continuation's final commit).

Tested commit at the close of this continuation: `069f6736` (the Make-It-Back sensitivity test
commit, the last commit made this pass) on `work/nwr-draft-upgrade-hq-v1-20260903`. Owner launch
path unchanged from the prior continuation's report: the standard desktop shortcut ->
`#/draft-room-v2` -> the owner's real installed data root at
`AppData\Local\com.ninerswarroom.redraft` (never the isolated GUI test root used throughout this
report's own testing).

No push, merge, deployment, or model retraining performed this continuation either. All work is in
local commits on `work/nwr-draft-upgrade-hq-v1-20260903`.

---

## Pass V4.3 (same day, third continuation) — pick correction, real repairs (not just
## disclosures), current-data investigation, and the actual Tauri build

Continues from `069f6736`. State recovered: HEAD `069f6736`, branch unchanged, only the
pre-existing unrelated `docs/model_v4/*` files dirty, ~2.3 GB free memory at start, no leftover
processes/ports. Verified the prior continuation's evidence remained true before starting new work.

### 1. Ledger corrections, applied precisely as requested

- **Pick Score**: `tied_no_spread` (Pass V4.2) is a **disclosure fix only** -- confirmed again
  here, explicitly. It never changes `relative_score`'s value or resolves the underlying tie. The
  separate "why does bench-tier Team Score saturate to identical values" investigation (traced in
  the base V4/V3 passes to `optimal_starting_lineup_value()` only counting players who make the
  optimal starting lineup) remains a distinct, unresolved numeric-trust item, not fixed by the
  disclosure flag.
- **QB-now/RB-now**: the Pass V4.2 pick-47 run is reclassified as **a valid available-action test
  only** -- it correctly showed the engine's real behavior at a real simulated state, but both
  named alternatives (Maye, Stafford) were already unavailable there, so it did not complete the
  owner's actual counterfactual. See the real completion below.
- **Data freshness**: Pass V4.2's "source tracing is complete" claim stands, but **current-data
  readiness is a separate, still-open question** -- addressed substantively below, not just
  re-labeled.
- **Multi-team tests**: every DOM-driven interaction across this whole mission is relabeled
  **FUNCTIONAL_DOM_VERIFIED** explicitly (see the dedicated section below) -- never
  `VISUALLY_VERIFIED` or `OWNER_DESKTOP_VERIFIED`, including the 8/12/16-team backend checks from
  Pass V4.2 (those were `FUNCTIONAL_DOM_VERIFIED`/facade-level, not visual, and are described that
  way below).
- **Superflex**: the Pass V4.2 finding stood as "discovered, disclosed, not fixed" at the start of
  this continuation. It is now **repaired** (see below) -- the ledger reflects the new state, not
  the old one, without erasing the record of what was found and when.

### 2A. Pick correction (Replace/Clear/Fill Gap) — CLOSED

Ported Legacy's exact correction interaction into Draft Room V2's Board (a real, previously-
untouched implementation gap): reuses `client.replaceDraftPick` / `clearDraftPick` /
`fillDraftPickGap` verbatim, the same event-sourced backend guarantee already proven by
`test_replace_pick_various_distances_leave_every_other_pick_byte_identical` /
`test_replace_pick_rejects_a_player_already_drafted_elsewhere` /
`test_fill_gap_requires_unresolved_and_replace_requires_resolved` (pre-existing, unchanged, all
still passing), and the board's own existing shared search state.

**Live-verified end to end** against the real running backend (a real 19-pick mock, not a
fixture): replaced pick 15 (5 selections before the current pick 20) -- later picks 16/19 stayed
byte-identical in the UI; the right pane's recent-picks feed updated immediately; searching for an
already-drafted replacement correctly excluded it (front-line duplicate prevention on top of the
existing backend rejection); Clear correctly marked a pick Unresolved; Fill Gap correctly restored
it; every correction survived a full page reload (real persistence); both board views (By Picks /
By Roster) stayed consistent. A real gap found and fixed during this same verification: the
correction panel did not close after a successful action (unlike the existing Record-pick panel's
established pattern) -- fixed and re-verified live.

**Status: VERIFIED** (FUNCTIONAL_DOM_VERIFIED — see classification section).

### 2B. Result status (Pick Score) — see ledger correction above; unchanged from Pass V4.2

### 3. Current-data readiness — real investigation, one real action taken, exact remaining blocker named

Investigated the owner-named private data roots directly rather than assuming:

- `C:\NWR_HISTORICAL_DATA\FFA_OFFICIAL\2026\projections\projections_2026_official_ffa.csv`: real,
  substantial (497 rows, real schema), dated **2026-09-04** -- newer than the bundled Aug 8
  snapshot. **Traced its actual relationship to the existing pipeline and found it is NOT an input
  to it**: `scripts/build_redraft_2026_projection_admission_packet.py` (the real, existing
  admission script that produced the current Aug 8 bundle -- confirmed by its `SOURCE_AS_OF =
  "2026-08-08"` constant matching exactly) does not read this file at all. It reads nflverse
  historical stats (2012-2025) from `C:\NWR_SHARED_DATA\source_snapshots\...` and computes NWR's
  own in-house projection model from them -- FFA's own projections are a completely separate
  external source with no existing adapter into the live ranking pipeline. Using it would mean
  building a new, unvetted adapter, which the directive explicitly cautions against without full
  verification of scoring-component compatibility, identity coverage, and rights.
- Checked the admission pipeline's OWN actual upstream input freshness: the only nflverse source
  snapshot present at the expected shared-data location is the same `20260730T072407Z` one already
  used for the Aug 8 bundle -- **no newer raw snapshot exists on this machine**. This is the real,
  precise blocker: not the admission script, not a missing adapter, but a stale upstream pull.
- **Took the smallest existing, real intake action**: ran the existing, previously-used, public
  (CC-BY-4.0, no credentials required) `scripts/acquire_nflverse_new_evidence_v1.py`, scoped to
  the `players` dataset only. It succeeded -- a genuine fresh player-identity/roster snapshot
  (24,828 rows) was pulled and admitted (additive-only; no existing snapshot was modified, per the
  script's own documented guarantee).
- **A real side effect found and corrected immediately**: the scoped run overwrote
  `config/nwr_new_evidence_snapshot_set_v1.json` (a git-tracked catalog/receipt file) wholesale,
  silently dropping the previously-catalogued `combine`/`depth_charts`/etc. entries from earlier,
  unrelated dataset pulls -- the script's catalog output is NOT additive/merging across scoped
  runs. Reverted the file to its committed state immediately (`git checkout --`) before it could be
  committed. This is disclosed here as a real, concrete tooling caution for any future refresh
  attempt: a safe full refresh must run every dataset in one invocation (the script's own default),
  not a subset, or must have its catalog-merge behavior fixed first.
- Did **not** attempt the much heavier full 2012-2025 stats re-pull or the downstream
  admission/backtest/candidate-generation run this pass, given real time budget constraints across
  the rest of this continuation's scope and the fact that the resulting candidate would still be
  `RESEARCH_ONLY_GOVERNANCE_PENDING` -- it would need explicit owner review and a new governance
  approval receipt before `_ensure_redraft_projection_seed` would ever install it, exactly matching
  the existing two-file (source + approval) gate, unchanged. **Nothing was installed, signed, or
  promoted.**
- News/alerts: reconfirmed no existing refresh mechanism exists for the specific file the app
  reads (`C:\NWR_DRAFT_DAY_TOOLS\KHA_FINAL_CHEAT_SHEET.csv`); checked
  `data_refresh_orchestrator_service.py` (the closest candidate) and confirmed it is a
  Dynasty-mode orchestrator (sleeper/dynastyprocess/nflverse/cfbd) with no path to this Redraft-
  specific file.

**Exact remaining blocker, named precisely**: producing a genuinely fresher admitted projection
bundle requires (1) a full, all-datasets nflverse re-acquisition (safe, existing, no credentials,
but real runtime cost -- untested this pass), (2) re-running the existing admission/backtest
pipeline against it (produces a `RESEARCH_ONLY_GOVERNANCE_PENDING` candidate, not an installed
bundle), and (3) **explicit owner review + a new governance approval receipt** before that
candidate could ever become the active seed -- an authorization this session cannot self-issue.
News/alert freshness has no existing refresh pathway at all; refreshing it depends on whatever
external process the owner uses to regenerate that specific file.

**Status: current-data readiness remains BLOCKED** (projections) and **LIMITED** (news) -- not
resolved this pass, but the exact path, the exact real blocker, and one real, verified, safe
intake step are now on record, not merely a repeated staleness label.

### 4. QB-now vs RB-now/later-QB counterfactual — completed with a clearly-labeled controlled
### reproduction (not the owner's live board)

The Pass V4.2 pick-47 state is reclassified per section 1 above. This pass found, across two
different random seeds in the same real 12-team simulation, that **elite/top-tier QBs are
consistently drafted by opponents well before round 4 in this model's own CPU market behavior** --
a real, disclosed finding in its own right (the owner's "wait until pick 47" framing does not
survive contact with how aggressively this simulated market drafts QBs). Rather than force pick 47
or hand-fabricate player availability, found the actual real point in the same simulation where a
genuinely comparable decision exists: **overall pick 23 (round 2.11, 12-team, real simulated draft
state, clearly labeled here as a constructed reproduction chosen because both alternatives are
genuinely available -- not the owner's own board)**.

At that real, live-queried state (owner roster: Christian McCaffrey only), the real DecisionBundle
showed:
- **Caleb Williams (QB, real overall rank ~20)**: Pick Score 100.0 (the single highest of every
  real candidate), Team Score After 100.0, equity gain +18.00pp, **action: TAKE NOW**, and a real
  Make-It-Back of only **14%** if the owner waits -- a genuine, high, disclosed risk of losing him.
- The best real non-QB alternative (Chris Olave, WR): Pick Score 91.7, Team Score After 99.2 --
  real numbers, not fabricated, showing QB-now edging out WR-now by a real (if modest) margin in
  this specific state.
- A real fallback QB tier exists in the same state (Bo Nix, real rank ~26, Make-It-Back 32%,
  action GOOD VALUE) -- the "later QB tier, with fallback" the owner's scenario described is
  genuinely present here, just not required by the numbers in this particular reproduction.
- **The engine's own real, unforced answer here is "take the QB now," not "wait on QB"** -- the
  opposite of what the owner's original hypothesis assumed, reported exactly as computed. This is
  not a manufactured winner for either side of the question; it is what the real machinery produced
  at a real, honestly-chosen state.
- Verified: candidate insertion affects the correct branch (Williams's own forced-candidate
  completion differs numerically from Olave's, as expected); later availability is not asserted as
  certain (14%/32%, not 100%); Cost of Waiting is a separate disclosed field, never folded back
  into Pick Score itself (confirmed by code structure in an earlier pass), so timing risk is not
  double-counted by construction.

**Status: VERIFIED** as a real, honest, controlled-and-labeled completion of the counterfactual
requirement -- explicitly not identical to "the owner's Maye/Stafford board," and reported as such.

### 5. Superflex — repaired via the existing generic pattern, not just constrained

Traced actual CPU decision *dependencies* (reading `_forced_position`, `_roster_need_adjustment`,
and `_roster_candidate_allowed` directly), not merely searching for the literal word "Superflex."
Found that the exact same generic pattern already proven and reused for RB/WR/TE's shared FLEX
slot (`have < required + shared-slot-count` → a real need signal) was simply never extended to QB
+ Superflex, even though the mechanism was clearly designed to generalize this way. **Repaired all
three call sites by reusing that identical pattern** -- not new logic, not a redesign:

- `_forced_position`: a configured Superflex slot now counts toward the real QB deadline-forcing
  requirement.
- `_roster_need_adjustment`: QB1-filled-but-Superflex-open now returns the same real -6.0 need
  signal RB/WR/TE already return for an open FLEX slot.
- `_roster_candidate_allowed`: the real legal QB cap is now `qb + superflex + 1` (preserving the
  existing +1-backup allowance on top of the real Superflex count).

**Zero-blast-radius for every 1QB league proven, not assumed**: `profile.roster.superflex`
defaults to 0 everywhere, so each changed expression algebraically reduces to its exact pre-fix
form; 3 new unit tests assert the 1QB branch is unchanged alongside the new Superflex-league
assertions. The owner's own real upcoming league is explicitly 1QB/no-Superflex, so this repair
carries zero risk to the build the owner will actually use.

**Live-proven at the integration level** (the real Monte Carlo engine, not just the source code): a
controlled A/B for a genuinely contested mid-tier QB showed **zero difference** between a 1QB and
Superflex league before this fix (the Pass V4.2 finding) and now shows the Superflex league
producing materially **lower** survival (0.0167 vs 0.1167 in one real run) -- the correct real-
world direction. 1 new integration test locks this in.

This is disclosed as a versioned behavior change to CPU candidate-selection policy for Superflex
leagues specifically (never for 1QB leagues, proven above) -- it does not inherit the frozen Team
Score/Championship Equity/Pick Score formulas' historical validation (those were not touched), and
it only changes which candidates the CPU treats as needed/legal, the same category of change the
existing need-aware-shortlist fix from an earlier pass already established as safe to iterate.

**Status: VERIFIED — repaired**, not merely constrained/labeled. Superflex simulation timing
metrics were never disabled or hidden; they now produce real, differentiated, correct-direction
output for the leagues that configure the slot.

### 6. Resource/screenshot loop — no new tooling, existing limitation confirmed precisely

Searched this repository for an existing Playwright/e2e browser-test setup or native (Tauri-
driver/UI-Automation) desktop-automation path before doing anything else this section --
confirmed none exists (only unrelated internal `node_modules` dependency files matched a
"playwright" search). Per the explicit instruction not to build another automation framework, none
was built. Chrome MCP (`javascript_tool`, DOM/`aria`-state-checked interaction) remained the only
available interaction path and was reused, with its evidence explicitly classified below.

Memory was inspected before every stack launch this continuation (recorded inline at each
decision point); the lean Vite+standalone-backend stack was used for the pick-correction
verification, then fully stopped (both PIDs identified by command line before being stopped,
ports confirmed clear via `netstat` afterward) before the Tauri build was attempted, keeping to one
verification stack at a time throughout.

### 7. The actual Tauri build — attempted, and real, meaningful, process-level evidence obtained

With ~2.3–2.5 GB of headroom available (the best this session), attempted a fresh
`npm run tauri:redraft` against this continuation's actual final commit. The Rust build completed
in 1.10s (an existing, valid incremental-compile cache from earlier same-day testing -- none of
this continuation's changes touch Rust/Tauri-side code, only TypeScript/Python, so no Rust
rebuild was actually required for them to take effect).

**Real, verified via direct OS process inspection (not assumed)**:
- `nwr-redraft-war-room.exe`, built from this exact worktree, launched successfully.
- A genuine embedded `msedgewebview2.exe` **native window process** spawned as its child, using
  `--user-data-dir="C:\Users\codex-agent\AppData\Local\com.ninerswarroom.redraft\EBWebView"` --
  the OWNER'S REAL app identity/data directory, confirming this is the same application identity
  the owner's actual installed shortcut would use, not a separate throwaway build.
- A real backend child (`run_nwr_desktop_api.py --port 0 ...`) auto-spawned by the Tauri binary
  itself with its own internal startup handshake -- confirming the real owner launch path does not
  require the manual stdin-credential workaround this session's standalone testing has needed.
- The frontend this window loads is served by the same Vite dev server (port 1422) whose source
  reflects this continuation's actual current commit -- the same frontend already
  FUNCTIONAL_DOM_VERIFIED extensively earlier this pass via a plain browser tab against that
  identical bundle.

**A precise, structural (not transient) limitation, disclosed exactly**: Chrome MCP's screenshot
tool is scoped to Chrome browser tabs only (`computer.screenshot` takes a `tabId`) -- it cannot
capture a native, non-Chrome desktop window like this one under any circumstances in this
environment, regardless of the "0 width" bug observed elsewhere this session. Pixel/visual
confirmation of the actual rendered window was therefore never achievable with the tools available
here, not merely blocked by a fixable bug. This is stated precisely rather than implied as luck-
dependent.

Shut down cleanly and completely afterward: every process this launch's chain was traced to (the
Tauri binary, both embedded webview children, the npm/node/tauri.js/vite wrapper chain, and its
Python backend child -- 8 PIDs, each individually identified by command line before being
stopped) was stopped; `netstat` confirms port 1422 is clear. Noted honestly: several additional
`msedgewebview2.exe` processes remain running system-wide after this cleanup -- consistent with
WebView2's own shared-runtime background-process behavior (a normal, expected Windows/WebView2
characteristic, not unique to this app) and/or other unrelated applications on this machine; none
could be positively attributed to this launch specifically once its own parent process was
confirmed gone, so none were touched, per the explicit instruction never to stop processes that
cannot be positively identified as belonging to this mission.

**Status: build+launch VERIFIED via real process-level evidence** (the exact final commit, the
exact real frontend, the exact real owner app identity). **Visual/pixel confirmation: structurally
NOT_VERIFIED** in this environment/toolset -- disclosed as a tooling ceiling, not a skipped step.

### FUNCTIONAL_DOM_VERIFIED classification (all continuations, restated precisely)

Every interaction this mission has performed via `javascript_tool` (`.click()`/DOM-state calls,
checked against real `aria-pressed`/text-content changes each time) is, and remains,
**FUNCTIONAL_DOM_VERIFIED**: confirmed real application behavior through the real interface
elements and real backend responses, but never `POINTER_VERIFIED` (no real mouse/pointer events
were dispatched -- the Chrome MCP `computer` tool's coordinate/ref-based clicks did not register
correctly this entire session, confirmed by repeated direct tests), never `VISUALLY_VERIFIED` (no
real screenshot evidence exists this session), and never `DESKTOP_VERIFIED` (browser-only, except
for the process-level Tauri evidence in section 7 above, which is its own distinct, narrower
claim). This report does not relabel any DOM evidence as visual or desktop verification anywhere,
including the 8/12/16-team checks and the pick-correction verification in this same continuation.

### Updated test/regression evidence

- `tests/test_redraft_draft_room_v1_service.py` + `tests/test_shadow_numeric_authorities_service.py`:
  80/80 pass (3 new Superflex unit tests + 1 new Superflex integration test this section, on top of
  the prior continuation's tests).
- Desktop: 125/125 vitest pass (unchanged this continuation -- pick correction is UI/state wiring,
  no new pure functions needed); `npm run typecheck` clean.
- Full backend regression across `decision_bundle`/`desktop`/`redraft`/`shadow_numeric`: **353
  passed, 8 failed** -- the same 8 pre-existing, unrelated failures as every prior continuation
  this session (4 documented `test_desktop_application_api.py` baseline + 4 in files never touched
  this session: rookie projection manifest bytes, dynasty bridge, combined-snapshot validation,
  Windows shortcut installer).
- Resource state: the lean Vite+backend stack used for pick-correction verification was fully
  stopped (both PIDs confirmed by command line); the Tauri build's full 8-process chain was fully
  stopped (each PID confirmed by command line); port 1422 confirmed clear via `netstat` at the end
  of this continuation. No config/data files were left modified by the current-data investigation
  (the one accidental catalog overwrite was reverted before it could be committed).

### Final separate verdicts, as requested

- **WORKFLOW**: PASS -- every scenario exercised this continuation (pick correction's full 10-step
  flow, the Superflex A/B, the pick-23 QB/RB counterfactual, the real Tauri build/launch/shutdown)
  completed correctly with real data; nothing BLOCKED.
- **LAYOUT**: mostly COMPLETE -- pick correction (the last major implementation gap from prior
  passes) is now closed; full pixel/viewport verification remains structurally unavailable in this
  environment (not a layout defect).
- **NUMERIC TRUST**: SUPPORTED, broadened further -- Superflex is now a real, tested, working
  behavior (not just a disclosed gap); the QB-now/RB-now counterfactual is genuinely completed with
  an honest, labeled, non-manufactured answer. LIMITED remainder: the underlying bench-tier Team
  Score saturation (a frozen-formula property, not fixed, correctly not conflated with the Pick
  Score disclosure fix) and the broader per-metric result-status taxonomy beyond Pick Score/DQ/
  Make-It-Back.
- **PROJECTION FRESHNESS**: BLOCKED -- 2026-08-08, confirmed live; the real path to a fresher
  bundle is now precisely named (full nflverse re-acquisition → re-run admission pipeline → owner
  governance approval), one real safe step of it demonstrated working, but the bundle itself is
  unchanged and correctly still requires owner authorization this session cannot self-issue.
- **ADP FRESHNESS**: CURRENT -- unchanged, real, working, in-app refresh (confirmed end to end in
  an earlier pass).
- **NEWS FRESHNESS**: LIMITED -- unchanged; a real local file, no in-app or scriptable refresh
  pathway exists for it in this codebase.
- **OWNER DESKTOP VERIFIED**: PARTIAL -- build and launch mechanics verified via real, direct
  process-level evidence against this continuation's exact final commit and the owner's real app
  identity; visual/pixel confirmation is not achievable with the tools available in this
  environment (a disclosed tooling ceiling, not a skipped or failed check).

**Overall verdict: `YELLOW_OWNER_FEEDBACK_PARTIALLY_CLOSED`.**

Outstanding canonical requirement IDs at the close of this continuation: **B remainder** (a unified
cross-metric result-status taxonomy beyond Pick Score/DQ/Make-It-Back), **the bench-tier Team
Score saturation itself** (distinct from the Pick Score disclosure fix -- a frozen-formula property,
disclosed, not altered), **current-data readiness** (a full nflverse re-acquisition + admission
re-run + owner governance approval, none of which this session can complete alone), **F** (full
pixel/viewport matrix -- structurally unavailable, not merely unattempted), **visual confirmation
of the real Tauri window** (structurally unavailable with the tools in this environment).

Tested commit at the close of this continuation: `e307dba6` (the Superflex fix commit, the last
commit made this pass) on `work/nwr-draft-upgrade-hq-v1-20260903`. Owner launch path, verified this
pass via real process inspection: the desktop shortcut → `npm run tauri:redraft`-equivalent → the
Tauri binary → its own auto-spawned backend + the Vite-served (or, for a production build, bundled)
frontend → `#/draft-room-v2` → the owner's real data root at
`AppData\Local\com.ninerswarroom.redraft` (this continuation's own Tauri launch used that exact
real user-data directory, confirmed live, not assumed).

No push, merge, deployment, or model retraining performed this continuation either. All work is in
local commits on `work/nwr-draft-upgrade-hq-v1-20260903`.

## Pass V4.4 -- controlled projection refresh, cross-metric status contract, bench/news precision

Continuation from `9dfc2f78`, under a narrow owner authorization to acquire-and-build a candidate
(never install), finish the shared status requirement, and disclose bench/news precisely.

### 1-3. Controlled candidate refresh (acquire -> build -> compare, nothing installed)

Used the **existing** tooling only, against a **separate candidate location** the whole way --
never the git-tracked catalog, never `C:\NWR_SHARED_DATA\source_snapshots` for the build output,
never the active bundle at `docs/hq/model/nwr_redraft_2026_rookie_projection_candidate_v1_20260809`.

- **Acquisition**: `acquire_nflverse_new_evidence_v1.py --datasets player_stats_seasonal
  --skip-client-archive --snapshot-root <isolated temp root> --catalog-output <isolated temp
  catalog>` (never the tracked `config/nwr_new_evidence_snapshot_set_v1.json` -- avoids the
  previously-found scoped-catalog-overwrite bug by construction, not by care). Result: a real new
  snapshot, `20260907T042341Z-b4cb36c421e9`, 14/14 seasons (2012-2025) admitted.
- **Builder parameterized, not redesigned**: `build_redraft_2026_projection_admission_packet.py`
  hardcoded its two input snapshot directories inline. Added optional
  `--player-snapshot-dir`/`--stats-snapshot-dir` overrides (default = the exact existing
  2026-08-08 literals) so the **same, unchanged** feature engineering / temporal backtest /
  candidate-construction code can run against a different snapshot. Verified the default path is
  still byte-identical (two default-args runs differ only in `generated_at`/output-dir-name
  fields, confirmed field-by-field).
- **Real bug found and fixed in passing**: the packet's own `PROJECTION_SHA256.json` /
  `NWR_DATA_GOVERNANCE.json` recorded `snapshot_aggregate_sha256`/`retrieved_at_utc` as **hardcoded
  literals** matching the 2026-08-08 snapshot regardless of which snapshot directory was actually
  loaded -- so pointing the builder at a different snapshot (exactly what this pass does) would
  have silently mis-reported its own provenance. Fixed by reading each snapshot's own real
  `COMPLETION_MANIFEST.json` instead (every acquired snapshot carries one); proven byte-identical
  for the default/unchanged case by directly comparing to the literals it replaced.
- **Old-vs-new comparison** (baseline = builder run against the existing 2026-08-08 snapshot pair;
  candidate = same builder against the new stats snapshot, same players snapshot):
  - Baseline: 530 ranked rows. Candidate: 532 ranked rows.
  - **529 of 530 shared players: byte-for-byte identical `projected_points`.**
  - **1 changed**: Caleb Williams, QB, 315.18 -> 315.68 (+0.5 pts).
  - **2 added**: Bo Melton, Jack Westover -- both depth-only, `GOVERNANCE_PENDING`/
    `MODEL_VALIDATED_REVIEW_ONLY` like every other row, not top-of-market movers.
  - Blocked-row count: 380 -> 378 (exactly the 2 newly-admitted players).
  - `PROJECTION_VALIDATION.csv` (temporal backtest): every metric shifted by tiny amounts (max
    observed: 0.24 MAE points on one position/season cell, `player_count` off by 1 in one cell) --
    consistent with 2 more rows entering some season's backtest cohort, not a methodology change.
  - Rookie coverage: 0 in both (this veteran-only builder never covers rookies; unaffected either
    way -- that lane is the separate rookie pipeline, untouched this pass).
  - Identity coverage: unchanged (910 rows) -- expected, since only the stats snapshot was
    swapped, not the players/identity snapshot.
  - **Verdict: `NO_MATERIAL_CONTENT_CHANGE`.** The fresher stats pull does not move a single
    top-of-market projection; this is not being presented as a refreshed player outlook.
- **Candidate artifact**: `CANDIDATE_PROJECTION_SNAPSHOT.csv`,
  sha256 `07d379dc5b2fa5c1056b8d07b92fdfb1c7a23732227db34bef5a7aaa960ece03`, held only in an isolated
  temp directory (`%LOCALAPPDATA%\Temp\nwr_candidate_refresh_20260907\packet_candidate_new_20260907`),
  never copied into the repo or the active bundle location.
- **Installation boundary, proven empirically, not just asserted**: ran the real engine loader
  (`load_projection_snapshot`) directly against this candidate CSV. Every one of its 532 rows
  carries `source_status=GOVERNANCE_PENDING`, which is not in `ADMITTED_SOURCE_STATUSES` --
  the loader reports zero rankable rows for this candidate (and, confirmed identically, for a
  fresh rebuild of the CURRENT baseline through the same raw path). This candidate **cannot** be
  installed or rendered anywhere without a real governance status-elevation + the separate
  rookie-combine step that produced the active `GOVERNED_COMBINED_608...` bundle -- out of this
  pass's narrow authorization, and not attempted. No approval receipt was fabricated, renewed, or
  reused.
- **The FFA candidate** (`C:\NWR_HISTORICAL_DATA\FFA_OFFICIAL\...`): untouched this pass, not read,
  not referenced by the builder. Remains exactly what it was: an available separate-source lead,
  not an admitted replacement.

### 4. Shared cross-metric result-status contract -- real, additive, tested

New `src/services/metric_status_contract_service.py`: one `MetricStatus` type
(`computation_state` in EVALUATED/PENDING/BUDGET_LIMITED/UNSUPPORTED/MISSING_INPUT/ERROR;
`genuine_zero`; `tied_no_spread` (nullable); `validation_domain`; `source_freshness`;
`data_coverage`) -- three independent axes, never collapsed into one label. Wired into **both** real
`CandidateBundle` construction sites (`decision_bundle_service.py`'s live path,
`historical_decision_state_service.py`'s replay path), through `desktop_facade.py`'s
`_decision_bundle_payload` (`metricStatus` per candidate, camelCase-safe -- keyed by fixed field
names, not data values, so the known `public_json_value` key-mangling footgun does not apply), the
`@nwr/contracts` TS interface, and into the frontend: `PlayerDrawer`'s six primary stat tooltips,
and the Suggestions/Compare tables' Pick Score and Cost-of-Waiting cells.

- **Covers 6 of 8 named metrics** with the full three-axis contract: Player Score, Team Score,
  Championship Equity, Cost of Waiting, Make-It-Back, Pick Score.
- **Real, previously-silent distinction surfaced**: Cost of Waiting silently falls back to the
  plainer Pick-Score-embedded estimate whenever the richer per-candidate V2 evaluation doesn't
  cover a candidate (its own documented "no other candidate to compare against" skip condition) --
  proven live via the real HTTP decision-bundle endpoint (see below) and now disclosed via
  `dataCoverage: "Full Cost-of-Waiting-V2 evaluation"` vs `"Fallback: ..."` instead of looking
  identical either way.
- **Remaining, precisely-named gap**: Raw Action Value / expected regret / decision-quality
  percentile (`decision_bundle_service_v2.py`) already have their own real, non-coerced
  `"OK"`/`"UNAVAILABLE: <reason>"` disclosure -- **not yet** mapped into this shared vocabulary.
  This is a real time-boxing gap in this pass, not a missing-evidence gap; the underlying
  disclosure already exists and is genuine, just not unified with the other six yet.
- **Result properties never coerced**: a missing Player Score is `MISSING_INPUT`, never a silent 0;
  a real computed 0 is `EVALUATED` with `genuine_zero=true`; `tied_no_spread` reuses the exact same
  fact the earlier Pick Score fix already computes, never a second independently-derived flag.
- **Tests**: 12 new unit tests (`test_metric_status_contract_service.py`), 5 new integration tests
  in `test_decision_bundle_service.py` (multi-axis independence, missing-input non-coercion, the
  Cost-of-Waiting fallback distinction, tied-flag parity with the existing disclosure). All 68
  pass; the pre-existing 4-file/8-test unrelated baseline re-checked and unchanged (93 passed, the
  same 8 named failures, byte-identical to the documented baseline).
- **Verified through the real rendered/HTTP path, not just unit tests**: started the standalone
  backend against the existing isolated practice root (`nwr_gui_test_root`, port 18742, real
  `X-NWR-Desktop-Token` auth), called the live `POST
  /api/v1/redraft/draft/<profileId>/decision-bundle` endpoint against a real in-progress practice
  draft (pick 23, owner's turn), and confirmed `metricStatus` renders correctly end to end --
  `EVALUATED`/`source_as_of=2026-08-08`/the real Cost-of-Waiting evidence-quality note all present
  in the actual JSON response. Backend cleanly stopped afterward; port 18742 confirmed clear (only
  transient `TIME_WAIT` entries from the curl calls, no listener).
- Frontend: desktop-wide `npm run typecheck` clean, `npm run test` 125/125 passed (no regression
  from the prior 125-test baseline).

### 5. Bench-tier Team Score saturation -- precisely traced, not assumed, not retuned

Traced the **actual active computation**, not one starter-only feature in isolation:
`team_score()` (V1, live), `team_score_v2_multi_league_service.py` (V2), and
`championship_equity()` all call the same `optimal_starting_lineup_value()` for **both** the
target roster and every comparable/opponent roster in their population. That function sums
`p.value` for only the players `_select_starting_lineup` actually selects as starters -- a
rostered bench player who is not selected contributes **exactly 0** to the value being compared.
This means bench depth is invisible to **all three** of Team Score V1, Team Score V2, and
Championship Equity alike, by the same shared root cause, not three separate gaps.

A different, real function -- `roster_composition_report()` / its `bench_contingency_value` field
-- **does** compute real bench value today. Confirmed by direct grep: it is **not called from
`desktop_facade.py` or any frontend file** -- it exists in the service layer only and is not
rendered anywhere in the live product. So today the owner has zero live visibility into bench
depth value anywhere in Draft Room V2, not merely a saturation ceiling on one visible metric.

This is recorded as a real, frozen-formula limitation in the ledger (item 2, unchanged from the
prior pass) -- not retuned, not patched with an invented bench bonus.

### 6. News freshness -- precisely restated

Active artifact: local file at `C:\NWR_DRAFT_DAY_TOOLS\KHA_FINAL_CHEAT_SHEET.csv` (overridable via
`NWR_KHA_CHEAT_SHEET_PATH`). Confirmed directly: the CSV carries `current_alert`/
`current_alert_severity` columns per player but **no per-row/per-alert timestamp column at all** --
the file's own mtime is the *only* freshness signal that exists (`snapshotGeneratedAtUtc`/
`snapshotAgeHours`, `STALE_AFTER_HOURS=24.0`). As of this pass, that file is **~99 hours old**
(stale). "Existing way to select/import a replacement" is precisely: replace the file at that path,
or point `NWR_KHA_CHEAT_SHEET_PATH` at a different one before launch -- there is no in-app picker or
import flow for this source, and none was added. An absent alert in this snapshot is not evidence
of no real news; the UI's stale-badge already says so and this pass did not change that wording.

### 7-8. Final build and handoff for this pass

Application code changes this pass: `scripts/build_redraft_2026_projection_admission_packet.py`
(parameterized + provenance fix), `src/services/metric_status_contract_service.py` (new),
`src/services/decision_bundle_service.py`, `src/services/historical_decision_state_service.py`,
`src/application/desktop_facade.py`, `desktop/packages/contracts/src/index.ts`,
`desktop/apps/redraft/src/draft-room-v2.tsx`, plus new/updated tests. `docs/model_v4/*` remains the
same pre-existing, untouched dirty state from session start.

- Backend: scoped baseline re-check 93 passed / 8 pre-existing unrelated failures (identical names
  to the documented baseline); new/changed test files (`test_decision_bundle_service.py`,
  `test_historical_decision_state_service.py`, `test_desktop_http_api.py`,
  `test_decision_bundle_explanation_service.py`, `test_metric_status_contract_service.py`) all
  green, 68/68. A full unscoped `tests/` run was started, then deliberately stopped as
  disproportionate to what changed this pass (per the owner's own instruction against repetitive
  full-suite reruns) once the scoped, relevant evidence above was in hand.
- Frontend: desktop-wide typecheck clean, 125/125 vitest.
- Live HTTP-level verification of the new `metricStatus` payload performed and torn down cleanly
  (see section 4 above) -- FUNCTIONAL_DOM/HTTP_VERIFIED, not a native-process or visual check.
- **No native Tauri process/window re-launch performed this pass** -- the launcher/process-spawn
  code itself is untouched since the prior pass's real process-level verification (recorded above,
  same continuation); only backend Python content changed this pass, and that was verified through
  the isolated HTTP harness instead. Visual/pixel confirmation remains the owner's own, for the
  reasons already recorded (structural tooling ceiling in this environment).
- No push, merge, deploy, or model retraining performed. No receipt renewed, no timestamp altered,
  no new source silently admitted. All work is in local commits on
  `work/nwr-draft-upgrade-hq-v1-20260903`.
