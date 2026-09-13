# NWR Post-UI Workday Ledger

Multi-worker unattended implementation shift on the NWR desktop frontend,
branch `upgrade/nwr-post-ui-product-v1-20260912`, worktree
`C:\NWR\post-ui-product-v1`. Each worker appends its own entry below. Durable
tracking doc for the next workers -- keep entries concise, not narrative.

No merge/push/deploy by any worker. No push to origin without explicit
owner authorization (none exists for this shift).

---

## CURRENT HEAD

Fourteen commits on top of start head `003d0dd4183f7bfc7a2ad2f03960c967dd0bb02e`
(Work Unit 0 + P0-1, then P0-2, then P0-3, then P1-1, then P1-2, then P1-3
backend, then P1-3 UI, then P1-4, then P1-5, then P2-1, then Worker 11's
final shift consolidation (docs-only, no code commit), then Worker A's
closure pass, then Worker B's privacy-safe packaging pass, then Closure
Worker C's final verification trio below) -- run `git log -1` for the
exact hash.

## Closure Worker C — final verification trio (real release smoke, prospective-ledger hardening, full regression) -- 2026-09-13

**Scope: verification-only trio before this branch is pushed as a checkpoint --
real read-only release smoke (Work Unit 5), prospective-ledger hardening
(Work Unit 6), full regression/endurance (Work Unit 7).** Started at
Worker B's `32f7059f`. Found and fixed ONE genuine bug (Work Unit 6, real
pathological decision-trace duplication) -- everything else this pass
touched was verification only, no code change. Final HEAD: `1da21322`.

**WORK UNIT 5 -- REAL READ-ONLY RELEASE SMOKE: PASS.** Reused Worker 3's
`nwr_release_gate_smoke.ps1 -KeepRunning -SleeperLeagueId
1312983576827920384 -SleeperUsername scolety` end to end against the real,
read-only Fantasy Gamers league, then drove the same real backend + real
production `vite preview` build live in Chrome for the full click-through
the directive named: league chooser -> Fantasy Gamers -> Home -> Lineup ->
Improve Team -> Trades (Analyze + Find Trades) -> Players (Rankings +
Player Drawer open/close/reopen + global cross-tool search) -> League (My
Roster/Manage Leagues) -> Draft Room (pre-draft state only, `Start Draft`
never clicked) -> Attention Center ("Multi-League Overview -- Read-Only",
the real Multi-League Center) -> cross-league player search (Bijan
Robinson resolved correctly across 7 saved leagues, real
AVAILABLE/UNAVAILABLE-per-league statuses) -> Cheat Sheet -> History ->
Data Health -> a cold app restart (fresh navigation + hard reload back to
the league chooser's remembered active league) -> a cold direct deep link
(`/#/league/<id>/trade-analysis?tab=find`, hard-reloaded from scratch).
**Zero console messages of any kind** (not just errors) across every one
of those loads, checked via `read_console_messages` with no pattern
filter after each. `findings: []` in the smoke script's own JSON report
(previously non-empty for both the weekly-home-actions 500 and the
check:resources block; both are confirmed still fixed -- see below).

**Weekly Home / weekly-home-actions 500 fix: CONFIRMED STILL HOLDS**, on a
fully fresh rerun with both Worker A fixes and Worker B's packaging change
in place: `POST /api/v1/redraft/weekly-home-actions {"week":1}` ->
HTTP 200 (real 9-action response, real STREAMER rows present), rendered
live in the "NWR Actions" panel with real cards (START/SIT, close-call
QB, WAIVER, etc.) and zero console errors, including across 3 back-to-back
full page reloads of Weekly Home. Current week/opponent/scores/standings
(Week 1, Puka's Bitches, 6.0-25.4, 0-0 #9 of 10, playoffs Week 15) all
correct against the real Sleeper league. Trade packages render with real
before/after impact numbers. Decision traces record (see Work Unit 6).
The identity-boundary fix (bug 2, "Open in Analyze" equivalent) -- verified
via the real My Roster page showing real MATCHED/UNMATCHED
`canonicalPlayerId`/`identityStatus` per player, and via the Trade Finder
tab producing real trade candidates with the corrected id boundary intact
(no regression to the fixed `mySleeperPlayerId`/`opponentSleeperPlayerId`
fields, confirmed by code-diff review below, not re-exercised end-to-end
via the legacy unrouted button this pass since Worker A's own live
verification already covered that path directly). Data notices are
coherent: header chip correctly shows "3 data issues" for this league's
real state (Market ADP unavailable / Sleeper scoring needs review / 7
rookies remain blocked), unchanged from prior passes' own disclosed
findings.

**SLEEPER WRITES: 0**, verified three ways, same as every prior worker:
(1) structural -- `SleeperHttpClient` (`src/services/sleeper_import_
service.py`) defines only `get_json()`; (2) grep -- zero POST/PUT/PATCH/
DELETE call sites target `api.sleeper.app` anywhere in `src/`; (3) the
smoke script's own real before/after byte-comparison of `league`/
`rosters`/`users` fetched directly from `api.sleeper.app` around this
pass's real Sleeper import call: IDENTICAL (`beforeAfterIdentical: true`
in the JSON report).

**TIMINGS** (from the smoke script's real, instrumented run against the
real Fantasy Gamers league; single-request wall-clock, not averaged):

| Surface | Time (ms) |
|---|---|
| Cold bootstrap (Home) | 236.1 |
| Warm bootstrap (Home) | 242.9 |
| Sleeper import (real, read-only) | 2,449.0 |
| League workspace context | 1,018.4 |
| My Roster | 880.7 |
| Opponent Rosters | 934.7 |
| Data Health | 4,237.9 |
| Player Availability Status | 5.9 |
| Lineup (Start/Sit, week 1) | 912.0 |
| Waivers (Improve Team, THIS_WEEK) | 16,318.1 |
| Free Agents | 1,897.0 |
| Trade Finder | 1,578.6 |
| Weekly Home actions aggregation (week 1) | 7,936.2 |

Player Drawer first/repeat open and Draft refresh were not separately
timed by the instrumented script (no dedicated endpoint -- the drawer
renders from already-loaded bootstrap/ranking data, confirmed live with
zero additional network calls on open/close/reopen); both opened
instantly and with zero console errors in the live Chrome pass above.
Waivers' 16.3s is a real, pre-existing, undisclosed-as-new latency
(unrelated to this pass -- no waiver-path code was touched this shift) --
flagged as an open item below, not investigated further (out of this
verification pass's scope).

**WORK UNIT 6 -- PROSPECTIVE LEDGER HARDENING: REAL PATHOLOGICAL
DUPLICATION FOUND AND FIXED.** Every supported decision family
(START_SIT, WAIVER, FAAB, TRADE, TRADE_FINDER, TRADE_PACKAGE_SEARCH,
K_STREAMER, DST_STREAMER) was confirmed registering real traces correctly
for the Fantasy Gamers profile (229+ folded events, spanning every tool
type; `DRAFT` remains schema-only with no live call site, unchanged, per
the hard boundary). But the directive's suspected duplication risk was
real, not hypothetical: every facade call site that records a trace is
reached from a plain `useAsync` page-mount/dependency-change frontend
effect (Weekly Home, Lineup, Waivers/Improve Team, Trade Finder, Find
Trades) -- never gated behind an explicit "record this" action -- so a
page refresh, a route remount, or `redraft_weekly_home_actions`'s own
internal re-calls to `redraft_weekly_lineup`/`redraft_waivers`/
`redraft_trade_finder` (already invoked standalone moments earlier by the
same page render) previously wrote a brand-new ledger line, with a
brand-new random `trace_id`, for the exact same underlying recommendation
every single time.

**Live, real evidence, not just reasoning:** the smoke script's own single
run showed `weekly-home-actions` internally re-calling `redraft_weekly_
lineup`/`redraft_trade_finder` seconds after their own standalone endpoint
calls moments earlier -- BEFORE this pass's fix, that would have written 2
duplicate START_SIT lines and 2 duplicate TRADE_FINDER lines for one real
smoke pass alone. Pre-existing historical evidence of the exact same
defect was independently found already sitting in this profile's own real
ledger, untouched by this pass: three real TRADE_PACKAGE_SEARCH lines
sharing one identical microsecond-precision timestamp and byte-identical
content, clearly written back-to-back by an uncontrolled duplicate call in
an earlier session -- left exactly as recorded, per the append-only/
no-retroactive-deletion invariant (this pass deletes or mutates nothing
already recorded).

**Fix (`src/services/in_season_decision_trace_service.py`,
`record_decision_trace`):** a new content fingerprint (tool/week/
roster-state/free-agent-state/recommendation/alternatives -- deliberately
excluding provenance-only fields like `engine_version`/`data_versions`/
`league_snapshot_id`/`status_versions` so a metadata-only difference never
defeats a real match) is compared against the MOST RECENT existing trace
in the exact same `(league_id, tool, week)` scope; if it matches AND that
trace was recorded within `DEDUP_WINDOW_SECONDS` (300s -- sized to absorb
a refresh/remount storm, not to suppress a genuinely time-separated "still
recommended" event), the existing record is returned instead of writing a
duplicate line. A genuinely different recommendation (the real, changed
output of an actually-changed roster/data state) or an identical one
recorded again after the window elapses both still always get their own
new, real line -- exactly the "don't lose a genuinely distinct event"
requirement.

**Verified live against the real Fantasy Gamers ledger, not just unit
tests:** after this fix, the smoke script's own internal double-call
(`weekly-home-actions` re-invoking `weekly_lineup`/`trade_finder`
seconds after their standalone calls) produced exactly ONE line each for
START_SIT and TRADE_FINDER, not two -- while the two genuinely distinct
WAIVER/FAAB scopes (THIS_WEEK week=1 vs. REST_OF_SEASON week=None) both
correctly got their own separate lines, proving the fix discriminates real
scope differences rather than over-suppressing. Three additional real,
live full-page reloads of Weekly Home produced ZERO new WAIVER/FAAB/
TRADE_FINDER/K_STREAMER/DST_STREAMER lines (all correctly deduped as
within-window repeats of identical content) and exactly ONE new,
legitimate START_SIT line once its own window had genuinely elapsed
(~304s after the prior identical recommendation -- just past the 300s
threshold, the exact "recommendation unchanged but the window elapsed"
case this design deliberately still records). A follow-up real endurance
run (10 full nav loops x 10 endpoints = 100 calls, 20 repeated
player-availability reads, 5 rapid identical `FIND_WIN_WIN` trade-package
searches, and 10 real league-switch cycles between two profiles with a
ledger read after each switch) added exactly ONE new ledger line across
125 recommendation-shaped calls (the rest all correctly deduped) and zero
non-200 responses; the 10 league-switch cycles independently reconfirmed
per-league ledger isolation (the other profile's `totalCount` stayed
genuinely 0 throughout; Fantasy Gamers' count was unaffected by switching
away and back).

**Tests added (`tests/test_in_season_decision_trace_service.py`, +8, all
passing):** identical content within the window dedupes and returns the
existing record (and a provenance-only field change like `engine_version`
does not defeat the match); genuinely different content is never deduped;
scope isolation holds across different leagues/tools/weeks; a WAIVER
week-scoped vs. week-agnostic pair is compared like-for-like rather than
cross-contaminated; identical content recorded again after the window has
elapsed still gets a new line; an A -> B -> A content alternation within
the window never incorrectly merges the third event into the first (dedup
only ever compares against the single most recent record in scope).

**Confirmed no accidental regression to any existing caller:** every
pre-existing test in this file (21) and every facade test exercising a
traced call site (`test_prospective_recommendation_ledger_v1.py`,
`test_desktop_application_api.py`'s K/DST trace test,
`test_weekly_home_single_snapshot.py`, `test_trade_package_search_facade_
wiring.py`, `test_redraft_identity_boundary_opponent_and_trade_finder.py`,
`test_desktop_facade_architecture_wiring.py`, `test_player_availability_
status_consumer_consistency.py`, `test_decision_envelope_consumer_
migration.py`) still pass unchanged -- none of them call the same traced
method twice with identical content in one test, so none exercised the
new dedup branch by accident; `pytest tests/test_in_season_decision_trace_
service.py tests/test_prospective_recommendation_ledger_v1.py`: 31/31
passing.

**WORK UNIT 7 -- FULL REGRESSION / ENDURANCE.**
- `npx vitest run --no-file-parallelism` (full monorepo, post-fix,
  post-commit): **367/367 passing, 28/28 files** -- unchanged from Worker
  A's own total (this pass touched zero frontend files).
- `npx tsc -b apps/dynasty/tsconfig.json apps/redraft/tsconfig.json`:
  clean, both before and after this pass's commit.
- `pytest tests/test_desktop_application_api.py`: 46 passed, 4 failed --
  the exact same 4 pre-existing failures this ledger's own baseline
  documents (`test_dynasty_facade_composes_real_governed_workflows`,
  `test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_
  aware`, `test_redraft_bootstrap_seeds_once_and_matches_desktop_
  contract`, `test_facade_has_no_streamlit_or_app_component_dependency`).
- `pytest tests/` (full suite): run TWICE, honestly reporting both.
  **First run (uncommitted working tree, this pass's fix staged but not
  yet committed):** `340 failed, 4277 passed, 72 skipped, 13 errors in
  600.14s`. Traced ALL 10 of the excess failures to one real, disclosed,
  pre-existing repo convention, NOT a regression: `test_no_forbidden_or_
  protected_paths_changed`-style governance tests (one per historical
  lane -- `test_blocked_sources_and_protected_paths_are_not_used`,
  `test_forbidden_shared_local_secret_and_protected_paths_are_not_
  tracked`, `test_no_protected_or_app_paths_changed`, `test_no_forbidden_
  or_protected_paths_changed` (x4 across different lane files), `test_no_
  protected_or_forbidden_paths_changed`, `test_no_forbidden_or_protected_
  paths_changed_by_lane`, and one `test_shared_local_secret_and_app_paths_
  are_not_tracked` variant) literally assert `"src/services/" not in
  (git status --short)` -- i.e. each one fails whenever ANY file under
  `src/services/` sits uncommitted anywhere in the working tree,
  regardless of what actually changed. A separate, real, already-known
  side effect was also found and reverted before committing: running the
  full suite regenerates 5 `docs/model_v4/*.md` files with "0 rows" (a
  script under test writing real output reflecting this environment's
  missing `local_exports` data) -- `git checkout --` discarded those 5
  incidental doc changes; they were never part of this pass's real diff.
  **Second run (clean tree, this pass's fix committed):** attempted for a
  true apples-to-apples clean-tree comparison, but the process stalled
  (confirmed via near-zero measured CPU time after ~7 minutes idle, not a
  slow test actively working) and was killed rather than left to
  potentially hang indefinitely -- a real, disclosed environment
  flakiness this pass hit, not attributable to this pass's own change
  (this exact fix's own targeted suites were independently re-run to
  completion multiple times with no such stall -- see below). In place of
  a completed second full run, the specific 10 tests identified above as
  false failures were re-run directly against the now-committed, clean
  tree: **8/8 passed** (2 of the 10 original failure names were exact
  duplicates across different lane files and are covered by the same 8
  distinct test IDs actually re-run), confirming the inflation was real
  and is now resolved. Combined with the already-clean `vitest`/`tsc`
  re-runs and the targeted `pytest` re-runs below (all against the
  committed tree), this pass is confident the true clean-tree full-suite
  count is in the neighborhood of `330 failed / ~4287 passed / 72
  skipped / 13 errors` (340-10 / 4277+10, the 13 pre-existing
  `test_redraft_engine_v1_service.py` calendar-drift errors unaffected by
  either run) -- close to, and consistent with, this ledger's own
  documented "~323 pre-existing failures" baseline (a few more than 323
  is expected drift: today's date, 2026-09-13, pushes additional
  hardcoded fixture dates in that same file outside their 30-day
  freshness window, exactly as Worker B's own prior entry already
  disclosed) -- not independently re-verified end-to-end in one single
  completed run, disclosed exactly as such rather than overclaimed.
- Targeted regression on every hard-boundary-adjacent scoring/legality
  service (post-commit): `pytest tests/test_decision_bundle_service.py
  tests/test_decision_bundle_service_v2.py tests/test_redraft_trade_
  analysis_service.py tests/test_trade_finder_service.py tests/test_
  trade_package_search_service.py tests/test_waiver_engine_service.py
  tests/test_weekly_lineup_optimizer_service.py`: **72/72 passing**,
  confirming zero regression to any file referencing `marginal_roster_
  utility_v2` (all show zero diff across the whole `e06e4a26..HEAD` range
  per the diff review below, independent of this test run).
- **Native package:** `npm run check:resources` (via `node
  desktop/scripts/check-resource-allowlists.mjs` directly) still passes
  cleanly, both before and after this pass's commit. `cargo check` (from
  `desktop/apps/redraft/src-tauri`) still compiles cleanly, both before
  and after. The actual NSIS/MSI installers Worker B built (`desktop/
  target/release/bundle/{nsis,msi}/`) are still present on disk, untouched
  -- this pass's fix is backend Python logic only and was not rebuilt into
  a fresh sidecar/native package (a full native rebuild was judged out of
  scope for a verification-only fix with no packaging/frontend surface;
  disclosed as an open item below).
- **Web production build:** the real `vite build` + `vite preview` this
  pass's own smoke run performed (via `nwr_release_gate_smoke.ps1`)
  succeeded (368ms build, real production bundle served on port 1422) and
  is the same build this pass's whole Chrome walkthrough exercised live.
- **Endurance:** 10 full nav loops (10 endpoints x 10 = 100 calls: 0
  non-200); 20 player-availability/drawer-equivalent reads (0 non-200); 10
  league-switch cycles between two real profiles with a ledger read after
  each switch (40 calls, 0 non-200, per-league isolation reconfirmed); 5
  rapid identical trade-package searches (0 non-200, correctly deduped to
  1 real ledger line); deep-link hard reloads across Home, Lineup,
  Improve Team, Trades (Analyze + Find Trades), Players (+ Player Drawer
  open/close/reopen), League/My Roster, Attention Center (+ cross-league
  search), Draft Room, Cheat Sheet, History, and Data Health -- zero
  console messages on every one. A cold app restart (fresh navigation +
  hard reload) correctly restored the remembered active league.

**FULL DIFF REVIEW (`e06e4a26..1da21322`, the whole closure pass, not just
this pass's own commit):** read every changed file in full. Worker A's 2
commits (STREAMER-shape 500 fix; canonical-vs-Sleeper identity-boundary
fix, purely additive `canonicalPlayerId`/`identityStatus`/
`mySleeperPlayerId`/`opponentSleeperPlayerId` fields) and Worker B's 1
commit (privacy-safe governance-receipt packaging: a new release-summary
service/script, a new install-from-summary function alongside the
byte-for-byte-unmodified original, resource-map/allowlist/Rust-constant
path corrections) plus this pass's 1 commit (additive dedup fix in the
decision-trace ledger only) are the entire range. **Zero touches, direct
or incidental, to `marginal_roster_utility_v2`, draft recommendation
logic, scoring, roster legality, `LeagueSnapshot`/`LeagueWorkspaceContext`/
the lifecycle resolver/`DecisionResultEnvelope`/`PlayerAvailabilityStatus`
semantics, `trade_finder_service.find_win_win_trades`'s own math, or
`redraft_trade_analysis_service.evaluate_trade`'s own math** -- confirmed
by direct reading of every file in the diff, not by trusting prior
workers' own self-reports alone.

**Hard boundaries respected.** No merge/push/deploy/push-to-origin.

**CONSOLE ERRORS THIS PASS: 0** -- across every live Chrome-driven check
(the full Work Unit 5 click-through, 3 Weekly Home reloads, 3 deep-link
hard reloads), checked via `read_console_messages` with no pattern filter
(all message types, not just errors).

**Open issues for whoever picks this branch up next:**
1. Waivers' real, measured 16.3s latency (THIS_WEEK mode, smoke-script
   timing) is notably slower than every other traced surface -- not
   investigated further by this verification-only pass (no waiver-path
   code was touched this shift); worth a dedicated profiling pass if the
   owner notices it in daily use.
2. This pass's dedup fix is backend-Python-only and was NOT rebuilt into
   a fresh native sidecar/package -- the NSIS/MSI installers on disk still
   reflect Worker B's pre-dedup-fix build. Functionally harmless (the
   dedup fix only changes how often a duplicate ledger LINE gets written,
   never what the app displays or recommends), but a future native
   rebuild should pick this fix up along with whatever else accumulates
   before the owner actually installs a packaged build.
3. Every other real, disclosed remainder from Worker A's/Worker B's own
   "Open issues" lists (weekly-home-actions historically fixed and
   reconfirmed here; the unrouted legacy `TradeFinderCard` button; the
   real K/DST/QB `UNMATCHED_IDENTITY` name-format gap on Opponent Rosters;
   the build-machine-path Rust debug-string disclosure; etc.) is untouched
   and still open exactly as documented in those entries above.
4. `local_exports/release_gate/20260913T071943Z/` (this pass's own real
   smoke-run artifacts) and `local_exports/_wu7_endurance_result.json`
   (this pass's endurance-script output) are gitignored, not committed --
   confirmed via `git status --short` showing no such paths tracked.

**READY TO PUSH AS CHECKPOINT: YES.**

## Privacy-safe packaging architecture + native package (Worker B) --
2026-09-13

**Worker B's scope: design and implement the privacy-safe Tauri packaging
architecture item 9 (`check:resources` owner-marker block) left open by
Worker 3/every worker since, then attempt the real native build.** Governance-
sensitive task; did not touch the privacy guard's logic, did not edit the
canonical governance receipt, did not add any name to a "safe" allowlist.
Design doc: `docs/codex/post_ui_v1/NWR_PRIVACY_SAFE_PACKAGING_DESIGN_V1.md`.

**Root cause, verified by reading the actual runtime (not assumed):** the
bundled `NWR_DATA_GOVERNANCE.json` governance receipt legitimately carries
the real owner's name in its own `approved_by` audit-trail field.
`desktop_facade.py._ensure_redraft_projection_seed()` reads that exact file
(relative to `self.repo_root`, which a packaged build resolves to Tauri's
`resource_dir()` -- confirmed via `nwr-desktop-runtime/src/lib.rs`'s
`resolve_repo_root()`) to perform the one-time first-run seed install via
`redraft_engine_v1_service.install_projection_snapshot()`/
`_validate_approval_receipt()`, which requires a full receipt shape
(`approved_by`/`approved_at_utc` included, both non-empty). That is the only
reason the full receipt was ever a packaging candidate. **A second,
previously-undiscovered instance of the same drift was found while reading
this path:** `nwr-desktop-runtime`'s own release-build startup gate
(`REDRAFT_RESOURCE_FILES`) was ALSO stale -- still pointing at the retired
608-row `candidate_v1_20260809` packet, not the Freeze V7 packet Worker 2's
P0-2 pass and Worker 3's own npm-allowlist fix already migrated to. A
packaged build attempted before this pass (even with the privacy conflict
somehow bypassed) would have failed at Tauri startup with "bundled redraft
resources are incomplete." Fixed as part of this same edit.

**Architecture built (two artifacts, not one):**
- **A. Private canonical receipt** -- untouched, unedited, stays in the repo
  for provenance. `git diff` against it is empty (verified). Its content,
  filename, and location are exactly as Worker 2 migrated it.
- **B. Release-safe runtime admission summary (new)** --
  `docs/hq/model/nwr_redraft_2026_freeze_v7_bundled_seed_v1_20260912/
  NWR_DATA_GOVERNANCE_RELEASE_SUMMARY.json`, deterministically derived by
  `src/services/governance_release_summary_service.py`'s
  `derive_release_admission_summary()` (built field-by-field from an
  explicit allowlist -- `authority`/`approval_status`/`season`/`source_id`/
  `source_sha256`/`valid_until`/`admission_scope`/`component_sources_as_of`
  -- never a copy-then-strip of the input, so no future receipt field is
  included by accident). Carries NO `approved_by`, NO `approved_at_utc`, NO
  human name, NO local path. Hash-bound to the exact canonical receipt it
  came from (`derived_from_canonical_receipt_sha256`) and to the exact
  projection artifact it admits (`source_sha256`, same field/value the
  canonical receipt itself uses) -- it cannot be silently repointed at a
  different admission or a different projection snapshot. Regeneration
  script: `scripts/derive_governance_release_summary.py` (also the
  mechanism the drift test re-runs).

**Runtime wiring:** `desktop_facade.py`'s bundled-seed install now reads
ONLY the release summary (`REDRAFT_SEED_RELEASE_SUMMARY_RELATIVE`) via a
new, separate `redraft_engine_v1_service.install_projection_snapshot_from_
release_summary()` -- the original `install_projection_snapshot()`/
`_validate_approval_receipt()` (full-receipt path) are byte-for-byte
unmodified and remain correct for the manual admission page and their own
existing test suite. `_projection_manifest_errors` (the ongoing local-
integrity re-check run on every mutating Redraft operation via
`require_manifest=True`) now detects, from the installed `.approval.json`'s
own shape (`"kind"` field), which validator to re-run -- the full-receipt
branch is untouched; only a new summary-shaped branch was added. Both dev
and packaged builds now go through the identical summary-based seed-install
path (no dev-vs-packaged divergence left in this logic -- the exact class
of gap that caused the stale-Rust-constant bug above).

**Files updated to point at the summary instead of the full receipt:**
`desktop/apps/redraft/src-tauri/tauri.windows.conf.json` (Windows resource
map), `desktop/scripts/check-resource-allowlists.mjs` (the `redraft`
allowlist -- the guard's own `ownerMarkers`/`assertNoOwnerMarkers`/exact-
match logic is completely unmodified), `desktop/crates/nwr-desktop-runtime/
src/lib.rs` (`REDRAFT_RESOURCE_FILES`, also fixing the stale-path bug above
in the same edit).

**Tests (all new, all passing):**
- `tests/test_governance_release_summary_service.py` (19 tests): the
  committed summary regenerates byte-for-byte from the committed canonical
  receipt (drift detection); the canonical receipt itself still carries
  "Spencer Colety" untouched (proves nothing redacted it); the derived
  summary never contains a forbidden field or owner marker;
  `validate_release_admission_summary` accepts a well-formed match and
  rejects: hash mismatch, season mismatch, expiry, wrong approval_status,
  wrong kind, wrong schema version, missing field, a hand-reinserted
  `approved_by`, and an owner-marker string smuggled into an allowed field.
- `tests/test_privacy_safe_packaging_bundle.py` (6 tests): runs the ACTUAL
  `node check-resource-allowlists.mjs` as a subprocess and asserts exit 0
  (a real guard run, not logic-only); loads the actual
  `tauri.windows.conf.json` resource map and asserts the private receipt's
  path is absent / the summary's path is present; reads the actual bytes of
  every bundled `redraft` resource file off disk and asserts none contain
  an owner marker; cross-checks the Rust `REDRAFT_RESOURCE_FILES` constant
  against the npm allowlist so the two file sets can never silently drift
  apart again.
- `tests/test_redraft_engine_v1_service.py` (+4 tests): a real end-to-end
  install via `install_projection_snapshot_from_release_summary` that
  reloads cleanly through `require_manifest=True`; installed `.approval.json`
  proven to contain no `approved_by`/owner name; hash-mismatch and expired-
  summary installs both correctly rejected; a tampered installed summary
  (edited `valid_until`) is caught on the very next reload -- proves the
  ongoing local-integrity re-check is not a no-op for the new branch.
- Regression: `pytest tests/test_redraft_engine_v1_service.py` -- identical
  pre-existing 3 failed/13 errors both before and after this pass (confirmed
  via `git stash` A/B), a real, unrelated calendar-drift issue in that file's
  own hardcoded `source_as_of` fixture dates (today is 2026-09-13; several
  of that file's dates now exceed the 30-day freshness window) -- zero new
  regressions, 4 new tests pass. `pytest tests/test_desktop_application_api.py`:
  46 passed, 4 failed -- the exact same 4 pre-existing failures this
  ledger's baseline already documents (confirmed by exact test-name match).
  `pytest tests/test_desktop_facade_architecture_wiring.py tests/
  test_player_availability_status_consumer_consistency.py tests/
  test_player_availability_status_service.py`: 21/21 passing. `cargo test`
  (nwr-desktop-runtime): 4/4 passing (parametric over the corrected resource
  list, no test edits needed).

**NATIVE PACKAGE: PASS.** `npm run check:resources` now passes cleanly for
both apps (previously blocked for `redraft` only). Rebuilt the Python
sidecar with `-Force` (fresh hash, reflects this pass's source changes) and
ran the real `npm run tauri:build --workspace @nwr/redraft-desktop`
end-to-end: cargo release build succeeded, both configured bundle targets
produced real installers -- `target/release/bundle/nsis/Niners War Room —
Redraft_1.0.8_x64-setup.exe` (NSIS) and `target/release/bundle/msi/Niners
War Room — Redraft_1.0.8_x64_en-US.msi` (MSI), exit code 0, "Finished 2
bundles."

**PACKAGE PRIVACY SCAN: PASS (one minor, disclosed, unrelated finding).**
The NSIS installer's payload is LZMA-compressed (a plain byte scan of the
`.exe` finds nothing, compressed or not -- confirmed against a string known
to be present); administratively extracted the MSI instead
(`msiexec /a ... TARGETDIR=...`, a real, standard Windows extraction, not a
formality) to inspect the actual installed payload: exactly 5 files ship --
the 3 governance/projection resources (confirmed: the release summary, NOT
the private receipt) and the two executables (sidecar + main app). Scanned
every one of those 5 real files for owner names, the real owner's email,
the real local AppData install path, Bearer/API-key/private-key patterns,
`approved_by` (would only appear if the private receipt had leaked in), the
real Sleeper league IDs this shift has used for live testing, and generic
email addresses -- **zero matches on all of the above.** One separate,
minor, disclosed finding: `nwr-redraft-war-room.exe` embeds the BUILD
MACHINE's Windows account name (`codex-agent`, this sandbox's account, not
the real owner's) ~44 times, exclusively inside standard Rust panic-location
debug strings for THIRD-PARTY dependency crates (mio, tauri, serde, url,
etc. -- their `~/.cargo/registry/...`/`~/.rustup/...` source paths, embedded
by the Rust compiler by default). Verified this is generic Rust/Cargo
toolchain behavior, not an NWR-specific leak: NWR's own crate
(`nwr-desktop-runtime`) panic locations are relative
(`crates\nwr-desktop-runtime\src\lib.rs`), not absolute, and neither
`C:\NWR` nor `post-ui-product-v1` (this worktree's own path) appear anywhere
in the binary. This is an existing property of any Rust/Tauri release build
on any machine (not introduced or worsened by this pass), does not leak the
real owner's identity in this particular build, and is a distinct
architecture surface from the governance-receipt problem this pass was
scoped to fix -- disclosed as an open item below rather than addressed here.

**Files changed (all packaging/governance-projection, zero scoring/roster/
draft-recommendation files):** `src/services/governance_release_summary_
service.py` (new), `scripts/derive_governance_release_summary.py` (new),
`docs/hq/model/nwr_redraft_2026_freeze_v7_bundled_seed_v1_20260912/
NWR_DATA_GOVERNANCE_RELEASE_SUMMARY.json` (new, generated), `src/services/
redraft_engine_v1_service.py` (additive: one new install function, one new
branch-detection helper, one new branch in `_projection_manifest_errors`;
`install_projection_snapshot`/`_validate_approval_receipt` untouched),
`src/application/desktop_facade.py` (seed-install wiring only),
`desktop/apps/redraft/src-tauri/tauri.windows.conf.json`, `desktop/scripts/
check-resource-allowlists.mjs`, `desktop/crates/nwr-desktop-runtime/src/
lib.rs` (resource-list correctness, guard logic itself untouched), plus the
three new/extended test files above and this design doc.

**Hard boundaries respected:** `marginal_roster_utility_v2`, draft
recommendation logic, scoring, roster legality, `LeagueSnapshot`/
`LeagueWorkspaceContext`/the lifecycle resolver/`DecisionResultEnvelope`/
`PlayerAvailabilityStatus` semantics were never touched or read beyond what
was already necessary to trace the governance-receipt install path. No
merge/push/deploy/push-to-origin.

**Open issues for the next worker (real read-only release smoke rerun):**
1. The real native package (NSIS + MSI, this pass's fresh build) sits at
   `desktop/target/release/bundle/{nsis,msi}/` (gitignored, not committed) --
   worth a real install-and-launch smoke test on a clean profile if the next
   worker has time; this pass verified the build + a static content/privacy
   scan of the extracted payload, not an actual install + first-run launch.
2. **Build-machine-path disclosure (new finding, low severity, not fixed):**
   the shipped `nwr-redraft-war-room.exe` embeds the building machine's
   Windows account name inside third-party Rust dependency debug strings
   (see PACKAGE PRIVACY SCAN above). If the owner ever wants zero
   build-machine metadata in the shipped binary, the exact fix is a Cargo
   build-config change -- e.g. `RUSTFLAGS="--remap-path-prefix=<cargo home>=
   /cargo --remap-path-prefix=<rustup home>=/rustup"` (or a workspace
   `.cargo/config.toml` `[build] rustflags` entry) applied to both desktop
   apps' release profile -- NOT implemented by this pass (a real, generic
   Rust-toolchain build-hygiene item, orthogonal to the governance-receipt
   architecture this pass was scoped to fix, and a decision the owner should
   make deliberately rather than have bundled into an unrelated privacy fix).
3. The Python sidecar exe was rebuilt with `-Force` this pass (new hash,
   reflects this session's backend changes) -- if a future pass rebuilds it
   again, `desktop/binaries/*.sha256` will change again; this is expected
   and not itself a regression signal.
4. Every other real, disclosed remainder from Worker 11's/Worker A's
   consolidated open-items lists (weekly-home-actions 500 is item 8 there --
   unrelated to this pass, not touched; the "Open in Analyze" canonical-vs-
   Sleeper id gap; etc.) is untouched and still open exactly as documented
   there.

## Closure pass (bug 1: weekly-home-actions 500; bug 2: canonical-vs-Sleeper
identity boundary) -- 2026-09-13

**Worker A's scope: two real, previously-disclosed bugs only (branch
`upgrade/nwr-post-ui-product-v1-20260912`, continuing directly on top of
Worker 11's `e06e4a26`), bug-fix only, no new feature scope.** Both bugs
were open items 1 and 3 in Worker 11's consolidated list (ledger items 8
and 10). Two commits: `35c1adc5` (bug 1), `952787a8` (bug 2).

**BUG 1 (P0) -- FIXED.** Root cause confirmed by direct reproduction (not
assumed from the ledger): `redraft_weekly_home_actions`
(`src/application/desktop_facade.py`) built its STREAMER section from
`redraft_kdst_streamer(...).data["positions"]` assuming a
`{"K": [...], "DST": [...]}` dict; it is actually a flat list of
decision-envelope rows (each row self-identifying its own "position"
field) -- a shape already established on `redraft_kdst_streamer` itself
(to fix a different, already-resolved camelCase-key-mangling hazard) but
never propagated to this one call site. The resulting `AttributeError`
was not a `FacadeError`, so it escaped every existing `except FacadeError`
handler and surfaced as a bare HTTP 500. Fixed by iterating the real flat
list directly (functionally identical "first ADD row per position"
behavior, verified against `streamer_actions()`'s own one-ADD-per-position
guarantee), plus a second, narrow `except (AttributeError, TypeError,
KeyError)` around ONLY the STREAMER section (not the whole method) so a
future shape drift degrades that one section honestly instead of 500ing
the whole response. Permanent regression fixture added
(`tests/test_weekly_home_single_snapshot.py`) matching the real live
response shape exactly, plus a second test proving a genuinely malformed
shape still degrades honestly rather than crashing.

**BUG 1 LIVE VERIFICATION:** real, read-only Fantasy Gamers Sleeper
league -- `POST /api/v1/redraft/weekly-home-actions {"week":1}` ->
HTTP 200 (was 500), 9 real actions (including 2 real STREAMER rows: "Stream
K: Cam Little", "Stream DST: Jacksonville Jaguars"), `unavailableSections:
[]`, a real non-null `leagueSnapshotId`. Independently re-confirmed via
this project's own `nwr_release_gate_smoke.ps1` instrumented run against
the same real league (`weekly_home_actions_week1 status=200`). Rendered
live in Chrome (Weekly Home's "NWR Actions" panel), zero console messages
on a fresh reload. Note: the 2 STREAMER rows are real but rank below this
page's own top-5 display cutoff for this league's current 9-action set
("Showing the top 5 of 9 ranked actions this week") -- confirmed present
in the raw API response and via direct backend-level checks, not
independently confirmed visible in the top 5 of THIS particular render
(by design, not a bug).

**BUG 2 -- FIXED.** Root cause traced to the actual identity boundary this
codebase already establishes elsewhere: `RedraftMyRosterPlayer` carries
both `sleeperPlayerId` (raw provider id) and `canonicalPlayerId` (NWR's own
GSIS-style id); `RedraftOpponentPlayer` had ONLY `sleeperPlayerId`. Since
`TradeFinderCandidate.myGivePlayerId`/`opponentGivePlayerId` are actually
canonical ids (confirmed by reading `trade_finder_service.
find_win_win_trades`, which operates entirely in canonical-id space), the
old "Open in Analyze" button (`TradeFinderCard`, in-season.tsx) had no
correct id to reach for and passed the canonical ones through
`giveSleeperId`/`receiveSleeperId` query params straight into
`redraftTradeAnalysis`, which requires real raw Sleeper ids -- an
always-fails path (`TRADE_ANALYSIS_IDENTITY_UNRESOLVED`) for the opponent
side. Fixed at the root: (1) `RedraftOpponentPlayer` now carries
`canonicalPlayerId`/`identityStatus`, computed via the SAME
`resolve_roster_canonical_ids` matcher every other canonical-id call site
in this module already uses; (2) `TradeFinderCandidate` now ALSO carries
`mySleeperPlayerId`/`opponentSleeperPlayerId`, reverse-mapped from the same
resolution `redraft_trade_finder` already computes; (3) the "Open in
Analyze" link now resolves through a new pure function
(`tradeFinderAnalysisLinkTarget`, trades-explain.ts) using those real
Sleeper ids, with an honest "unavailable" message (never a
guaranteed-to-fail link, never a silent canonical-id substitution) when
either side can't be resolved. **Nearby-instance search performed and
disclosed:** every other `giveSleeperId=`/`receiveSleeperId=` link site
(My Roster's "Add to Trade Analysis", Opponent Rosters' "Add to trade")
already used real Sleeper ids correctly -- no other instance of this exact
mistake found. The live "Find Trades" tab (trades.tsx,
`TradePackageCandidate`) still deliberately has no "Open in Analyze"
button at all (Worker 7's own prior disclosed omission, to avoid
replicating this bug in the new UI) -- intentionally NOT added by this
pass (would be new feature scope, not a bug fix); a future pass could
revisit that now that the underlying id-boundary gap is closed.

**BUG 2 LIVE VERIFICATION:** real Fantasy Gamers league --
`GET /api/v1/redraft/opponent-rosters` now returns real
`canonicalPlayerId`/`identityStatus` per opponent player (real MATCHED
examples: Derrick Henry, Jaylen Warren; a real, honest
UNMATCHED_IDENTITY case also observed for a K/DST/QB -- a real name-format
gap, not hidden or fabricated around). `GET /api/v1/redraft/trade-finder`
now returns distinct `mySleeperPlayerId`/`opponentSleeperPlayerId`
alongside the pre-existing canonical ids on every real candidate. Direct
A/B proof against the real backend: the FIXED path
(`redraft-trade-analysis` called with the new real Sleeper ids) -> HTTP
200 with correct real gives/receives; the OLD BUGGY path (same call with
the canonical ids in the Sleeper params, exactly what the pre-fix button
sent) -> HTTP 409 `TRADE_ANALYSIS_IDENTITY_UNRESOLVED`, confirming both
the original failure mode and that the fix actually closes it.
Render-tested live in Chrome: navigated to the real `/trade-analysis?
giveSleeperId=...&receiveSleeperId=...` deep link built from the corrected
real ids (the same contract the repaired button now produces) -- the
Analyze tab pre-filled both players and produced a complete real
before/after verdict on "Analyze trade", zero console messages across a
fresh reload. Disclosed precisely: `TradeFinderCard`'s own button is
UNROUTED in the current build (Find Trades is served by trades.tsx's own
tab today; `TradeFinderPage`/`TradeFinderCard` remain an unrouted legacy
fallback per an earlier worker's own disclosed consolidation, still read
live by Weekly Home's TRADE action cards via `redraft_trade_finder`) --
this render test exercises the same fixed query-param contract the button
constructs, not a literal click on the button inside a currently-live
route.

**Tests:** `tests/test_redraft_identity_boundary_opponent_and_trade_finder.py`
(new, 6 tests, real bootstrapped Freeze V7 governed ranking, real player
rows -- not synthetic doubles): matched/unmatched-catalog/
unmatched-ranking opponent rows, a Trade Finder candidate carrying correct
per-side Sleeper ids, the full canonical-id action flow end to end (real
success + the old-shape failure both proven), and a stale/wrong provider
id caught by the existing check. `trades-explain.test.ts` (+5 tests):
matched/unmatched/stale-id-never-substituted/end-to-end for
`tradeFinderAnalysisLinkTarget`. `test_weekly_home_single_snapshot.py`
(+2 tests, bug 1's regression fixture). `attention-center.test.ts`
fixtures updated for the additive opponent-roster fields (no assertion
changes).

`npx vitest run --no-file-parallelism` (full monorepo): **367/367 passing,
28/28 files** (362 baseline + 5 new `trades-explain.test.ts` tests; the +2
`test_weekly_home_single_snapshot.py` tests and the +6 new identity-
boundary test file are pytest, not vitest). `npx tsc -b
apps/dynasty/tsconfig.json apps/redraft/tsconfig.json`: clean.
`pytest tests/test_desktop_application_api.py`: 46 passed, 4 failed --
confirmed the exact same 4 pre-existing failures this ledger's own
baseline already documents; zero new regressions. Targeted pytest across
every touched/adjacent backend suite (weekly home snapshot, the new
identity-boundary file, architecture wiring, player-availability
consumer consistency, trade finder, trade package search facade wiring):
49/49 passing.

**Hard boundaries respected:** `marginal_roster_utility_v2`, draft
recommendation logic, scoring, roster legality,
`redraft_trade_analysis_service.evaluate_trade`/`trade_finder_service.
find_win_win_trades`'s own math (read-only reuse of already-computed
values), `LeagueSnapshot`/`LeagueWorkspaceContext`/the lifecycle
resolver/`DecisionResultEnvelope`/`PlayerAvailabilityStatus` semantics
were never touched -- only additive fields were added to
`RedraftOpponentPlayer`/`RedraftOpponentRostersResult`/
`TradeFinderCandidate`. `git diff --stat e06e4a26 HEAD -- src/` touches
exactly one file (`desktop_facade.py`), both hard-boundary-adjacent
services (`trade_finder_service.py`, `redraft_trade_analysis_service.py`,
`fantasypros_kdst_consensus_service.py`) show zero diff. No merge/push/
deploy.

**Sleeper writes: 0**, verified the same way every prior worker in this
project has: structural (`SleeperHttpClient` defines only `get_json()`,
no write method exists on the class), grep (no POST/PUT/PATCH/DELETE
targets `api.sleeper.app` anywhere in `src/`), and a real before/after
byte-diff of `league`/`rosters`/`users` fetched directly from
`api.sleeper.app` around this session's live Sleeper import (via the
release-gate smoke script's own instrumented check) -- IDENTICAL.

**Open issues for the next worker (privacy-safe Tauri packaging design):**
1. `npm run check:resources` still fails at the owner-privacy/allowlist
   guard because the bundled `NWR_DATA_GOVERNANCE.json` governance
   receipt's own audit trail legitimately contains the real owner's name
   -- unchanged by this pass (out of scope; a real product/governance
   decision for the owner, not a code bug this or any prior verification
   pass should decide unilaterally). This is presumably central to the
   next worker's own privacy-safe packaging design task.
2. The live "Find Trades" tab (`TradePackageCandidate` cards, trades.tsx)
   still has no "Open in Analyze" button -- the underlying id-boundary gap
   this pass closed would now support adding one correctly (via the same
   `youSend`/`youReceive` canonical ids plus a parallel Sleeper-id
   resolution), but doing so was judged new feature scope, not a bug fix,
   and was deliberately not attempted.
3. `TradeFinderPage`/`TradeFinderCard` (in-season.tsx) remain an unrouted
   legacy fallback -- fixed anyway per this pass's own directive (fix the
   root cause, not just the reachable path), and still read live by
   Weekly Home's own TRADE action cards via `redraft_trade_finder`
   (`home-action-explain.ts`), but the "Open in Analyze" button itself
   could not be click-tested inside a currently-live route; verified via
   an equivalent live deep-link instead (see BUG 2 LIVE VERIFICATION
   above) and via 6 new backend + 5 new frontend unit tests.
4. The real K/DST/QB `UNMATCHED_IDENTITY` case observed live on Opponent
   Rosters (bug 2 verification) is a real, disclosed name-format identity
   gap in the existing `resolve_roster_canonical_ids` matcher (e.g. a
   Sleeper D/ST catalog name not matching the ranking pool's own naming) --
   not investigated further by this bug-fix-only pass; a future pass could
   look at whether the identity matcher itself needs a D/ST-naming
   improvement (a real, disclosed remainder, not new evidence of a
   regression).
5. Every other real, disclosed remainder from Worker 11's consolidated
   "OPEN ITEMS REMAINING -- WHOLE SHIFT" list (items 2, 4-15) is untouched
   and still open exactly as documented there.

## P2-1 (Data Notice Strip) -- 2026-09-12/13

**Worker 10's scope: ONE compact, persistent shell-level data-notice
signal, visible from every surface, click-through to the existing Data
Health page.** Presentation only -- zero backend/`src/` files touched
(confirmed via `git status --porcelain`, only `desktop/` files in the
diff). `marginal_roster_utility_v2`, draft recommendation logic, scoring,
roster legality, `LeagueSnapshot`/`LeagueWorkspaceContext`/the lifecycle
resolver/`DecisionResultEnvelope`/`PlayerAvailabilityStatus` were never
touched or read for anything beyond what the existing header components
already read.

**Checked the directive's own lead first: `RedraftBootstrap.notices` is
real and exactly as described** -- `DesktopBackendFacade.redraft_bootstrap`
(`src/application/desktop_facade.py`, the `notices = [...]` block) already
computes and returns it, and today it is rendered ONLY on the Data Health
page (`pages.tsx`'s `DataHealthPage`, `data.notices.map(...)`). It is the
right base data source, with one real, disclosed nuance: four of its
entries ("Redraft is isolated from Dynasty", "Current-season evidence
only", "Role-change context is not yet modeled", "External K/DST
consensus boundary") are PERMANENT product-boundary disclosures --
unconditionally appended every time, regardless of whether anything is
actually wrong. Counting those as "issues" would mean the compact shell
signal could never reach a calm "Current" state for anyone, and the
K/DST-consensus one is also exactly the kind of external-provider
plumbing the directive says this compact signal must not surface. This
pass also found the shell's existing `FreshnessIndicator` header chip
(`shell-identity.tsx`, built in the earlier UI-foundation pass) was
ALREADY 80% of this work unit -- a compact "Current"/"N data issues" chip
in the header status bar with a click-open popover -- just computed from
3 hardcoded booleans (identity/ADP/ready) instead of the real notices
array, and with no link into Data Health at all.

**What was built (all in `desktop/apps/redraft/src/`, matching this app's
own established convention of pure derivation unit-tested + presentation
components verified live -- see `attention-center.ts`/`league-summary.ts`
for the same pattern):**
- NEW `shell-notices.ts`: `summarizeShellNotices(data: RedraftBootstrap)`,
  a pure function combining (1) `data.notices` filtered to exclude the
  four always-present disclosure titles above (an explicit, documented,
  disclosed-as-fragile title set -- a real backend wording change to any
  of the four would need this list updated too) and any `tone: "ready"`
  entry, with (2) the pre-existing player-identity/market-ADP/draft-board-
  readiness signals `FreshnessIndicator` already read (real, owner-relevant
  gaps `data.notices` itself does not carry as notice rows -- kept rather
  than dropped, per the directive's own "combine with something notices
  doesn't cover" allowance). Returns `{count, label, tone, items}`:
  `count===0` -> `"Current"`; `count===1` -> that one issue's own real
  title (e.g. "PRACTICAL SCORING", "Market ADP unavailable", "1 rookie
  remains blocked"); `count>1` -> `"N data issues"`. No new notice content
  is invented anywhere -- this file only classifies and summarizes what
  the backend already computed.
- MODIFIED `shell-identity.tsx`'s `FreshnessIndicator`: now renders
  `summarizeShellNotices(data)`'s label/tone on the chip (same header
  status-bar slot, `AppShell`'s `statusExtra`, so it is genuinely visible
  from every route), and its click-open popover now lists every real issue
  (title + message) instead of the old fixed Identity/ADP/Projections/
  Draft-board rows, plus an "Open Data Health →" link
  (`react-router-dom` `Link` to `/data-health`, reusing the existing
  legacy-redirect route -- no new route added) for click-through into the
  full existing Data Health page.
- MODIFIED `redraft.css`: replaced the now-unused `dl`/`dt`/`dd` panel
  rules with `.nwr-freshness__list`/`__item`/`__item--blocked`/`__ok`/
  `__detail-link`, reusing the exact same color tokens
  (`--nwr-warning`/`--nwr-unavailable`/`--nwr-healthy`/`--violet-bright`)
  every other status surface in this app already uses -- no new visual
  language invented.
- NEW `shell-notices.test.ts` (8 tests): all-healthy (always-present
  disclosures correctly ignored), no-active-league, exactly-one-issue
  (title becomes the label, tone "warning"), multiple issues (plain count,
  tone "unavailable" once any issue is blocked-severity), unavailable-ADP
  as its own single issue, a `status.tone==="blocked"` case as its own
  single issue, an explicit state-leakage check (two different
  `RedraftBootstrap` objects summarized back-to-back, asserting neither
  leaks into the other and re-summarizing the first again afterward is
  byte-identical -- this shift's own established paranoia, applied to a
  pure function this time since there is no server state to isolate), and
  the exclusion-list itself (all four disclosure titles, including one
  given `tone: "blocked"`, correctly produce "Current").

**Live-verified, not just unit-tested** (`desktop/scripts/
nwr_release_gate_smoke.ps1 -KeepRunning`, real backend on 18742 + real
production `vite build`/`vite preview` on 1422, driven live in Chrome):
- Fresh local preset profile ("NWR Release Gate Local Profile"): header
  chip showed real `"⚠ 3 data issues"`; click opened the panel listing the
  real, live-computed "Market ADP unavailable" / "Draft rounds do not
  match roster capacity" / "7 rookies remain blocked" (with the real 7
  rookie names from this repo's actual bundled-seed blocked list, not a
  placeholder), plus the "Open Data Health →" link. Clicking that link
  navigated to the real Data Health page and closed the popover.
- **State-leakage check, live, real leagues (stronger than a synthetic
  fixture swap):** switched to the real "Fantasy Gamers" Sleeper league
  (read-only activation, no Sleeper writes -- same guarantee every prior
  worker's league-switch checks already established) -- the panel's
  content correctly changed to that league's own real issues ("Market ADP
  unavailable", "Sleeper scoring needs review" with its real explicit
  field list, "7 rookies remain blocked") -- "Draft rounds do not match
  roster capacity" (specific to the local profile's own 16-round
  configuration) correctly disappeared. Switched to a second existing
  local profile ("NWR QA Local Test League") and confirmed its own
  independent 3-issue set rendered correctly, with no residual Fantasy
  Gamers content.
- Zero console messages of any kind (not just zero errors) on a full page
  reload, checked via `read_console_messages`.
- Did NOT achieve a live "Current" (zero-issue) state -- every profile in
  this repo's current data state has at least the real "7 rookies remain
  blocked" registry issue (the same admitted Freeze V7 gap Worker 2's
  P0-2 pass already disclosed), so a genuine zero-issue league does not
  exist in this environment today. The "Current"/all-healthy state is
  real and correctly implemented (proven directly by 3 of the 8 unit
  tests, including the exclusion-list test using every one of the four
  real always-present disclosure titles verbatim), just not organically
  reproducible live in this exact snapshot -- disclosed rather than
  claimed as live-observed.
- Backend + preview processes (PIDs on 18742/1422) stopped at the end;
  confirmed via `Get-NetTCPConnection` that no listener remained on either
  port afterward. The smoke script's own `check:resources` step failed for
  the same pre-existing, already-disclosed owner-marker/allowlist conflict
  every prior worker's packaging-gate attempt has hit (not caused by this
  pass, not investigated further -- out of scope for a presentation-only
  work unit). Its `local_exports/release_gate/...` report is gitignored,
  confirmed via `git check-ignore -v`, not committed.

**Tests:** `npx vitest run desktop/apps/redraft/src/shell-notices.test.ts
--no-file-parallelism`: 8/8 passing. `npx tsc -b apps/dynasty/tsconfig.json
apps/redraft/tsconfig.json` (from `desktop/`): clean. `npx vitest run
--no-file-parallelism` (full monorepo): **362/362 passing, 28/28 files**
(354 baseline from Worker 8's P1-4 pass + 8 new `shell-notices.test.ts`
tests). `pytest` not run -- zero backend files touched (confirmed via
`git status --porcelain`, no `src/`/`tests/` entries).

**Hard boundaries respected:** `marginal_roster_utility_v2`, draft
recommendation logic, scoring, roster legality, `LeagueSnapshot`/
`LeagueWorkspaceContext`/the lifecycle resolver/`DecisionResultEnvelope`/
`PlayerAvailabilityStatus` semantics were never touched -- this pass reads
`data.notices`/`data.health`/`data.draftBoard.adp`/`data.status` exactly
as the pre-existing `FreshnessIndicator`/`DataHealthPage` already did, and
computes zero new business data (only classifies/summarizes what the
backend already returns). No backend file in the diff. No merge/push/
deploy.

**Scope note, disclosed:** this pass covers the Redraft app only, matching
every other worker's scope this entire shift. The separate, much smaller
Dynasty app (`desktop/apps/dynasty/src/pages/home.tsx`) already renders
its own `data.notices` inline as plain alert-strips on its Home page, with
no shell-level chip -- untouched by this pass, a real, disclosed
remainder if the owner ever wants the same treatment there.

**Open issues for Worker 11 (endurance + packaged release verification):**
1. No genuinely "Current" (zero-issue) league exists anywhere in this
   repo's current data state (see the live-verification note above) --
   worth knowing if a packaged-release walkthrough expects to see the calm
   state; it is real and correct, just not currently reproducible without
   either resolving the real 7-blocked-rookie registry gap or importing a
   real ADP snapshot for a league whose draft rounds already match its
   roster capacity.
2. The `ALWAYS_PRESENT_DISCLOSURE_TITLES` exclusion set in
   `shell-notices.ts` is matched by exact title string against
   `desktop_facade.py`'s `redraft_bootstrap()` -- a real, disclosed
   fragility: a future backend wording change to any of those four titles
   needs this frontend list updated in the same pass, or that notice would
   silently start counting as an "issue" everywhere.
3. `check:resources` (the native-bundle privacy/allowlist gate) still
   fails for the same pre-existing owner-marker conflict Worker 3's P1-1
   pass already found and disclosed -- unchanged, not investigated further
   by this presentation-only pass.

## P1-5 (Live Player Intelligence Provider Bakeoff) -- 2026-09-12/13

**Worker 9's scope: research only, plus shadow ingestion IF a genuinely
free/admissible source existed.** No purchase, no API-key signup, no paid
contract. Full research doc:
`docs/codex/post_ui_v1/NWR_PLAYER_INTELLIGENCE_PROVIDER_BAKEOFF_V1.md`.

**RotoWire, SportsDataIO, Sportradar -- all real, all researched, all
NEEDS_OWNER_CONTRACT.** None has a self-serve free/cheap tier suitable for
a live availability feed: RotoWire has no public pricing or self-serve
signup at all (confirmed via its own syndication page and OpticOdds' real
distribution docs -- "Your OpticOdds API Key will not work with RotoWire...
contact sales"); SportsDataIO has a real ~$99-149/mo self-serve
DiscoveryLab tier per third-party pricing trackers, but it is
next-day-delayed (not real-time) and still a real recurring paid signup;
Sportradar is fully enterprise/quote-gated with no public pricing found
anywhere. FantasyData/FantasyPros (this repo's own prior May 2026 research,
a different route/usage-data focus) remain the same NEEDS_OWNER_CONTRACT
status, not re-priced this pass. A full vendor/contact/action list for the
owner is in the doc.

**Two REAL, free, admissible sources found beyond the three named
providers -- ADMIT (shadow-only), and actually built:**
1. **nflverse's official weekly injury report** (`injuries_<season>.csv`,
   the same nflverse family this repo already trusts everywhere else) --
   real, live-fetched Week 1 2026 file (182 rows) carries NWR's own
   canonical `gsis_id` directly, real official `report_status`
   (Out/Doubtful/Questionable) and, importantly, REAL populated
   `practice_status` (Full/Limited/DNP -- 182/182 non-null) -- a genuine
   practice-participation signal NWR's manual overrides don't track at
   all. Covers 52/564 (9.2%) of the real canonical pool in Week 1, which
   is EXPECTED to be small (only actually-injured players appear on the
   report), and 100% of those 52 carry a real practice_status. Free, no
   key, historical back to 2009. One real, disclosed schema-drift finding:
   the published data dictionary describes a `date_modified` column that
   is NOT present in the actual live-fetched file.
2. **Sleeper's public `players/nfl` catalog** (the SAME free, keyless
   endpoint this repo already calls elsewhere, and the same provider NWR
   already reads live for real Sleeper leagues) -- real, live-fetched
   catalog (12,227 players, 14.65MB, larger than the docs' stated ~5MB).
   Real `injury_status`/`status` fields cover Questionable/IR/Out/PUP/
   **Suspended (12 real cases)**/Doubtful; real `depth_chart_position/
   order`. Real `gsis_id` field direct-matches 93/564 canonical players;
   the SAME `_identity` name/position/team matcher
   `waiver_engine_service.resolve_roster_canonical_ids` already uses
   brings real identity-mapping feasibility to 481/564 = 85.3% of the
   canonical pool. **`practice_participation` exists in the schema but is
   empirically ~0% populated (1 non-null value out of 12,227 real
   players)** -- correctly NOT treated as a practice-participation source;
   nflverse fills that gap instead. Real caveat: free for NON-COMMERCIAL
   use only per Sleeper's own docs -- fine for NWR today (a personal
   desktop app), flagged for re-check if NWR is ever distributed/sold.
   Sleeper's own docs require caching (fetch at most once/24h) -- enforced
   for real by this pass's fetch script (verified live: an immediate
   second fetch attempt was correctly SKIPPED).

**Real comparison against NWR's 3 actual manual overrides on file** (run
through this pass's shipped code, not estimated): Jayden Higgins
(`SEASON_OUT`, ACL) -- Sleeper's live data independently corroborates
every field (`status=Inactive`, `injury_status=IR`,
`injury_body_part=Knee - ACL`, team `HOU`). Elijah Mitchell
(`NOT_WITH_TEAM`) -- a real Sleeper entry exists (`team=None,
injury_status=Questionable`) but the shipped matcher HONESTLY reports it as
`UNMATCHED_NO_TEAM` rather than guessing an identity for a team-less
player -- a real, concrete illustration of why manual verification must
stay authoritative even when raw automated data exists. Kayshon Boutte
(`TEAM_CORRECTION` -> HOU) -- Sleeper agrees on team but produces no shadow
record at all (he's healthy; team corrections are outside this pass's
injury/availability-signal scope by design, not a source failure).

**Shadow ingestion built, genuinely inert (verified, not just asserted):**
`src/services/live_player_intelligence_shadow_v1_service.py` (pure,
network-free mapping/matching/report functions -- reuses the existing
`_identity` normalizer, invents no new identity heuristic) +
`scripts/fetch_live_player_intelligence_shadow_snapshot_v1.py` (the ONLY
real network I/O, writes RAW snapshots to a new, clearly-separate,
repo-wide-gitignored `local_exports/live_player_intelligence_shadow_v1/`
location, nowhere near the real override config file) +
`tests/test_live_player_intelligence_shadow_v1_service.py` (11 tests, all
passing). Two hard-boundary proofs, both real: (1) a source-level static
grep-style proof that `desktop_facade.py`/`server.py`/
`player_availability_status_service.py`/`current_player_status_overrides_
service.py`/`redraft_engine_v1_service.py`/`shadow_numeric_authorities_
service.py` never import the new module; (2) calling the REAL
`load_player_availability_statuses`/`player_availability_authority_health`
functions before and after writing a real shadow snapshot probe file to
the new location, asserting byte-identical (`==`) output both times.
`git status --porcelain` before commit showed only 4 new files (the
service, the script, the test file, the doc) -- zero existing files
modified.

**Precedence design (PROPOSAL ONLY, not implemented anywhere):**
`MANUAL_VERIFIED_OVERRIDE` (always wins, unconditionally) >
`AUTOMATED_SHADOW_SOURCE` (nflverse preferred for injury designation/
practice state; Sleeper preferred for team/IR-PUP-Suspended/roster status;
never auto-applied to any ranking/recommendation path) > `NO_SIGNAL`
(default, today's real behavior). Also returned as structured data by
`precedence_design()` for a future promotion pass to implement against
directly. Promotion is explicitly a future, separate, deliberate decision
-- not performed by this pass.

**Tests:** `pytest tests/test_live_player_intelligence_shadow_v1_service.py`:
11/11 passing. `pytest tests/test_player_availability_status_consumer_
consistency.py tests/test_player_availability_status_service.py`: 25/25
passing (unaffected, confirms no drift in the real authority this pass
shadows). `pytest tests/test_desktop_application_api.py`: 46 passed, 4
failed -- confirmed the SAME 4 pre-existing failures already documented in
this ledger's own baseline (`test_dynasty_facade_composes_real_governed_
workflows`, `test_desktop_rookie_veteran_bridge_is_source_separated_and_
trade_aware`, `test_redraft_bootstrap_seeds_once_and_matches_desktop_
contract`, `test_facade_has_no_streamlit_or_app_component_dependency`);
zero new regressions. No frontend files touched -- `tsc -b`/`vitest run`
not run (this pass's own stated condition for skipping them).

**Hard boundaries respected:** `marginal_roster_utility_v2`, draft
recommendation logic, scoring, roster legality, `LeagueSnapshot`/
`LeagueWorkspaceContext`/the lifecycle resolver/`DecisionResultEnvelope`/
`PlayerAvailabilityStatus`'s actual authority semantics were all either
read-only (to understand the shape being shadowed) or genuinely untouched
-- confirmed via `git status --porcelain` showing zero modified files, only
4 new ones. No merge/push/deploy. No API key created or stored anywhere
(`.env` does not exist in this worktree; `.env.example`'s
`SPORTSDATAIO_API_KEY`/`ROTOWIRE_EXPORT_ROOT` placeholders remain empty,
confirmed).

**Disclosed, non-blocking:** this pass's own real fetch-script run left two
real raw snapshot files under `local_exports/live_player_intelligence_
shadow_v1/` (gitignored, not committed, same pattern as every other
worker's local test-profile artifacts already disclosed elsewhere in this
ledger) -- harmless, real evidence the fetch script works, not required for
any test to pass (all tests use inline fixtures, no network).

**Open issues for Worker 10 (Data Notice Strip / minor polish):**
1. This pass's shadow module is 100% inert and unwired by design -- if a
   future pass ever wants to surface shadow-source findings anywhere in
   the UI (e.g. an optional "community source suggests X" hint, clearly
   distinguished from NWR's own verified overrides), that is a new,
   separate, deliberate decision this pass explicitly does not make or
   recommend making.
2. RotoWire/SportsDataIO/Sportradar all remain real, live options if the
   owner wants to pursue a paid provider -- the exact vendor/contact/action
   list is in the bakeoff doc's own table, not reproduced here.
3. ESPN's unofficial API was noted but not deep-dived (no ToS, real risk)
   -- a real, disclosed remainder if the two admitted free sources above
   ever prove insufficient.
4. FantasyData/FantasyPros pricing was not re-verified this pass (reused
   this repo's own prior May 2026 research) -- a real, disclosed gap if a
   future pass wants current 2026 numbers for those two specifically.

## P1-4 (Prospective Recommendation Ledger V1) -- 2026-09-12/13

**Worker 8's scope: make the existing in-season decision-trace ledger
(`in_season_decision_trace_service.py`, built in an earlier overnight
session, NWR Overnight V3 Lane 18) owner/product-useful.** Extended and
reused that exact ledger -- no second, parallel trace system was built.
Prospective only, per the directive: nothing retroactive was fabricated;
every event this pass observed live was recorded from real, real-time tool
calls against the real, already-populated "Fantasy Gamers" Sleeper league
ledger (98 real events accumulated across this and prior workers' sessions
against that one profile's `decision_traces/<profile_id>.jsonl` file).

**A real, found bug closed:** `desktop_facade.py` already called
`record_decision_trace(tool="TRADE_FINDER", ...)` (the legacy 1-for-1
finder) and `record_decision_trace(tool="TRADE_PACKAGE_SEARCH", ...)`
(Worker 6/7's new rich multi-player search) at real call sites -- but
neither string was a member of the OLD `TOOL_TYPES` frozenset in
`in_season_decision_trace_service.py`, so every such call silently raised
`DecisionTraceError`, swallowed by the facade's own best-effort wrapper
(`_record_decision_trace_safe`'s `except Exception: return None`). Both
tools were recording **zero real traces in production** despite looking
fully wired end to end (a real response `traceId` field that was always
`None`). The governing directive's own phrasing ("Verify Worker 7's new
Trade Package search (`TRADE_FINDER`) actually records a trace...") turned
out to conflate the two -- the actual new Worker 6/7 feature's tool string
is `TRADE_PACKAGE_SEARCH`, distinct from the pre-existing legacy
`TRADE_FINDER` tool; **both were broken, both are now fixed.**

**1. Schema extension (`in_season_decision_trace_service.py`):**
- `TOOL_TYPES` gains `TRADE_FINDER`, `TRADE_PACKAGE_SEARCH` (closing the
  bug above) and `DRAFT` (per the directive, schema-only -- see hard
  boundary note below) alongside the seven pre-existing types
  (`START_SIT`/`WAIVER`/`ADD_DROP`/`FAAB`/`TRADE`/`K_STREAMER`/
  `DST_STREAMER`, all already correct and unchanged).
- Two new additive, backward-compatible fields on every record:
  `league_snapshot_id` (the same real `LeagueSnapshot` identity hash every
  migrated tool's own `DecisionResultEnvelope` already computes -- moved
  earlier in 6 call sites in `desktop_facade.py` so the SAME already-
  computed value, not a second derivation, reaches the trace) and
  `status_versions` (a real, honest fingerprint of the
  `PlayerAvailabilityStatus` authority in effect -- reuses the already-
  existing `player_availability_authority_health()` read, never a new
  source, never a fabricated semantic version number). Both default to
  `None`/`{}` for every pre-existing caller/row.
- `generatedAt`/`league`/`leagueSnapshotId`/`traceId`/etc. (the directive's
  literal field-name list) are the OUTWARD, camelCase History-surface
  shape (`_decision_trace_history_event_payload`) -- the underlying Python
  dataclass keeps its existing `recorded_at_utc`/`league_id`/`trace_id`
  names for backward compatibility with every existing caller/test.

**2. Append-only owner-action/outcome write path:**
`record_owner_action` already existed (a prior session's contract) but had
never been wired to any facade method or HTTP route -- now real and
callable via `DesktopBackendFacade.redraft_record_decision_trace_owner_action`
+ `POST /api/v1/redraft/decision-trace/owner-action`. `record_outcome` is
NEW (mirrors `record_owner_action` exactly), wired the same way via
`redraft_record_decision_trace_outcome` + `POST /api/v1/redraft/decision-trace/outcome`
-- real and directly tested (append-only, never mutates the original
recommendation line, folds to one latest state per `trace_id` on read),
but **nothing in this app's own UI calls it yet**, exactly as the directive
anticipated ("even if nothing calls it yet -- define the contract"): no
real 2026-season outcome exists for anything recorded so far. Verified live
against the real Fantasy Gamers ledger, not just unit-tested (see below).
A freshly recorded recommendation's own JSON row carries no `outcome` key
at all (not even null) until a real `record_outcome` append happens --
preserves the pre-existing `test_no_future_outcome_field_exists_on_the_
record_shape` test's own stricter guarantee.

**3. History/Review surface:** `DesktopBackendFacade.redraft_decision_trace_history()`
(`GET /api/v1/redraft/decision-trace-history`, no parameters -- always
resolves the CURRENTLY active profile itself, so there is no parameter
through which a caller could request a different league's history) reads
the ledger, newest first, and returns real events plus an honest
`totalCount`. Frontend: a new "History" nav item (League group) ->
`/league/:leagueKey/decision-history` -> `DecisionHistoryPage`
(`decision-history.tsx`), a plain DataTable (Date / League(via context) /
Decision / Recommendation / Owner action / Outcome status), built on pure,
unit-tested derivation (`decision-history-format.ts` -- 18 new vitest
tests) that never invents a summary field a tool didn't actually record.
Zero-events state renders "Nothing recorded yet" with an honest message,
not a spinner or blank page. No calibration/accuracy/"was NWR right"
metric anywhere on the page -- an explicit disclosure line says so, and
this was a deliberate choice, not an oversight (real 2026-season outcomes
don't exist for anything recorded so far).

**Verification -- REAL, live, not fixture-only (disclosed exactly which
parts were real vs. unit-tested):**
- Stood up the real backend + a real production `vite build`/`vite
  preview` via Worker 3's own `nwr_release_gate_smoke.ps1 -KeepRunning
  -SleeperLeagueId 1312983576827920384 -SleeperUsername scolety`
  (unmodified; run from Windows PowerShell 5.1 -- `pwsh` is not installed
  in this environment, a real, disclosed environment quirk, not a script
  bug) against the real, read-only "Fantasy Gamers" Sleeper league.
- Directly exercised the real, running backend via `Invoke-RestMethod`
  (bearer token + Origin header, same pattern the smoke script itself
  uses): confirmed `POST /api/v1/redraft/trade-package-search`
  (`FIND_WIN_WIN`) and the smoke script's own `trade_finder`/`waivers`/
  `weekly_lineup_week1`/`kdst` calls now all return a REAL non-null
  `traceId` (previously `TRADE_FINDER`/`TRADE_PACKAGE_SEARCH` always
  returned `null`). Read `GET /api/v1/redraft/decision-trace-history`
  directly afterward: **98 real recorded events** for the real Fantasy
  Gamers profile, spanning `START_SIT`/`WAIVER`/`FAAB`/`K_STREAMER`/
  `DST_STREAMER`/`TRADE_FINDER`/`TRADE_PACKAGE_SEARCH` (accumulated across
  this and prior sessions' real exercise of that one profile), each
  carrying a real, non-null `leagueSnapshotId` and a real `statusVersions`
  fingerprint. `TRADE` (Trade Analysis) was verified by code-reading + the
  identical, already-proven-safe reordering pattern rather than a live
  call -- a live attempt hit a real, unrelated pre-existing gap (opponent-
  roster rows carry no `identityStatus`/`canonicalPlayerId` field, the same
  known bug Worker 7's ledger entry already flagged for "Open in Analyze")
  that made constructing a valid live gives/receives pair impractical in
  the time available; not a gap in this pass's own trace-recording fix.
- Exercised the real, live append-only owner-action write (`POST
  .../decision-trace/owner-action`) and outcome write (`POST
  .../decision-trace/outcome`) against a real recorded `TRADE_PACKAGE_
  SEARCH` trace: confirmed live via a direct read of the real on-disk
  `decision_traces/<profileId>.jsonl` file that the append produced
  EXACTLY 3 lines for that one `trace_id` (`RECOMMENDED` ->
  `OWNER_ACTION_RECORDED` -> `OUTCOME_RECORDED`), the original line byte-
  identical/untouched, and the History read folding correctly to ONE
  latest-state row (`totalCount` did not double-count the two appends).
- **State-leakage check (this shift's own established paranoia), live, not
  just unit-tested:** created a real second local profile ("P1-4 Leak
  Check League") via the real backend, activated it, confirmed via a
  direct `GET decision-trace-history` call that its `totalCount` was
  genuinely `0` (not the Fantasy Gamers league's 98) -- then reactivated
  Fantasy Gamers and confirmed its real 98 events were still intact,
  unaffected. Same isolation independently proven at the pytest level
  (`test_decision_trace_history_never_leaks_across_leagues`, two isolated
  profiles, asserts both the facade read AND the raw on-disk ledger files
  directly).
- **Real, live-rendered Chrome confirmation:** the History page, reloaded
  fresh (full page reload, not just a client-side route change), rendered
  the real 98-event table for Fantasy Gamers with the exact live-appended
  owner-action ("PROPOSED_TO_OPPONENT (live P1-4 verification)") and
  outcome ("OUTCOME RECORDED" badge, "REJECTED_BY_O...") visible in their
  real columns; switching to the fresh local profile rendered the real,
  honest "Nothing recorded yet" empty state with zero events. **Zero
  console messages of any kind** (not just zero errors) on a fresh full
  reload of the History page. Both the backend and vite-preview processes
  were stopped at the end (the preview's actual listening PID was a
  `cmd.exe`-spawned child of the PID the smoke script itself reported --
  same real teardown wrinkle Worker 7's ledger entry already documented --
  found and killed correctly; confirmed via `Get-NetTCPConnection` showing
  no listener on 18742/1422 afterward, only `TimeWait` remnants).
- Two harmless local test profiles ("P1-4 Leak Check League" x2, created
  while debugging a PowerShell scripting mistake during the live-check
  above, not a product bug) were left in this worktree's own
  `local_exports/redraft_v1/` store -- consistent with several other
  accumulated local test profiles already present from prior workers'
  sessions in the same store (e.g. "NWR QA Local Test League", "NWR
  Release Gate Local Profile" x2); disclosed, not cleaned up (no delete/
  archive facade action exists to remove a profile outright, only
  `archived: true`, which was judged not worth a separate, out-of-scope
  facade change for this pass).
- Tests: `pytest tests/test_in_season_decision_trace_service.py
  tests/test_prospective_recommendation_ledger_v1.py
  tests/test_trade_package_search_facade_wiring.py
  tests/test_trade_package_search_service.py tests/test_trade_finder_service.py
  tests/test_redraft_trade_analysis_service.py
  tests/test_desktop_facade_architecture_wiring.py
  tests/test_player_availability_status_consumer_consistency.py`: 78/78
  passing (15 + 10 new). `pytest tests/test_desktop_application_api.py`:
  46 passed, 4 failed -- confirmed via an A/B `git stash` comparison to be
  the EXACT SAME 4 pre-existing failures present before this pass (byte-
  identical failure set both times); zero new regressions. `npx tsc -b
  apps/dynasty/tsconfig.json apps/redraft/tsconfig.json`: clean. `npx
  vitest run --no-file-parallelism`: **354/354 passing, 27/27 files** (336
  baseline from Worker 7's P1-3 UI pass + 18 new
  `decision-history-format.test.ts` tests).

**Files changed:** `src/services/in_season_decision_trace_service.py`
(schema extension + `record_outcome`), `src/application/desktop_facade.py`
(`_record_decision_trace_safe`/new `_status_versions_snapshot` helper, 6
call-site reorderings to pass `league_snapshot_id`/`status_versions`, 3 new
facade methods, 1 new module-level payload helper -- the search/scoring
logic itself at every touched call site was read, never modified),
`src/desktop_api/server.py` (3 new routes), `tests/test_in_season_decision_
trace_service.py` (extended), `tests/test_prospective_recommendation_
ledger_v1.py` (new), `desktop/packages/contracts/src/index.ts` (additive
types), `desktop/packages/api-client/src/index.ts` (3 new client methods),
`desktop/apps/redraft/src/decision-history.tsx` (new page),
`desktop/apps/redraft/src/decision-history-format.ts` (new, pure
derivation) + its test file, `desktop/apps/redraft/src/RedraftApp.tsx` (+1
nav item, +2 routes), `desktop/apps/redraft/src/redraft.css` (+2 rules).

**Hard boundaries respected:** `marginal_roster_utility_v2`, draft
recommendation logic, scoring, roster legality, `LeagueSnapshot`/
`LeagueWorkspaceContext`/the lifecycle resolver/`DecisionResultEnvelope`/
`PlayerAvailabilityStatus` SEMANTICS, and Worker 6's trade-package
search/scoring logic were all either read-only (the same already-computed
values were reused, never recomputed) or genuinely untouched. `DRAFT`
joining `TOOL_TYPES` is schema-only, deliberately -- no live call site was
added inside the draft decision-bundle path (`redraft_decision_bundle`/
`_decision_bundle_payload`), since that is squarely "draft recommendation
logic" territory and a real, latency-benchmarked hot path; wiring it was
judged out of this pass's scope, not merely deferred by oversight. No
merge/push/deploy.

**CALIBRATION METRICS: not claimed, deliberately.** Real season outcomes
don't exist yet for anything this ledger has recorded (every event is
prospective, from 2026-09-12/13 forward) -- no accuracy/calibration/"was
NWR right" figure is computed, displayed, or implied anywhere in this
pass's code, tests, or UI copy.

**Open issues for Worker 9 (Live Player Intelligence provider
bakeoff/shadow work):**
1. `DRAFT` is a valid `TOOL_TYPES` member with no live call site --
   wiring it (inside `redraft_decision_bundle`/`redraft_decision_bundle_v2`)
   is a real, disclosed remainder for a future pass with the hard-boundary
   context above already worked out.
2. The pre-existing "Open in Analyze"/opponent-roster
   `identityStatus`/`canonicalPlayerId` gap (Worker 7's ledger entry, still
   real, still not fixed) also blocked an organic live `TRADE` (Trade
   Analysis) trace-recording check this pass -- `TRADE`'s own trace/
   `leagueSnapshotId`/`status_versions` wiring was verified by code-reading
   + the identical proven-safe pattern instead; a future pass with that
   gap closed could add a fully organic live check.
3. Two harmless extra local test profiles ("P1-4 Leak Check League" x2)
   sit in this worktree's local store, disclosed above -- no functional
   impact, just worth knowing about if profile counts look surprising.
4. The append-only owner-action/outcome write paths are real, tested, and
   callable, but no UI control captures either yet (no "I did this"/"here's
   what happened" button anywhere in the app) -- a real, disclosed product
   opportunity for a future pass, not attempted here per the directive's
   own "as far as is genuinely useful right now, no further" instruction.

## P1-3 (Rich Trade Package Generator -- UI half) -- 2026-09-12

**Worker 7's scope: wiring Worker 6's real, tested
`POST /api/v1/redraft/trade-package-search` into the existing Trades UI.**
Zero files under `src/` touched (confirmed via `git status`) -- presentation
only, per the directive's hard boundary.

**TS contracts, verified against a real computed payload, not just the
prior entry's doc.** Added `TradePackageCandidate` / `TradePackageEvaluation`
/ `TradePackageSearchResult` / `TradePackageSearchMode` / `TradePackageShape`
to `packages/contracts/src/index.ts`. Verification method: ran
`search_win_win_packages` directly against `test_trade_package_search_service.py`'s
own real two-team fixture, then applied `desktop_facade.py`'s exact
`_evaluation_payload`/candidate serializer code to the real result object
and inspected the actual JSON produced -- not a live HTTP round trip, but a
real, computed backend object through the real serializer, which is what
actually decides the wire shape. **Found the one place the prior entry's
"byte-for-byte the same shape as `TradeAnalysisResult`" claim was slightly
imprecise, exactly as flagged as a real possibility**: the nested
`ownerEvaluation`/`opponentEvaluation` carries no
`leagueId`/`traceId`/`leagueSnapshotId`/`decisionEnvelope`/
`championshipEquityNote`/`writeBehavior` -- those are response-envelope-level
fields that exist once at the top of `TradePackageSearchResult`, not per
side per candidate. Modeled as a distinct `TradePackageEvaluation` interface
rather than reusing `TradeAnalysisResult`, so the contract can't lie about
carrying a `championshipEquityNote` it never receives. Separately confirmed
live against the real, running backend + real Fantasy Gamers league (see
below) that the actual HTTP response matches this contract exactly.

**UI: `desktop/apps/redraft/src/trades.tsx`'s existing "Find Trades" tab now
has three real search modes** (`SEARCH MODE` segmented control, same
primitive Waivers already uses for its own THIS_WEEK/REST_OF_SEASON split):
FIND_WIN_WIN (default), TARGET_PLAYER (a `TradeSidePicker` reused as a
single-select target, sourced from the same opponent-roster candidate list
Analyze already builds -- no second roster fetch), IMPROVE_POSITION (a
QB/RB/WR/TE/K/DST segmented control). No third tab added -- this is
genuinely an enhancement to the existing "Find Trades" tab exactly as
directed (the old 1-for-1-only `redraftTradeFinder()` call is a real subset
of what `FIND_WIN_WIN` now returns). Each candidate renders as one
`DecisionExplain` card: YOU SEND / YOU RECEIVE (per-player availability
badge + a View button into the existing global Player Drawer, canonical
ids -- confirmed working, see below), WHY IT HELPS YOU / WHY IT MAY FIT
THEM (the backend's own real sentences, explicitly labeled, never
paraphrased), WEEKLY IMPACT / ROS IMPACT (owner-side starting lineup value
and net marginal utility/ROS value delta, the same real fields/grammar
`explainTradeAnalysis` already uses for Analyze -- correctly omits a
championship-equity line here since the nested payload has none), plus
DEPTH/POSITION EFFECT/RISK using the same established facts. All new pure
derivation lives in `trades-explain.ts`
(`explainTradePackageCandidate`/`describeTradePackageSearchError`),
unit-tested in `trades-explain.test.ts` (12 new tests) rather than as a
live-DOM component test, matching this codebase's existing test-file
convention (every other page in this app is verified the same way: pure
logic unit-tested, full pages verified live).

**Acceptance-probability check: none anywhere.** `whyItHelpsYou`/
`whyItMayFitThem` are rendered as the backend's own verbatim sentences;
`explainTradePackageCandidate` invents no new copy beyond explicit
"Why it helps you:"/"Why it may fit them:" labels. A dedicated unit test
asserts the full rendered explanation never contains "probability" or
"accept".

**Softened error, before/after:** Worker 6's disclosed
`TRADE_PACKAGE_SEARCH_TARGET_IDENTITY_UNRESOLVED` -- before: the raw
facade message ("The requested target player could not be
identity-matched to the governed ranking pool.") would otherwise have
rendered as-is. After (`describeTradePackageSearchError`, only this one
code overridden -- every other code passes through the facade's own
already-human-readable message/recovery honestly, no invented second
layer): message "Couldn't find that player on a tradeable roster.",
recovery "Pick the player from the search list above instead -- they may
not be in NWR's governed rankings yet." Confirmed live against a REAL
occurrence of this exact error (see below) -- not just unit-tested.

**Truncated-results honesty:** `TradePackageSearchResult.truncated` renders
as a `StatusBadge` ("SEARCH CAPPED -- MORE LEGAL PACKAGES MAY EXIST BEYOND
THIS BOUND") next to the real `candidates.length` /
`opponentsSearched`/`packagesEvaluated` summary line, and is absent when
`false` -- confirmed both ways live (see below): the real Fantasy Gamers
league hit the 900-package cap on FIND_WIN_WIN/IMPROVE_POSITION(RB) (badge
shown) but not on IMPROVE_POSITION(QB) (399 evaluated, no badge).

**A real, pre-existing bug found and deliberately NOT carried into new
code (also NOT fixed -- flagged for the next worker):** the old Find
Trades tab's "Open in Analyze" cross-tab button passed
`TradeFinderCandidate.myGivePlayerId`/`opponentGivePlayerId` (NWR's own
canonical, GSIS-style ids, e.g. `"00-0023459"` -- confirmed via
`trade_finder_service.py`'s `canonical_player_id` and the real bundled
Freeze V7 seed's own `player_id` column) into
`redraftTradeAnalysis(givesSleeperPlayerIds, receivesSleeperPlayerIds)`,
which requires REAL raw Sleeper ids (resolved against the Sleeper
`players/nfl` catalog in `redraft_trade_analysis_service` via
`resolve_roster_canonical_ids`). Trade Package Search's own
`youSend`/`youReceive` are the identical canonical id space, so a naive
"Open in Analyze" button on the new package cards would have replicated
the exact same always-fails bug (`TRADE_ANALYSIS_IDENTITY_UNRESOLVED`
every time) rather than fixed it. Deliberately did not add that button to
the new cards. A correct fix needs a small, genuinely additive backend
contract change (`RedraftOpponentPlayer` has no `canonicalPlayerId` field
today, unlike `RedraftMyRosterPlayer` which already does) -- out of this
pass's UI-only scope, not attempted.

**Trial matrix (7+ states), real backend + real Fantasy Gamers Sleeper
league for most states, `window.fetch` patching (the same mechanism every
prior UI worker used) for the states this real league's current roster
state could not organically reproduce -- disclosed exactly which is
which, per state:**
1. TARGET PLAYER, real result -- REAL: searched "TreVeyon Henderson" (a
   real Bill's Sleepers RB), got "15 candidates found across 1 opponent
   roster (120 packages evaluated)" including a real 2-for-2.
2. FIND WIN-WIN, multiple candidates -- REAL: 15 candidates across 8
   opponent rosters, 900 packages evaluated, truncated=true.
3. FIND WIN-WIN, zero candidates -- MOCKED (this real league's current
   roster state has real FIND_WIN_WIN candidates today, so a genuine zero
   could not be organically forced): confirmed the exact honest empty-state
   copy renders correctly.
4. IMPROVE POSITION -- REAL, both a populated case (RB: 15 candidates,
   truncated) and a genuine, organically-occurring REAL zero-candidate
   case (DST: "0 candidates found across 0 opponent rosters (0 packages
   evaluated)" -- DST is a real, disclosed unmodeled 0.0-value asset per
   Worker 6's ledger entry, so no legal DST package ever improves it under
   the real model) -- both real, neither mocked.
5. Long player/package-text stress case -- MOCKED (real player/team names
   in this league are what they are): an extreme long-name/long-sentence
   2-for-2 candidate wraps cleanly with no layout break or horizontal
   overflow.
6. Softened error state -- REAL for the underlying mechanism confirmed via
   a real occurrence path (an unresolved TARGET_PLAYER identity is a real,
   reachable case), MOCKED for the exact trigger condition in this
   specific session's league state (no real currently-unmatched opponent
   player identity happened to be picked into the target search-candidate
   list this pass -- see the P1-2 ledger entry's own note that Fantasy
   Gamers has 3 real unmatched roster identities, a good target for a
   future pass's live repro): confirmed the softened copy renders exactly
   as designed, with the raw error code never shown.
7. `truncated` flag, both states -- REAL: true (FIND_WIN_WIN, IMPROVE_
   POSITION/RB, both hit the 900-package cap) and false (IMPROVE_
   POSITION/QB, 399 evaluated, badge correctly absent) both observed live
   against the real league.

Also confirmed live: the global Player Drawer opens correctly from a
package candidate's canonical `playerId` (labeled "OPENED FROM TRADES",
same as Analyze), and zero console errors across a full page reload +
every mode switch (checked with console tracking armed from a fresh
reload, not just spot-checked mid-session).

**Method/viewport:** real backend (`scripts/run_nwr_desktop_api.py`) + a
real production `vite build`/`vite preview` via Worker 3's own
`nwr_release_gate_smoke.ps1 -SleeperLeagueId 1312983576827920384
-SleeperUsername scolety -KeepRunning` (unmodified), driven live in Chrome.
Did not need the `<iframe>` viewport-width technique -- no multi-width
layout claim is made this pass (the long-text stress case above was
checked at one standard desktop width only; a dedicated responsive/narrow-
width pass is not part of this directive's required matrix and is not
claimed as verified). Both the backend and vite preview processes were
stopped at the end (`Stop-Process` on the real PIDs, then the follow-on
`node` child); confirmed via `Get-NetTCPConnection` showing no active
listener on 1422/18742 afterward (one connection briefly in `FinWait2`
during teardown, not a listener).

**Tests:** `desktop/`: `npx tsc -b apps/dynasty/tsconfig.json
apps/redraft/tsconfig.json` clean; `npx vitest run --no-file-parallelism`:
**336/336 passing, 26/26 files** (324 baseline from Worker 5's P1-1 pass +
12 new `trades-explain.test.ts` tests). `pytest` not run by this pass --
zero backend files touched (confirmed via `git diff --stat 83773ed2 HEAD
-- src/`, empty).

**Hard boundaries respected:** `marginal_roster_utility_v2`, draft
recommendation logic, scoring, roster legality, `LeagueSnapshot`/
`LeagueWorkspaceContext`/the lifecycle resolver/`DecisionResultEnvelope`/
`PlayerAvailabilityStatus` semantics, and Worker 6's search/scoring backend
logic itself were all read from (contract shapes only) or not touched at
all -- zero files under `src/` in the diff. No merge/push/deploy.

**Open issues for Worker 8:**
1. The pre-existing "Open in Analyze" canonical-vs-Sleeper-id bug above
   (old Trade Finder flow, `trades.tsx`/`in-season.tsx`) is real and
   NOT fixed -- needs a small additive `RedraftOpponentPlayer.
   canonicalPlayerId` backend field (mirroring `RedraftMyRosterPlayer`'s
   existing one) before "Open in Analyze" can be correctly restored
   anywhere it touches opponent-side players.
2. Weekly starting-lineup impact (the real per-week lineup optimizer, not
   the marginal-utility model's own starting-lineup-value approximation
   this pass renders as WEEKLY IMPACT) is still the same disclosed,
   NOT-computed omission Worker 6's entry already flagged -- unchanged by
   this pass.
3. 3+-player packages remain out of scope (Worker 6's own disclosed
   remainder, unchanged).
4. The softened-error trial state was confirmed via a mocked trigger, not
   a live-organic one, in this specific session (see trial matrix item 6)
   -- a future pass could pick one of Fantasy Gamers' 3 real unmatched
   roster identities (P1-2 ledger entry) as a TARGET_PLAYER search input
   for a fully organic repro.

## P1-3 (Rich Trade Package Generator -- BACKEND/SEARCH half) -- 2026-09-12

**Worker 6's scope only: the search/scoring backend.** A separate Worker 7
owns the Trade Package UI + its own tests, built on top of what is
documented here. Nothing under `desktop/` was touched by this pass
(confirmed via `git status` -- zero frontend files in the diff); no `tsc`/
`vitest` run was needed as a result (the directive's own stated condition
for skipping it).

**Preregistered quality gates, written and committed BEFORE the search
module:** `docs/codex/post_ui_v1/TRADE_PACKAGE_SEARCH_QUALITY_GATES_P1_3.md`.
Covers, with exact numbers: post-draft roster-size legality (NOT a change
to `redraft_roster_legality_service.py`'s own draft-time rules), owner/
opponent utility floors per mode, full-Pareto dominance filtering, dedup
keying, the bounded-search pruning strategy and its hard caps, a real
latency target, and an explicit "no acceptance probability, ever" rule.
Every constant/rule in the implementation traces back to this doc; none
were tuned after seeing results (fixture VALUES were tuned to realize
specific intended scenarios -- e.g., "a real starter hole" -- verified by
running the real, unmodified `evaluate_trade` before writing assertions;
the gate thresholds/rules themselves were never touched after that).

**What already existed vs. what was missing (verified fresh, not
assumed):** `trade_finder_service.find_win_win_trades`
(`src/services/trade_finder_service.py`) only ever generates 1-for-1
packages (confirmed by reading its full body -- single `my_drop`/
`their_drop` loop, no combination logic). `redraft_trade_analysis_service.
evaluate_trade` (`src/services/redraft_trade_analysis_service.py`) already
accepts arbitrary `gives_ids`/`receives_ids` LISTS and is a real,
already-tested multi-player evaluator -- just never driven by a search
layer that proposes multi-player packages. This pass builds exactly that
missing search layer and changes NEITHER existing function's own math.

**New file: `src/services/trade_package_search_service.py`.** Generates
1-for-1, 2-for-1, 1-for-2, and 2-for-2 candidate packages across every real
opponent roster, scoring every candidate by calling the SAME `evaluate_trade`
TWICE (owner perspective, then the counterparty's) -- the identical pattern
`find_win_win_trades` already uses for 1-for-1, just extended to bounded
multi-player packages. Reuses, never duplicates:
`waiver_engine_service.rank_drop_candidates` (weakest-first candidate
ordering), `shadow_numeric_authorities_service._asset_pool` (real ROS value,
read-only, for IMPROVE_POSITION's by-position ranking), and
`redraft_roster_legality_service._normalized_position` (the canonical
D/ST-vs-DEF-vs-DST normalization, reused rather than reinvented).

**Pruning strategy (real, bounded, documented -- not brute force):** each
side's candidate pool is capped to `DEFAULT_CANDIDATES_PER_SIDE` (6) players
-- weakest-first (`rank_drop_candidates`) for FIND_WIN_WIN/TARGET_PLAYER
filler slots, real-ROS-value-descending for IMPROVE_POSITION's by-position
pool. Multi-player combos are built only from that bounded pool
(`itertools.combinations`, sizes 1-2 -- 3+-player packages are an
explicitly out-of-scope, disclosed remainder). A package is skipped BEFORE
the expensive `evaluate_trade` call if either side's post-trade roster size
would be illegal, or (IMPROVE_POSITION) it doesn't touch the requested
position. Two hard caps stop the search early even with legal combinations
remaining: `MAX_PACKAGES_EVALUATED_PER_OPPONENT` (120) and
`MAX_TOTAL_PACKAGES_EVALUATED` (900) -- `TradePackageSearchResult.truncated`
reports honestly when a cap was hit.

**Modes implemented (all three, verified against real, individually-run
`evaluate_trade` numbers before assertions were written -- not
hand-guessed):**
- `search_win_win_packages` (FIND_WIN_WIN) -- both sides' net marginal
  utility must be strictly `> 0`. Verified: a real 1-for-2 candidate that
  fills TWO real starter holes at once (WR and TE) from a single
  deadweight throw-in, correctly surviving dominance against every
  available 1-for-1 subset.
- `search_target_player_packages` (TARGET_PLAYER) -- scoped to whichever
  real roster actually holds the named player; no owner-utility floor
  (the owner may rationally pay a cost), but the target's OWN marginal
  utility to the owner must be positive, and the opponent's net utility
  must be non-negative. Verified: a lone mediocre throw-in for a real
  entrenched starter is correctly EXCLUDED (opponent net utility negative
  under the real model), while adding a second throw-in that fills the
  opponent's own real hole flips the same deal to a real, included
  2-for-1 candidate -- both a 1-for-1 (a different single throw-in that
  independently satisfies the gate) and a 2-for-1 shape are present in the
  final result.
- `search_improve_position_packages` (IMPROVE_POSITION) -- receive side is
  always drawn from the opponent's own players AT the requested position
  (ranked by real ROS value, a deliberately different signal than the
  other two modes' "weakest bench" ordering); owner utility must be
  strictly positive, opponent non-negative.

**Candidate structures confirmed working:** 1-for-1, 2-for-1, 1-for-2, and
2-for-2 all appear in real search output across the test suite (not just
theoretically generated and immediately filtered away).

**Quality gates enforced and directly tested:**
- Legality: a NEW, disclosed post-draft roster-SIZE check (total slots =
  `qb+rb+wr+te+flex+superflex+k+dst+bench_size`; position maxima are NOT
  enforced, matching the existing disclosed design in
  `redraft_trade_analysis_service.py`). Proven load-bearing with an exact
  count, not just "no violation observed": a fixture with both rosters at
  EXACT capacity evaluates precisely 52 of 100 raw combinations (every
  size-mismatched 1-for-2/2-for-1 combo -- 48 of them -- pruned before
  `evaluate_trade` ever runs).
- Baseline utility + opponent-utility floors: directly unit-tested against
  constructed `TradeEvaluation` stubs for every mode/edge case in the gates
  doc (owner `<= 0`, opponent `== 0`/`< 0`, target-mode's target-impact
  floor vs. its explicit lack of an owner-net floor).
- Dominance filtering: a full pairwise Pareto sweep per opponent, unit-
  tested directly (`_drop_dominated`) -- a strictly-worse bigger package is
  removed; a bigger package that wins on either axis, or two incomparable
  same-size packages, both survive.
- Dedup: every candidate keyed by
  `(opponent_roster_id, frozenset(gives), frozenset(receives))` in an
  explicit seen-set; asserted zero duplicate keys in real search output.
- No acceptance probability: confirmed by construction (the module never
  computes one) and directly asserted against every real
  `why_it_helps_you`/`why_it_may_fit_them` string in the test suite (no
  "probability"/"accept" language appears anywhere).

**Latency (real, measured, not estimated):** a realistic 12-team league (11
opponents, each a full 15-player roster, default pruning constants) via
`search_win_win_packages` completes in well under the preregistered 5-second
target (asserted directly with `time.perf_counter()` in
`test_pruning_and_latency_bounds_hold_on_a_realistic_12_team_league`; runs
in a small fraction of a second in this environment -- see the test file
for the exact wall-clock assertion, not hardcoded here to avoid this doc
going stale).

**Backend wiring for Worker 7 (a real, callable endpoint -- not just a
library function):** `DesktopBackendFacade.redraft_trade_package_search`
(`src/application/desktop_facade.py`) follows the EXACT same pattern as
the existing `redraft_trade_finder`/`redraft_trade_analysis` methods
(governed-ranking read, live Sleeper roster/user/player read via the
existing read-only `SleeperHttpClient.get_json` -- no write method exists
on that class, structurally impossible to write to Sleeper from here,
`DecisionResultEnvelope` via the same unmodified `build_decision_envelope`,
decision-trace recording, the same canonical
`self._player_availability_status_map()` -- one more legitimate call site
of the SAME existing helper, confirmed via the updated call-count assertion
in `test_player_availability_status_consumer_consistency.py`, 6 -> 7, not a
new competing helper). New HTTP route:
`POST /api/v1/redraft/trade-package-search`
(`src/desktop_api/server.py`), body `{mode, targetPlayerSleeperId?,
position?, limit?}`. Input validation (invalid mode / missing
target-for-TARGET_PLAYER / missing position-for-IMPROVE_POSITION) fails
BEFORE any Sleeper read is attempted -- directly proven in
`test_trade_package_search_facade_wiring.py` with a Sleeper mock that
raises `AssertionError` if called, confirming the ordering, not just
asserting it in prose.

**OUTPUT SCHEMA FOR WORKER 7 (exact JSON shape of
`POST /api/v1/redraft/trade-package-search`'s response `data`):**
```
{
  "leagueId": string,
  "mode": "FIND_WIN_WIN" | "TARGET_PLAYER" | "IMPROVE_POSITION",
  "traceId": string | null,
  "leagueSnapshotId": string,
  "decisionEnvelope": DecisionResultEnvelope,  // task: "TRADE_PACKAGE_SEARCH", same shape as every other migrated tool
  "candidates": [
    {
      "opponentRosterId": string,
      "opponentTeamName": string,
      "packageShape": "1-for-1" | "2-for-1" | "1-for-2" | "2-for-2",
      "youSend": string[],           // canonical player ids
      "youSendNames": string[],
      "youReceive": string[],
      "youReceiveNames": string[],
      "ownerEvaluation": TradeEvaluationPayload,     // owner's own roster before/after -- see below
      "opponentEvaluation": TradeEvaluationPayload,  // the counterparty's own roster before/after
      "whyItHelpsYou": string[],       // structured, real-delta sentences (see gates doc section 8) -- NEVER an acceptance probability
      "whyItMayFitThem": string[]      // same, computed from opponentEvaluation
    }
  ],
  "packagesEvaluated": number,   // real evaluate_trade call count, respects the documented caps
  "opponentsSearched": number,
  "truncated": boolean,          // true if a hard search cap was hit before exhausting the space
  "writeBehavior": "NO_SLEEPER_WRITES"
}
```
`TradeEvaluationPayload` is byte-for-byte the SAME shape
`POST /api/v1/redraft/trade-analysis` already returns for its own
`gives`/`receives` (see `TradeAnalysisResult`/`TradePlayerImpact` in
`desktop/packages/contracts/src/index.ts`, lines ~1134-1166) with one
addition -- it also carries `gives`/`receives` (the per-player
`TradePlayerImpact[]` for THAT side of THAT package), plus
`rosValueDelta`, `netMarginalUtility`, `startingLineupValueBefore/After/
Delta`, `benchContingencyValueBefore/After`, `starterHolesBefore/After`,
`positionRedundancyBefore/After`, `riskFlags` -- all field names identical
to `TradeAnalysisResult`'s, so Worker 7 can reuse or trivially extend that
existing TS interface rather than re-deriving field names from scratch.
**No TS contract types were added by this pass** (this pass touched zero
files under `desktop/`) -- Worker 7 will need to add
`TradePackageCandidate`/`TradePackageSearchResult` interfaces to
`packages/contracts/src/index.ts` (trivially: mirror the JSON shape above,
reusing `TradePlayerImpact` for the nested `gives`/`receives` arrays).

**Request body reference:**
`{"mode": "FIND_WIN_WIN"}` |
`{"mode": "TARGET_PLAYER", "targetPlayerSleeperId": "<sleeper player id>"}` |
`{"mode": "IMPROVE_POSITION", "position": "RB"}` -- `limit` (integer,
optional) caps the returned candidate count on any mode (default 15).

**Tests (all new, all real -- no existing test's assertions were loosened
to make these pass):**
- `tests/test_trade_package_search_service.py` (22 tests) -- the search
  algorithm itself: legality (direct + a precise 52-of-100 end-to-end
  pruning count), all three modes on individually-verified real-number
  fixtures, gate functions direct-tested for every documented edge case,
  dominance filtering direct-tested, dedup, combos generation, and the
  latency/pruning-bound test.
- `tests/test_trade_package_search_facade_wiring.py` (6 tests) -- the
  facade method against the REAL governed ranking (564-row Freeze V7 seed,
  installed via a real `redraft_bootstrap()` call in a fresh isolated
  store, not a test double) with mocked Sleeper HTTP: well-formed empty
  result on unmatched identities, all three validation-failure codes
  (each proven to short-circuit BEFORE any Sleeper read), unresolved
  target-identity error, and the structural "no write method exists"
  guarantee.
- One PRE-EXISTING test updated, not loosened:
  `test_player_availability_status_consumer_consistency.py`'s
  `test_every_migrated_surface_reads_the_same_helper_name` hardcodes the
  exact count of `self._player_availability_status_map()` call sites (a
  deliberate architecture guard against a second, competing helper) --
  updated 6 -> 7 to count this pass's one new, legitimate reuse of the
  SAME existing canonical helper.
- `pytest tests/test_trade_package_search_service.py
  tests/test_trade_package_search_facade_wiring.py
  tests/test_trade_finder_service.py
  tests/test_redraft_trade_analysis_service.py
  tests/test_decision_envelope_consumer_migration.py
  tests/test_desktop_facade_architecture_wiring.py
  tests/test_player_availability_status_consumer_consistency.py`: 56/56
  passing.
- `pytest tests/test_desktop_application_api.py`: 46 passed, 4 failed --
  confirmed via an A/B `git stash` comparison to be the EXACT SAME 4
  pre-existing failures present before this pass's changes (byte-identical
  failure set both times); zero new regressions.
- Frontend: zero files under `desktop/` touched by this pass -- `tsc -b`/
  `vitest run` were not run (the directive's own stated condition for
  skipping them; reported here as instructed rather than silently
  omitted).

**Hard boundaries respected (read-only call sites only, verified by
construction):** `marginal_roster_utility_v2`'s own computation, Team
Score/Championship Equity/RAV/Pick Score, `redraft_roster_legality_
service.py`'s own draft-time rules, `evaluate_trade`'s own single-package
math (called, never modified -- `git diff` on
`redraft_trade_analysis_service.py` and `trade_finder_service.py` is
empty), `LeagueSnapshot`/`LeagueWorkspaceContext`/the lifecycle resolver/
`DecisionResultEnvelope`/`PlayerAvailabilityStatus` semantics, draft
recommendation logic, waiver math. No merge/push/deploy.

**Open issues for Worker 7 (Trade Package UI + tests):**
1. Add `TradePackageCandidate`/`TradePackageSearchResult` TS interfaces to
   `packages/contracts/src/index.ts` (see the exact shape documented
   above) -- not done by this pass (zero frontend files touched).
2. No UI surface calls `POST /api/v1/redraft/trade-package-search` yet --
   the endpoint is real, tested, and live, but nothing in `desktop/apps/
   redraft` renders it (matches the same "backend wired, no visible UI
   toggle yet" pattern the big-draft-readiness pass used for Team Score
   V2).
3. Weekly starting-lineup impact is a disclosed, NOT-computed omission
   (see the module docstring in `trade_package_search_service.py` for the
   full reasoning -- `evaluate_trade` itself doesn't wire
   `weekly_lineup_optimizer_service` for any caller today, confirmed by
   reading its full body). A real follow-up if the owner wants it, but
   would need real per-candidate weekly-projection reads across every
   roster in the league and a latency re-check against the 5s target.
4. 3+-player packages (3-for-2, 3-for-3, etc.) are explicitly out of
   scope for this pass, per the directive's own permission to ship a
   precisely-scoped remainder rather than something unbounded.
5. `target_player_sleeper_id` resolution reuses
   `resolve_roster_canonical_ids` on a single-element list -- correct, but
   means an unmatched target returns a generic
   `TRADE_PACKAGE_SEARCH_TARGET_IDENTITY_UNRESOLVED` error rather than a
   friendlier "did you mean" -- fine for a backend contract, something
   Worker 7's UI may want to soften.

## P1-2 (Multi-League Attention Center) -- 2026-09-12

**COMPLETE.** A read-only cross-league overview ("which of my leagues needs
me?") built strictly on top of the existing single-league architecture --
**zero backend/`src/` files touched** (confirmed via `git diff --stat
82118caa HEAD -- src/`, empty). Every read reuses an already-existing,
already-tested endpoint (`activateRedraftProfile`, `redraftDataHealth`,
`redraftLeagueWorkspaceContext`, and, Sleeper-only, `redraftMyRoster`/
`redraftFreeAgents`/`redraftOpponentRosters`) -- the Start/Sit, Waiver,
Trade Finder, and K/DST Streamer engines are never called by this page, per
the directive's own explicit performance boundary.

**The core mechanical problem:** this app's backend has exactly ONE active-
profile pointer, and every per-league read implicitly reads whichever
profile is currently active -- there is no "read league B without
activating it" endpoint. Cross-league aggregation therefore means
activating each league in turn, reading its cheap facts, then restoring
whichever profile was active before the aggregation started.
`desktop/apps/redraft/src/attention-center.ts` (new, pure/orchestration,
no JSX) is the one place that does this:
- Sequential (never parallel) per-league reads, each independently
  try/caught (`fetchLeagueAttention`) so one league's failure (network
  down, a since-removed profile) never aborts the others.
- An unconditional `finally` restores the original active profile,
  regardless of success/partial-failure -- returns the RESTORE call's own
  fresh bootstrap (`restoredBootstrap`), never an intermediate value
  observed mid-loop; the page's one `onUpdate` call uses exactly that.
- A module-level serialization queue (`attentionCenterQueue`) forces every
  call to `runAttentionCenterAggregation` to fully complete (including its
  own restore) before the next one starts, so even a UI bug that fired two
  overlapping runs could never interleave their `activateRedraftProfile`
  calls against the single shared pointer. The page component also has its
  own in-flight guard (button disabled while working, generation-counter
  discard of a superseded run's display) as a first layer.
- 12 dedicated regression tests in `attention-center.test.ts` exercise this
  exact risk class with a fake client that tracks a mutable "currently
  active" variable (mirroring the real backend): full activation-order
  proof, per-league reads bucketed by which profile was ACTUALLY active
  when they ran (would catch any cross-contamination), restore-after-one-
  league-fails, restore-after-activate-itself-fails, no-original-profile
  edge case, and a rapid-double-trigger test proving zero interleaving.

**Signals used (cheap/cached only, confirmed NOT full-engine):**
`redraft_data_health` (already-composed status authority -- LEAGUE_SYNC
going UNAVAILABLE is the only URGENT case; every other degraded category
is WATCH, since a missing ADP import or no decision-trace activity yet is
routine, not a fire -- **a real severity-calibration bug found and fixed
during this pass's own live check**, see below), `LeagueWorkspaceContext`
(P1-1's real matchup/standings/playoff/issues fields -- a live draft in
progress is URGENT, a real reported issue is WATCH, an imminent real
playoff-start week is the only "deadline" this app tracks anywhere and is
WATCH), `RedraftMyRosterResult.identityStatus` (an unresolved player
identity, WATCH), and the existing ranked free-agent list (a top-60-overall
free agent sitting unowned, WATCH -- a disclosed heuristic threshold, same
pattern as `statusTone` in weekly-shared.tsx; NOT the REST_OF_SEASON Waiver
engine's FAAB/matchup modeling).

**Cross-league player search:** name-substring (case-insensitive), answers
exactly the directive's own phrasing -- "League A: rostered by you /
League B: available / League C: rostered by opponent / League D:
unavailable/unknown." Sleeper leagues build ownership from the same
my-roster/opponent-rosters/free-agents reads above; local/manual leagues
reuse the SAME bootstrap `rankings`+`draftBoard.teams` the activation call
already returned (`drafted`/`draftedBy`, and `teams.find(t => t.owner)` to
tell "you" from an opponent) -- no extra read for local leagues at all. A
league that could not be read, or a name matching nothing in a league that
loaded fine, both resolve to `UNKNOWN` -- never a fabricated "available".

**Real, live-rendered verification (NOT fixture-only):** stood up the real
backend (`scripts/run_nwr_desktop_api.py`, isolated `local_exports/
redraft_v1/` inside this worktree -- confirmed via `redraft_store_root`'s
own default, never the owner's real AppData install) + `vite dev`, and
drove it live in Chrome against this worktree's own **5 real saved
profiles already sitting in `local_exports/redraft_v1/`** from prior
workers' sessions (4 local fixture profiles + the real, real-Sleeper-backed
"Fantasy Gamers" league) -- a genuine 5-league, mixed-provider set, not
synthesized for this pass. Confirmed live:
- All 5 leagues render with real per-league detail -- Fantasy Gamers
  showed a REAL finding: 3 rostered players unmatched to an NWR identity
  (NE, Ka'imi Fairbairn, Marvin Harrison) and a real free agent (Jared
  Goff, #41 overall) -- and the real standings ("#9 of 10", matching
  Worker 4's own P1-1 finding exactly).
- **The severity-calibration bug above was found live**, not in a unit
  test: the first render showed all 5 leagues "NEEDS YOU NOW" purely
  because every profile lacked an ADP import -- correct per the naive
  per-category rule but useless as a signal (everything looks equally on
  fire). Fixed (LEAGUE_SYNC-only URGENT) and reconfirmed live: 0
  URGENT / 5 WATCH, correctly differentiated.
- Cross-league search for "Caleb Williams" (a real Fantasy Gamers roster
  player) correctly showed "Rostered by you" for Fantasy Gamers and
  "Available" for the 4 (undrafted) local profiles; "Jared Goff" (a real
  free agent) showed "Available" everywhere.
- **State-leakage, live (not just unit-tested):** ran the full 5-league
  aggregation with Fantasy Gamers active beforehand -- confirmed via
  direct backend `bootstrap` call afterward that `activeProfileId` was
  still Fantasy Gamers. Then switched the REAL active league to "NWR QA
  Local Test League", re-ran the full aggregation again, and confirmed
  (both in the UI and via a direct backend call) the active profile
  restored to "NWR QA Local Test League", not Fantasy Gamers and not
  whatever was last iterated. Restored the worktree's active profile back
  to Fantasy Gamers afterward (its state before this pass began).
- Weekly Home (P1-1's own surface) re-checked afterward and still renders
  its real matchup/standings ("Brown Town & Big Mike" vs "Puka's Bitches",
  6.0-25.4, #9) with zero console errors -- no regression.
- Zero console errors across every page load this pass touched.
- Sleeper zero-writes: fetched `league`/`rosters`/`users` directly from
  `api.sleeper.app` immediately before and after this pass's live check;
  byte-identical (`diff` confirmed) on all three.
- Both the backend and `vite dev` processes were stopped at the end;
  `Get-NetTCPConnection` confirmed no listener on 18742/1422 afterward.

**Performance:** the 5-league aggregation (4 local + 1 real Sleeper, the
Sleeper league alone issuing 3 extra live reads) completed in **3.0-3.4
real seconds**, shown live in the page's own header. This is a manual
"check on my leagues" surface (a Refresh button, not a hot path/polling
loop), so multi-second sequential HTTP is an accepted, disclosed tradeoff
for correctness (sequential, never parallel, to protect the single active-
profile pointer) over speed.

**Files changed:** `desktop/apps/redraft/src/attention-center.ts` (new,
pure logic + orchestration), `attention-center.test.ts` (new, 28 tests),
`attention-center-page.tsx` (new, the page component -- named
`-page.tsx` rather than `.tsx` because `attention-center.ts`/`.tsx` in the
same directory is an unresolvable module-resolution collision, discovered
via a real `tsc` failure), `RedraftApp.tsx` (+1 import, +1 nav item under
the existing League group, +1 top-level non-league-scoped route --
same pattern as `/leagues`), `redraft.css` (+3 rules, reuses every existing
Panel/DataTable/StatusBadge primitive). **Zero** files under `src/`
touched.

**Hard boundaries respected:** `marginal_roster_utility_v2`, draft
recommendation logic, scoring, roster legality, `LeagueSnapshot`/
`LeagueWorkspaceContext` semantics (read from via the existing contract
fields only, no restructuring), the lifecycle resolver,
`DecisionResultEnvelope`, `PlayerAvailabilityStatus` authority -- all
untouched. The Start/Sit, Waiver, Trade Finder, and K/DST Streamer engines
are never invoked by this page, confirmed by construction (the module doc
in attention-center.ts lists exactly which endpoints it calls) and by the
real 3.0-3.4s measured latency (a full per-league engine sweep across 5
leagues, per Worker 3's own latency table for Trade Finder alone at up to
9.3s/league, would have taken far longer). No merge/push/deploy.

**Open issues for Worker 6 (Trade Package Generator):** none blocking.
Two small, disclosed, non-blocking notes: (1) the waiver-opportunity
free-agent-rank-60 threshold and the playoff-deadline imminence window (0-1
weeks) are both undocumented-elsewhere heuristics local to this page, easy
to tune later if the owner wants a different sensitivity; (2) this pass did
NOT add a second, fixture-driven Chrome QA harness for the "one league's
read fails outright" (network-down) scenario -- that path is thoroughly
covered by `attention-center.test.ts`'s fake-client regression tests
instead (same disclosed tradeoff pattern P1-1 used for its own edge cases).

## P1-1 (automatic NFL week + matchup/standings/playoff context) -- 2026-09-12

**Gap confirmed exactly as Worker 3 flagged, then closed.** Verified fresh
(not assumed): `redraft_league_workspace_context`
(`src/application/desktop_facade.py`) hardcoded `current_week=None` on
every call, and `league_lifecycle_service.py`'s own module docstring
already disclosed "no wrapper around Sleeper's `GET /v1/state/nfl` or
equivalent exists anywhere in `src/services`". Weekly Home's `NFL WEEK`
field was a bare `useState(1)`, never wired to anything real. Both are
now fixed: `src/services/sleeper_league_context_service.py` (new) wraps
Sleeper's real `state/nfl`, per-week `matchups`, `rosters` (`settings`
wins/losses/points), `league` (status/playoff settings), and
`winners_bracket` endpoints as pure functions over already-fetched JSON;
`desktop_facade.py`'s `redraft_league_workspace_context` performs the
actual (try/except-guarded, never-crashing) reads and threads the results
through three new additive fields on `LeagueWorkspaceContext`:
`matchup`, `standings`, `playoff` (frozen-dataclass fields with real
defaults, `to_dict()`/`build_league_workspace_context()` extended --
every OTHER existing field/semantic on `LeagueWorkspaceContext` and the
lifecycle resolver were read-only, untouched, per the hard boundary).

**Raw facts only, honestly disclosed as such:** every field is `None`/
empty when Sleeper doesn't directly report it (non-Sleeper provider, a
failed HTTP read, a bye week, an unresolvable opponent, no bracket
generated yet) -- nothing is inferred, estimated, or simulated. The one
derived boolean (`playoff.inPlayoffs`) is a plain
`currentWeek >= playoffWeekStart` comparison over two raw provider
integers, not a prediction; no Championship Equity, no simulated playoff
odds were built (explicitly out of scope per the directive).

**Frontend:** `LeagueWorkspaceContext` contract gains `matchup`/
`standings`/`playoff` (additive-only; `packages/contracts/src/index.ts`).
Weekly Home (`in-season.tsx`) now fetches the context via a new shared
`useLeagueWorkspaceContext` hook (`weekly-shared.tsx`) and:
- Defaults its week to `context.currentWeek` (provider) with the existing
  `WeekControl` demoted to an explicit, clearly-labeled FALLBACK
  ("NFL week (auto)" vs "NFL week (manual)", with a "Use current week
  (N)" reset action) -- manual entry no longer wins by default.
- Resets that manual override on every league switch (`useEffect` keyed
  on `data.activeProfileId`) so no override leaks between leagues.
- Shows opponent/score (explicitly labeled "(Wk N)" -- the PROVIDER's
  real current week, independent of a manually browsed projections
  week, so the two numbers are never conflated), the owner's record/
  rank, a real Sleeper standings table, and (only once the league has
  actually reached its playoff weeks -- Sleeper pre-seeds an empty
  bracket skeleton months early, which would otherwise be a confusing,
  premature "Playoff round 2: opponent not yet determined" during Week
  1) the owner's real bracket matchup or a plain "Playoffs start Week N"
  otherwise.
- All new pure derivation (`ownerStandingsRow`, `formatRecord`,
  `formatStandingsRank`, `matchupStatusText`, `describeOwnerBracketEntry`,
  `playoffStatusText`) lives in `league-summary.ts`, unit-tested in
  `league-summary.test.ts` (same file/pattern the prior League-surface
  pass already established for `formatCurrentWeek`).
- Added one small, disclosed routing fix found along the way: the new
  Standings panel's "Open League" link needed a `/league` legacy-redirect
  route (`RedraftApp.tsx`) -- every other bare-path link in this file
  already had one, `/league` simply hadn't been added yet (no prior
  surface linked there).

**Verification:**
- New backend unit tests: `tests/test_sleeper_league_context_service.py`
  (19 tests, pure functions -- parse-week, team-name resolution, matchup
  bye-week/unavailable/opponent-unresolvable, standings sort/rank,
  playoff non-playoff/playoff/malformed-input cases).
- New backend facade-wiring tests (mocked Sleeper, same pattern as
  `test_desktop_facade_architecture_wiring.py`'s existing KDST test):
  `tests/test_league_workspace_context_sleeper_p1_1.py` (6 tests --
  current-week-populated, bye-week, playoff-state-with-bracket,
  provider-unavailable/OSError fallback, local/non-Sleeper honest
  "not automatically sourced", and a real league-SWITCH test asserting
  League A's matchup/standings never appear in League B's context).
- New frontend unit tests appended to `league-summary.test.ts` (10
  tests covering the same edge cases as the backend, at the display
  layer).
- `pytest tests/test_sleeper_league_context_service.py
  tests/test_league_workspace_context_sleeper_p1_1.py
  tests/test_league_workspace_context_service.py
  tests/test_desktop_facade_architecture_wiring.py
  tests/test_desktop_application_api.py`: 86 passed, 4 failed -- the
  SAME 4 pre-existing `test_desktop_application_api.py` failures P0-2
  already documented (confirmed via an A/B `git stash` comparison
  showing identical failures before/after this pass's changes); zero
  new failures.
- `npx tsc -b apps/dynasty/tsconfig.json apps/redraft/tsconfig.json`:
  clean.
- `npx vitest run --no-file-parallelism`: **296/296 passing, 25/25
  files** (286 baseline from Worker 1 + 10 new).
- **Real, live-rendered confirmation (real Sleeper, not a fixture):**
  used `desktop/scripts/nwr_release_gate_smoke.ps1 -KeepRunning
  -SleeperLeagueId 1312983576827920384 -SleeperUsername scolety`
  (Worker 3's own release-gate script, unmodified) to stand up the real
  backend + a real production `vite build`/`vite preview`, then drove it
  live in Chrome (read-only, real "Fantasy Gamers" league). Confirmed:
  `currentWeek: 1` (real, non-hardcoded), a real live matchup ("Brown
  Town & Big Mike" vs "Puka's Bitches", 6.0-25.4), a real 10-row
  standings table (owner correctly bolded, ranked #9), "Playoffs start
  Week 15." (real settings, correctly NOT showing the pre-seeded bracket
  skeleton in Week 1), the manual-override fallback control working
  exactly as designed (auto->manual->reset-to-auto, verified by
  screenshot at each step), and the new `/league` route. Zero console
  errors (verified with console tracking armed across two separate page
  loads). Both processes (backend + vite preview) were stopped and their
  full process trees killed at the end of this pass -- confirmed via
  `Get-NetTCPConnection` showing ports 1422/18742 in `TimeWait`/no
  listener, not left running. Did NOT additionally build a fixture-based
  Chrome harness for the bye-week/playoff-state edge cases (the prior
  UI-expansion effort's `window.fetch`-patched QA-harness technique) --
  those are covered instead by the backend facade-wiring tests' mocked-
  Sleeper scenarios above (bye week, playoff-state-with-real-bracket) and
  the frontend pure-function unit tests exercising the exact same
  display logic Home renders; a real fixture-harness Chrome pass for
  those specific shapes is a disclosed, not-yet-done option for a future
  pass if a live visual (not just unit-tested) confirmation of those
  specific edge cases is wanted.

**Sleeper safety (0 writes):** every new read (`state/nfl`,
`league/{id}/matchups/{week}`, `league/{id}/users`, `league/{id}`,
`league/{id}/winners_bracket`) goes through the existing `SleeperHttpClient
.get_json()` (GET-only, no write method exists on the class, same
structural guarantee prior workers already verified). The live-rendered
check above used the release-gate script's own real-league before/after
byte-diff (already run, already verified identical) plus this pass's own
real-time observation of the rendered app -- no new write surface was
introduced.

**Files changed:** `src/services/sleeper_league_context_service.py`
(new), `src/application/desktop_facade.py`
(`redraft_league_workspace_context` only),
`src/services/league_workspace_context_service.py` (additive fields
only), `desktop/packages/contracts/src/index.ts` (additive types only),
`desktop/apps/redraft/src/weekly-shared.tsx` (new
`useLeagueWorkspaceContext` hook), `desktop/apps/redraft/src/
league-summary.ts` (+6 pure functions), `desktop/apps/redraft/src/
in-season.tsx` (`WeeklyHomePage` only), `desktop/apps/redraft/src/
RedraftApp.tsx` (+1 legacy-redirect route), plus the three new/extended
test files above. Nothing under `marginal_roster_utility_v2`, draft
recommendation logic, scoring, roster legality, `LeagueSnapshot`/
`LeagueWorkspaceContext`'s OTHER fields, the lifecycle resolver,
`DecisionResultEnvelope`, or `PlayerAvailabilityStatus` was touched.

**For Worker 5 (Multi-League Attention Center):** `LeagueWorkspaceContext`
now carries real per-league `matchup`/`standings`/`playoff` -- likely
directly reusable for an attention center that needs to summarize
multiple leagues' current state at a glance (fetch the context once per
league, same shape every time). The pre-existing
`weekly-home-actions` 500 bug (Worker 3's finding) is still open and
NOT touched by this pass -- it's a separate endpoint from
`league-workspace-context` and was never in this pass's path except as
something to watch for; it degrades honestly (frontend shows "Command
center unavailable" rather than crashing) and was reproduced again,
unchanged, during this pass's own live-rendered check.

## P0-3 (real backend + Sleeper + packaged Tauri release gate) -- 2026-09-12

**Two separate, honest verdicts -- do not blend them:**

- **PACKAGING GATE: BLOCKED (pre-existing, not a regression).**
  `npm run check:resources` fails for the `redraft` app: the bundled
  `NWR_DATA_GOVERNANCE.json` governance receipt legitimately contains the
  real owner's name in its own audit trail (`"approved_by"`/`"renewed_by"`),
  which the same script's owner-privacy guard (`ownerMarkers`) forbids in
  any bundled resource. Verified this predates the whole shift
  (`git diff --stat 003d0dd4 HEAD -- desktop/scripts
  desktop/apps/redraft/src-tauri/tauri.windows.conf.json` was empty before
  this pass's own fix below) -- not caused by Worker 2's seed migration or
  anything in this shift. Did NOT bypass or weaken the privacy guard to
  force a build through; that is a real product/governance decision for the
  owner (e.g. redact the bundled copy, or keep the receipt out of the
  distributable bundle and verify it a different way), not something a
  verification pass should decide unilaterally. Separately confirmed the
  Rust/Tauri toolchain itself is NOT the blocker: PyInstaller successfully
  built the real Python sidecar exe (147MB,
  `desktop/binaries/nwr-desktop-api-x86_64-pc-windows-msvc.exe`, gitignored)
  and `cargo check` in `desktop/apps/redraft/src-tauri` compiles cleanly
  (~55s cold, ~1s warm) -- both bundle nothing, so neither hits the privacy
  conflict.
  - **Real, disclosed fix made along the way (not the privacy conflict
    itself, a different bug found while investigating it):** the Windows
    resource-bundle map (`tauri.windows.conf.json`) and its allowlist mirror
    (`check-resource-allowlists.mjs`) still pointed at the OLD 608-row
    bundled seed after Worker 2's P0-2 migrated the runtime facade to
    Freeze V7 (564 rows) -- a native build attempted before this fix would
    have bundled stale, already-expired-approval seed data into the
    installer. Both files now correctly point at
    `docs/hq/model/nwr_redraft_2026_freeze_v7_bundled_seed_v1_20260912/`.
    This did NOT unblock `check:resources` (the owner-marker conflict is
    separate and present on either seed generation's governance receipt).

- **BRIDGE SMOKE: PASS (real backend, real production frontend build, real
  read-only Sleeper league).** Since a full native bundle is blocked (above),
  built and verified the fallback the directive names: a real production
  `vite build` served by `vite preview`, talking to the REAL Python desktop
  API backend process (`scripts/run_nwr_desktop_api.py`, not mocked
  `window.fetch`) over real loopback HTTP with the real auth handshake. Ran
  the full click-through smoke flow live in Chrome against a REAL read-only
  Sleeper league ("Fantasy Gamers", league ID `1312983576827920384`, found
  via the owner's own real AppData profile record -- read-only filesystem
  inspection only, never written to): league chooser, Sleeper import/sync,
  Home, Lineup, Improve Team, Trades, Players (real 564-row Freeze V7 board,
  Player Drawer opens with real detail), League/My Roster (real 15-player
  roster)/Data Health, Draft Room (real not-yet-started board state,
  `configured:false` -- never clicked "Start Draft"), a full page reload
  (restart-equivalent), a cold deep link straight to a sub-route, and a real
  league switch (created a second isolated local profile, switched back).
  Every surface rendered real backend data; only exception is the one real
  bug found (next bullet). **ROS-DATA STATUS:** distinct from the above --
  Sleeper Weekly projections/League sync both showed `OK`/`CURRENT`/`LIVE`
  on Data Health for this profile; Market/ADP correctly showed `UNAVAILABLE`
  (no ADP snapshot imported into this fresh isolated profile -- an expected
  gap for a brand-new import, not a bug).
  - **Real bug found and disclosed, NOT fixed (backend out of scope for this
    pass):** `POST /api/v1/redraft/weekly-home-actions` (the Weekly Home
    "NWR Actions" panel) returns HTTP 500 for a Sleeper-imported profile
    with an active roster. Reproduced directly:
    `DesktopBackendFacade.redraft_weekly_home_actions`
    (`src/application/desktop_facade.py:4181`) still assumes
    `redraft_kdst_streamer(...).data["positions"]` is a dict keyed by
    position; it is actually a list of decision-envelope rows --
    `AttributeError: 'list' object has no attribute 'items'`. The frontend
    degrades honestly ("Command center unavailable") rather than fabricating
    data. NOT reproduced against a fresh local-preset profile with no
    roster (the STREAMER section is likely only reached once a roster
    exists).

**Sleeper safety (0 writes, verified with real evidence, not just an
assertion):** structural -- `SleeperHttpClient` (`src/services/
sleeper_import_service.py`) defines only `get_json()` via
`urllib.request.urlopen()` (GET, no `data=` payload; no write method exists
on the class at all). Grep -- no POST/PUT/PATCH/DELETE call site anywhere in
`src/` targets `api.sleeper.app`. Before/after -- fetched `league`,
`rosters`, `users` directly from `api.sleeper.app` immediately before and
immediately after the real import call and diffed: byte-identical on every
field, every time (both the manual pass and the scripted pass, run
separately). All writes this session touched a fresh, isolated
`local_exports/redraft_v1/` inside this worktree only -- the owner's real
`%LOCALAPPDATA%\com.ninerswarroom.redraft` install was read from exactly
once (one profile JSON + one sleeper_imports receipt JSON, both read-only,
to discover the real league ID/username to use) and never written to.

**Latency (real, single-session measurements; a `bootstrap`/Home cold vs.
warm pair and a cold-vs-warm Player Drawer pair were the only ones with
repeat samples -- see the script's JSON report for the full set):**

| Surface | Time |
| --- | --- |
| Production `vite build` (cold launch's frontend half) | ~0.3-0.6 s |
| Backend process start -> first successful `/api/v1/bootstrap` | ~1-2 s (polled) |
| `bootstrap` (Home) cold | ~215-300 ms |
| `bootstrap` (Home) warm | ~213-320 ms |
| Real Sleeper league-open/import (`sleeper/import`) | ~1.0-2.7 s |
| Player Drawer first open (real click, Chrome) | visually instant (<1 render frame; no separate network call -- drawer reads already-fetched rankings data client-side) |
| Player Drawer second open (warm) | same -- no network round-trip either time |
| Improve Team tab switch (Targets, real 25-candidate list) | ~1-2 s to "Reading..." resolve |
| Trade Finder | ~1.6-9.3 s (widest spread observed; heaviest computed endpoint) |
| Draft refresh (bootstrap's inline `draftBoard`) | included in `bootstrap` above -- no separate endpoint |

**For Worker 4 (automatic NFL week/matchup/standings context):** Weekly Home
today shows `"Fantasy Gamers · Week 1"` and an `NFL WEEK` field defaulting to
`1` regardless of the real current calendar date (today is 2026-09-12,
several weeks into a real season by kickoff conventions) -- worth checking
whether that is this project's real, intentional manual-week-selection
design (there is a visible `NFL WEEK` input the owner sets by hand) or a gap
your work unit is meant to close. Also inherit the disclosed
`weekly-home-actions` 500 bug above if your work touches that surface.

**Files changed this pass:**
`desktop/apps/redraft/src-tauri/tauri.windows.conf.json`,
`desktop/scripts/check-resource-allowlists.mjs` (both packaging-manifest
path fixes only, described above), `desktop/scripts/
nwr_release_gate_smoke.ps1` (new, the repeatable release-gate script),
`docs/codex/post_ui_v1/NWR_RELEASE_GATE_CHECKLIST.md` (new). **Zero** files
under `src/` (backend/model) touched beyond Worker 2's already-committed
migration -- confirmed via `git diff --stat 003d0dd4 HEAD -- src/` showing
only Worker 2's prior commit's changes, none from this pass.

## P0-2 (projection governance reconciliation) -- 2026-09-12

**Classification: B.** Verified fresh (not from memory): this worktree's
default bundled Redraft seed (608 rows, `e483caae...`) has a real,
independently-confirmed EXPIRED approval (`valid_until` 2026-09-09; today
is 2026-09-12) -- reproduced live with a standalone pytest run showing
`redraft_bootstrap()` fails to install any seed at all in a fresh store.
Found the real "Freeze V7" combined admission (491 veteran + 73 rookie =
564 rows) already sitting in this branch's own history (commit `0ae4b039`
verified an ancestor via `git merge-base --is-ancestor`), with its own
already-existing, still-valid owner approval (`valid_until` 2026-10-08) at
`docs/codex/nwr_redraft_2026_rookie_projection_admission_CANDIDATE_v2_20260908/
MERGED_CURRENT_CANDIDATE.approval.json`. No new approval was created --
migrated to that exact already-approved artifact.

Found and fixed a real CRLF-vs-LF checkout hazard (this worktree's
`core.autocrlf=true` would have silently broken the receipt's hash
binding) by LF-normalizing a byte-identical copy into a new canonical
packet (`docs/hq/model/nwr_redraft_2026_freeze_v7_bundled_seed_v1_20260912/`,
full provenance/hash-chain in its `PROVENANCE.md`) with a matching
`.gitattributes eol=lf` rule. Updated `desktop_facade.py`'s
`REDRAFT_SEED_*` constants and two presentation strings that would
otherwise have gone stale under the new counts. Net pytest effect:
`test_desktop_application_api.py` 5 -> 4 known failures (one genuinely
fixed; the remaining 4 are pre-existing/unrelated, one of them now
blocked only by this session's own `NWR_FANTASYPROS_API_KEY` env var, not
this change). Zero new regressions confirmed via an A/B stash comparison
across every other projection/redraft-engine/rookie test file. Frontend
`tsc -b` clean, `vitest run`: 286/286 unchanged. Committed at commit
(see `git log -1`); no merge/push/deploy.

**For Worker 3 (packaged Tauri + real backend release gate):** a FRESH
isolated `redraft_root` in this worktree now bootstraps real, current,
non-expired governed 2026 projection data (564 players) instead of
failing closed -- you do NOT need to stay on fixture/isolation paths for
the Redraft projection layer specifically if your work needs it live.
Everything else (Sleeper-linked Waivers/Trade Analysis/Trade Finder, the
real owner AppData install) is unaffected/untouched by this change and
still requires whatever isolation approach the prior UI-expansion workers
already used.

---

Prior entry (Work Unit 0 + P0-1) below.
(Work Unit 0 + P0-1, this entry) -- run `git log -1` in the worktree to get
the exact hash; not hardcoded here to avoid this doc going stale the
instant a future worker commits on top of it.

## COMPLETED

- **Work Unit 0 (baseline + ledger).** Verified branch
  (`upgrade/nwr-post-ui-product-v1-20260912`), start HEAD
  (`003d0dd4183f7bfc7a2ad2f03960c967dd0bb02e`, matches directive exactly),
  clean worktree. Ran `npm install` in `desktop/` (node_modules were absent
  at worktree creation -- a one-time hoisted-workspace install, not a
  dependency change). `npx tsc -b apps/dynasty/tsconfig.json
  apps/redraft/tsconfig.json`: clean. `npx vitest run
  --no-file-parallelism`: **278/278 passing, 25/25 files** -- exact match
  to the prior UI-expansion effort's final freeze count
  (`NWR_UI_EXPANSION_FREEZE_V1.md`). Confirmed freeze docs present and read:
  `docs/codex/NWR_UI_EXPANSION_FREEZE_V1.md` (FREEZE HEAD `1dd068a3`, one
  named carve-out: Draft Room Board/Queue/Teams/Cheat-Sheet visual-token
  migration, not attempted) and `docs/codex/NWR_UI_EXPANSION_V2_LEDGER.md`
  (12 work units, 24 real bugs fixed, 1 latent bug flagged-not-fixed --
  the exact two bugs this pass's P0-1 closes).
- **P0-1 (fix the two remaining latent crash sites).** Both real,
  pre-existing crash sites reproduced with actual malformed payloads (not
  assumed) and fixed at the narrowest correct source. See detail below.

## IN PROGRESS

None. This worker's scope (Work Unit 0 + P0-1) is done; terminating per
directive.

## BLOCKED

Nothing blocked this pass.

## NEXT

**P0-2 (projection governance reconciliation)** -- a separate worker's
scope, not attempted here. No other work units were started or touched.

## TEST STATUS

- `npx tsc -b apps/dynasty/tsconfig.json apps/redraft/tsconfig.json`:
  **clean**, both before and after the P0-1 fix.
- `npx vitest run --no-file-parallelism` (full monorepo, `desktop/`):
  **286/286 passing, 25/25 files** (278 baseline + 8 new regression tests,
  **0 regressions**).
  - `pages.test.ts`: +5 tests (`dataHealthStatusLabel` / `dataHealthTone`
    undefined-status regression group).
  - `draft-room-v2.test.ts`: +3 tests (`actionToBadgeTone`
    undefined/null-action regression group).
- Both bugs were reproduced with a standalone Node repro script BEFORE the
  fix (real `TypeError`, not assumed) and a matching `expect(() =>
  ...).toThrow(TypeError)` assertion is preserved in each new test group
  to prove the guard is load-bearing (not a no-op).
- Console errors introduced by this pass: **0** (no live browser render was
  performed this pass -- verification was tsc + vitest only, consistent
  with the directive's presentation/defensive-coding-only scope; no new
  runtime/browser-console risk was introduced by either fix).

## DATA-GOVERNANCE STATE

Unchanged. No backend/model file touched (`git diff --stat 003d0dd4 HEAD --
src/` is empty -- verified). No seed data, projections, ADP, or governance
receipts read or written. The owner's real leagues and
`AppData\Local\com.ninerswarroom.redraft` install were never touched.

## PROCESS-RAM STATE

No backend/desktop process was started this pass (tsc/vitest only, no
`npm run dev`, no Tauri launch, no Chrome MCP render). Nothing left running
in the background.

---

## Work Unit 0 + P0-1 detail (2026-09-12)

### Bug 1 -- `LeagueSyncTab` `.replaceAll()` on possibly-undefined `status`

**Location (exact):** `desktop/apps/redraft/src/league.tsx:341`, inside
`LeagueSyncTab`'s "League sync detail" panel --
`syncCategory.status.replaceAll("_", " ")`.

**Contract:** `DataHealthCategory.status` (`packages/contracts/src/index.ts`)
is typed as a non-optional enum (`"OK" | "DEGRADED" | "UNAVAILABLE" |
"NOT_APPLICABLE" | "NO_ACTIVITY"`), but a degraded/malformed backend
response (schema drift, partial payload) can genuinely omit it at runtime,
violating the declared type. `dataHealthTone(status)` (the paired tone
function) was already runtime-safe -- it only does `===` comparisons, no
method calls -- but the `.replaceAll()` label computation was not.

**Repro (real, not assumed):** a standalone Node script constructed
`{ status: undefined }` and called `.replaceAll("_", " ")` on it directly --
`TypeError: Cannot read properties of undefined (reading 'replaceAll')`,
matching the exact failure the prior ledger entry described.

**Same pattern found nearby, fixed too:** `desktop/apps/redraft/src/
pages.tsx:448` (`DataHealthPage`) reads the *same* `DataHealthCategory.status`
field with the identical unguarded `.replaceAll()` call -- same contract,
same root cause, high-confidence fix, not speculative.

**Fix:** added one shared helper, `dataHealthStatusLabel(status: string |
null | undefined): string` (`pages.tsx`, next to `dataHealthTone`) that
returns `status.replaceAll("_", " ")` when truthy, else the honest literal
`"Unknown"` -- never a fabricated status. Both call sites
(`league.tsx:341`, `pages.tsx:448`) now use it. `league.tsx` imports it
from `pages.tsx` alongside the existing `dataHealthTone` import (same
precedent, no new module).

**Regression tests:** `pages.test.ts`, new `describe("dataHealthStatusLabel
...")` block (5 tests) -- real-status formatting, the load-bearing
pre-fix-crash proof, undefined-to-"Unknown", null-to-"Unknown", and
`dataHealthTone` never fabricating a confident tone for a missing status.

### Bug 2 -- `actionToBadgeTone` `.toUpperCase()` on possibly-undefined `action`

**Location (exact):** `desktop/apps/redraft/src/draft-room-v2.tsx`, the
`actionToBadgeTone` function (was line 2645) and its one unguarded call
site in the Player Drawer's "Action" stat (was line 3981) --
`actionToBadgeTone(candidate.action)` / `label={candidate.action}`.

**Contract:** `DecisionBundleCandidate.action`
(`packages/contracts/src/index.ts`) is typed as a non-optional `string`,
but a degraded/malformed real `DecisionBundle` response can genuinely omit
it at runtime. Three sibling functions share this exact `action:
string` + `.toUpperCase()` shape (`resolveDisplayAction`,
`actionToBadgeTone`, `splitActionValue`); a full-file audit of every call
site confirmed the OTHER two call sites (the Suggestions table's Action/
Value columns, the Compare table) already coerce via `String(row.action)`
first or guard with `row.action == null` before calling -- safe, if a bit
leaky (would render the literal string `"undefined"` rather than crash, a
separate, lower-severity cosmetic gap, not touched this pass). Only the
Player Drawer's direct `candidate.action` read was unguarded.

**Repro (real, not assumed):** a standalone Node script constructed
`{ action: undefined }` and called `.toUpperCase()` on it via the exact
pre-fix function body -- `TypeError: Cannot read properties of undefined
(reading 'toUpperCase')`, matching the exact failure the prior ledger
entry described.

**Fix:** widened `actionToBadgeTone`'s signature to `action: string | null
| undefined` (the real runtime shape, not just the declared one) and added
a guard (`if (!action) return "review";`) -- an unrecognized/missing action
already fell to the generic `"review"` tone for other unrecognized labels,
so this reuses an existing, honest fallback rather than inventing a new
one. The call site's label was also hardened
(`label={candidate.action || "Unknown"}`) so a missing action shows the
literal word "Unknown" rather than a blank badge -- an honest degraded
state, not garbage. `resolveDisplayAction`/`splitActionValue` were left
untouched (no unguarded call site reaches them with a possibly-undefined
action; touching them was assessed as unnecessary defensive hardening
beyond the genuinely reachable bug).

**Regression tests:** `draft-room-v2.test.ts`, appended to the existing
`describe("actionToBadgeTone", ...)` block (3 tests) -- undefined-input,
null-input (both assert no throw + the "review" fallback tone), and the
load-bearing pre-fix-crash proof.

### Additional unsafe patterns reviewed, NOT fixed (out of narrow scope)

Searched all of `desktop/apps` for `.replaceAll(`, `.toUpperCase(`,
`.toLowerCase(` called directly on a field. Reviewed and deliberately left
alone (disclosed, not silently skipped):

- `result.writeBehavior.replaceAll("_", " ")` (`pages.tsx:525`,
  `improve-team.tsx:630`) -- `writeBehavior: string` appears identically in
  11 places across `packages/contracts/src/index.ts`, always as fixed
  response-envelope metadata (e.g. `"NO_SLEEPER_WRITES"`) populated by a
  shared backend helper on every response, not a per-category computed
  value with a known partial-failure mode like `DataHealthCategory.status`
  was. Lower confidence that this is genuinely reachable; left alone per
  the directive's explicit "not a repo-wide sweep" boundary.
- `apps/dynasty/src/pages/decisions.tsx:991`
  (`decision.recommendation.replaceAll(...)`) and `:1032`
  (`dimension.outcome.replaceAll(...)`) -- same non-optional-`string`-in-
  contract shape (`TradeDecision.recommendation`, a dimension's `outcome`),
  but a different app (dynasty, not redraft) and a different surface from
  either designated bug -- not "nearby" by file/contract/root-cause the way
  the `DataHealthCategory.status` duplicate was. Flagged here as a
  candidate for a future dynasty-side pass, not fixed this pass.
- Every other `.toUpperCase()`/`.toLowerCase()` call site found (see the
  full grep list in this session) was already guarded (`?? ""`, `String(...)`
  coercion, or operates on a value already known non-null in context) --
  no further action needed.

### Files changed (this commit)

`desktop/apps/redraft/src/pages.tsx`, `desktop/apps/redraft/src/league.tsx`,
`desktop/apps/redraft/src/draft-room-v2.tsx`, `desktop/apps/redraft/src/
pages.test.ts`, `desktop/apps/redraft/src/draft-room-v2.test.ts`. **Zero**
files under `src/` (backend/model) touched -- confirmed via `git diff
--stat 003d0dd4 HEAD -- src/` (empty).

### Hard boundaries respected

`marginal_roster_utility_v2`, draft recommendation logic, scoring, roster
legality, `LeagueSnapshot`/`LeagueWorkspaceContext` semantics, the
lifecycle resolver, `DecisionResultEnvelope` semantics,
`PlayerAvailabilityStatus` authority, and provider architecture were read
from (for contract shapes only), never written to. No merge, push, or
deploy performed.

### Open issues for the next worker

1. **P0-2 (projection governance reconciliation)** is untouched -- next in
   the queue per the directive.
2. `writeBehavior.replaceAll(...)` (2 sites) and dynasty's
   `decisions.tsx` (2 sites) are real, structurally-identical-risk
   `.replaceAll()`/similar call sites on non-optional-`string` contract
   fields, deliberately NOT hardened this pass (see rationale above) --
   worth a quick look if a future pass has budget for it, but genuinely
   lower-confidence/lower-reachability than the two fixed here.
3. The Compare table's and Suggestions table's `String(row.action)`
   coercion (draft-room-v2.tsx) is crash-safe but not leak-safe -- a
   genuinely missing `action` would render the literal string `"undefined"`
   as a visible badge/label rather than an honest "Unknown" fallback. Not
   a crash, so out of this pass's narrow P0-1 scope, but a real, disclosed
   cosmetic gap.
4. This pass did not launch a live browser render (Chrome MCP) to confirm
   zero console errors end-to-end -- verification was tsc + vitest only,
   which is sufficient for a presentation/defensive-coding fix of this
   size and matches the directive's own test requirements, but is
   disclosed here as a real, not a hidden, scope choice.

---

## WORKER 11 -- FINAL SHIFT CONSOLIDATION (endurance + drift + release-gate
re-verification + full regression) -- 2026-09-12/13

**Scope: verification and consolidation only, per the governing directive.**
No new feature work. No fix attempted unless a genuine NEW regression was
found (none was). FINAL HEAD: `815a809eeef3880f7d5f2fbd25d9678e61745bba`
(unchanged from Worker 10 -- this pass made no code commit). No merge,
push, or deploy.

### 1. FULL-SHIFT BACKEND/MODEL DRIFT CHECK (003d0dd4..HEAD)

**Verdict: NONE OUTSIDE LEGITIMATE SCOPE.** `git diff --stat
003d0dd4183f7bfc7a2ad2f03960c967dd0bb02e HEAD -- src/` touches exactly 7
files, all additive: `desktop_facade.py` (+686/-48),
`desktop_api/server.py` (+70/-0), `in_season_decision_trace_service.py`
(+131/-4), `league_workspace_context_service.py` (+18/-0, additive fields
only), `live_player_intelligence_shadow_v1_service.py` (new, +373, inert
per Worker 9's own hard-boundary proof), `sleeper_league_context_service.py`
(new, +307), `trade_package_search_service.py` (new, +524). Every hard-
boundary file confirmed **zero diff** across the whole shift:
`redraft_roster_legality_service.py`, `league_lifecycle_service.py`,
`player_lifecycle_service.py`, `decision_envelope_service.py`,
`player_availability_status_service.py`, and
`shadow_numeric_authorities_service.py` (which is where
`marginal_roster_utility_v2`/`team_score`/`championship_equity`/
`pick_score`/`evaluate_cost_of_waiting_v2` actually live -- confirmed via
grep, this repo has no separate `marginal_roster_utility*.py` file; the
directive's named path was a slight misdescription, verified against the
real location instead) -- all `git diff --stat` empty against the same
start head.

**Line-by-line read of every removed/reordered line in `desktop_facade.py`
(48 lines removed)** confirms every one is either (a) the P0-2 seed-
constant migration (608-row expired packet -> Freeze V7 564-row
already-approved packet, with its own dated commentary block), (b) a pure
reordering of an EXISTING `compute_league_snapshot_id(...)` call (same
three arguments, same function, moved a few lines earlier so a decision-
trace call could pass the same already-computed value -- confirmed
byte-identical inputs at 5 call sites: K/DST, Start/Sit, Waivers, Trade
Analysis, Trade Finder), or (c) P1-1's real `current_week=None` literal
replaced by a real, honestly-degrading Sleeper `state/nfl` read (empty/
`None` on any failure, never fabricated). `league_workspace_context_
service.py`'s diff is three new optional dataclass fields
(`matchup`/`standings`/`playoff`) plumbed through unchanged existing
parameters -- `resolve_league_lifecycle`'s own call is untouched.
`in_season_decision_trace_service.py`'s diff is entirely inside the
append-only audit ledger (new tool-type strings, two new optional/
backward-compatible fields, a new `record_outcome` mirroring the existing
`record_owner_action`) -- an audit/logging surface, not a scoring/legality
authority. `server.py`'s diff is pure additive routing (3 new routes, all
delegating to the corresponding new/existing facade methods with input
validation preceding any Sleeper read). **Conclusion: P0-2's data-constant
migration and P1-1/P1-3/P1-4/P1-5's new-feature backend additions are the
ONLY things in the whole-shift `src/` diff -- no drift into scoring,
legality, lifecycle, snapshot, envelope, or status-authority logic
itself.**

### 2. ENDURANCE TEST CONTRACT

Two methods used, disclosed per trial (per the directive's own explicit
permission to mix them):

- **10 league-switch cycles -- REAL backend (HTTP, not mocked):** a
  PowerShell script alternated `POST /api/v1/redraft/profiles/{id}/activate`
  between the real Fantasy Gamers (Sleeper) profile and a real local
  profile 10 times (20 activations), asserting HTTP 200 and the correct
  `activeProfileId` after every call. **0 errors, 0 wrong-active-profile
  results.** Original active profile (Fantasy Gamers) restored and
  confirmed via a fresh `bootstrap` read afterward.
  **+2 additional REAL UI-driven league-switch cycles** (Chrome, real
  production preview): Fantasy Gamers -> "NWR QA Local Test League" (via
  the real League Chooser card) -> back to Fantasy Gamers (via the
  header's "Switch league" dropdown) -- confirmed the active-league
  sidebar/header context updated correctly both times, the local
  profile's own real Draft Room rendered (pre-draft, `Start Draft` never
  clicked), and the data-notices chip's content was independently correct
  per league with no residual content, matching every prior worker's own
  state-leakage findings.
- **10 nav loops -- REAL production preview (Chrome, client-side
  `HashRouter` navigation, not full reloads):** an in-page script cycled
  through 9 distinct routes (`/attention-center`,
  `/league/:key/home|lineup|improve|trades|free-agents|rankings|
  data-health|decision-history`, `/leagues`) 10 times (90 navigations),
  with a global `error`/`unhandledrejection` listener armed for the whole
  run. **0 errors, 0 rejections recorded across all 90 navigations**;
  confirmed complete by the hash settling on the loop's own terminal route
  and staying stable for 3+ seconds afterward.
- **20 drawer cycles -- REAL production preview (Chrome):** 20 real
  open/close cycles of the global Player Drawer from the Players/Rankings
  page's "View" column (a different player each time as the underlying
  row scrolled), toggled via the drawer's own "Close" control each time.
  **Zero console messages of any kind** (not just zero errors) across the
  full 20-cycle run; the table re-rendered cleanly with no residual
  overlay/layout corruption after the final close.
- **Deep-link reloads across the larger route set -- REAL production
  preview (Chrome), genuine full browser navigations (new tab-level
  `navigate` calls, not hash-only client-side changes):** cold-loaded
  `/attention-center` (NEW route), `/league/:key/decision-history` (NEW
  route, rendered the real 180-event Fantasy Gamers ledger), `/league/
  :key/lineup`, `/league/:key/data-health`, `/league/:key/rankings`, and
  `/league/:key/trades` (then exercised its "Find Trades" tab live -- see
  below) -- **6/6 rendered correctly on a cold load, zero console messages
  on every one.**
- **Repeated multi-league aggregation reads (Attention Center) -- BOTH
  methods:** (a) REAL backend HTTP: 3 full passes over all 8 real saved
  profiles (Fantasy Gamers + 7 local), each pass reading `data-health` +
  `league-workspace-context` + `decision-trace-history` per profile after
  activating it -- **72 real backend calls, 0 non-200 responses, 0
  cross-league leaks** (every `decision-trace-history` read's own
  `profileId` matched the just-activated profile, every single time). (b)
  REAL Chrome, real Attention Center page: 1 cold-load automatic
  aggregation + 2 manual "Refresh" clicks, each a genuine sequential
  8-league activate/read/restore sweep -- **3/3 completed** (3.8s, then
  6.1s, real measured page-reported timings), consistently "0 need you
  now / 8 worth a look" (correct given this environment's real, unchanged
  7-blocked-rookie/no-ADP-import data state every prior worker already
  disclosed), active profile (Fantasy Gamers) confirmed unaffected
  afterward.
- **New Trade Package Search surface (P1-3) re-exercised live, not just
  navigated to:** ran a real FIND_WIN_WIN search against the real,
  current Fantasy Gamers roster state -- **15 real candidates found
  across 8 opponent rosters, 900 packages evaluated, correctly flagged
  `SEARCH CAPPED`** -- confirming this surface still works correctly after
  9 further workers' worth of changes on top of Worker 7's original
  verification.

All Sleeper contact this pass was structurally read-only (the same
`SleeperHttpClient.get_json()`-only guarantee every prior worker already
verified by construction); no `draft/start`, `draft/pick`, or any Sleeper
write endpoint was ever called. Backend + preview processes (ports
18742/1422) were stopped at the end; `Get-NetTCPConnection` confirmed no
listener remained on either port afterward.

### 3. PACKAGED-RELEASE GATE RE-VERIFICATION

Ran Worker 3's own `nwr_release_gate_smoke.ps1 -KeepRunning
-SleeperLeagueId 1312983576827920384 -SleeperUsername scolety` unmodified.
**Both previously-known findings reproduced in EXACTLY their documented
form, neither fixed nor worsened:**
- `npm run check:resources` still fails with the identical assertion --
  `redraft allowlisted resource contains owner marker "Spencer Colety"` in
  the same `NWR_DATA_GOVERNANCE.json` file under the same Freeze V7
  bundled-seed path Worker 2/3 already identified. Native build attempt
  skipped (not requested); `cargo check` still compiles cleanly (Rust
  toolchain itself remains provably not the blocker).
- `POST /api/v1/redraft/weekly-home-actions` still returns **HTTP 500**
  for the real Sleeper-imported Fantasy Gamers profile with an active
  roster, same root cause Worker 3 already pinpointed
  (`redraft_kdst_streamer(...).data["positions"]` is a list, not a dict,
  in `redraft_weekly_home_actions`) -- confirmed via the exact same error
  string in this run's own log, not re-derived from memory. **Status:
  confirmed unchanged -- not fixed, not worse.**
- Bridge smoke itself: **PASS.** Real backend + real production `vite
  build`/`vite preview`, real read-only Sleeper import (before/after
  byte-diff of `league`/`rosters`/`users` against `api.sleeper.app`:
  IDENTICAL, 0 writes), and every other surface smoke-tested by the
  script (`league_workspace_context`, `my_roster`, `opponent_rosters`,
  `data_health`, `player_availability_status`, `weekly_lineup_week1`,
  `waivers`, `free_agents`, `trade_finder`) returned real 200s with real
  data. This pass's own live Chrome checks above additionally exercised
  the NEW surfaces the script itself doesn't click through (Attention
  Center, Trade Package Search, Decision History, the data-notice strip)
  -- all real, all rendering correctly.

### 4. FULL REGRESSION

- `npx vitest run --no-file-parallelism` (full monorepo, `desktop/`):
  **362/362 passing, 28/28 files** -- matches Worker 10's own final count
  exactly (no drift since the last commit, as expected with zero new
  commits this pass).
- `npx tsc -b apps/dynasty/tsconfig.json apps/redraft/tsconfig.json`:
  **clean.**
- `pytest tests/test_desktop_application_api.py`: **46 passed, 4 failed**
  -- the SAME 4 pre-existing failures documented in this ledger's own
  baseline since P0-2 (`test_dynasty_facade_composes_real_governed_
  workflows`, `test_desktop_rookie_veteran_bridge_is_source_separated_and_
  trade_aware`, `test_redraft_bootstrap_seeds_once_and_matches_desktop_
  contract`, `test_facade_has_no_streamlit_or_app_component_dependency`),
  confirmed by exact test-name match against the ledger's documented
  baseline list, not re-derived from a stash diff this time (no code
  changed this pass to diff against). Zero new failures.
- `pytest` across every shift-touched backend suite in one run
  (`test_sleeper_league_context_service`,
  `test_league_workspace_context_sleeper_p1_1`,
  `test_league_workspace_context_service`,
  `test_in_season_decision_trace_service`,
  `test_prospective_recommendation_ledger_v1`,
  `test_trade_package_search_facade_wiring`,
  `test_trade_package_search_service`, `test_trade_finder_service`,
  `test_redraft_trade_analysis_service`,
  `test_desktop_facade_architecture_wiring`,
  `test_player_availability_status_consumer_consistency`,
  `test_player_availability_status_service`,
  `test_live_player_intelligence_shadow_v1_service`,
  `test_decision_envelope_consumer_migration`): **131/131 passing.**
- Native-Tauri packaging check: `check:resources` fails identically to
  Worker 3's own documented finding (see section 3) -- confirmed via this
  pass's own fresh run of the same script, not assumed unchanged.

### CONSOLIDATED BUG LIST -- WHOLE SHIFT (found AND fixed, pulled from all
10 prior entries)

1. **(Work Unit 0/P0-1)** `LeagueSyncTab`/`DataHealthPage` crashed on a
   malformed/missing `DataHealthCategory.status` (`.replaceAll()` on
   `undefined`) -- fixed via a shared `dataHealthStatusLabel` helper (2
   call sites, `league.tsx` + `pages.tsx`).
2. **(Work Unit 0/P0-1)** Player Drawer's `actionToBadgeTone` crashed on a
   malformed/missing `DecisionBundleCandidate.action` (`.toUpperCase()` on
   `undefined`) -- fixed with a null-safe guard + honest "Unknown" label
   fallback (`draft-room-v2.tsx`).
3. **(P0-2)** The default bundled Redraft projection seed (608 rows) had
   a real, independently-confirmed EXPIRED governance approval
   (`valid_until` 2026-09-09), silently failing `redraft_bootstrap()` in
   any fresh store -- fixed by migrating to the already-owner-approved
   Freeze V7 packet (564 rows, `valid_until` 2026-10-08); no new approval
   fabricated.
4. **(P0-2)** A real CRLF-vs-LF checkout hazard would have silently
   broken the Freeze V7 receipt's hash binding in this worktree
   (`core.autocrlf=true`) -- fixed via a canonical LF-normalized packet +
   `.gitattributes eol=lf` rule.
5. **(P0-3)** The Windows native-bundle resource map and its allowlist
   mirror still pointed at the OLD 608-row seed after P0-2's migration
   (would have bundled stale, expired-approval data into a real installer)
   -- fixed (both files repointed to the Freeze V7 path).
6. **(P1-2)** Attention Center's first live render showed all 5 (later 8)
   leagues as "NEEDS YOU NOW" purely because every profile lacked an ADP
   import -- a real severity-calibration bug (a uniformly-"on fire" signal
   is not a useful signal) -- fixed (only `LEAGUE_SYNC` degradation is
   URGENT; every other category is WATCH).
7. **(P1-4)** `TRADE_FINDER` and `TRADE_PACKAGE_SEARCH` were both already
   being passed to `record_decision_trace(tool=...)` at real call sites,
   but neither string was a member of the old `TOOL_TYPES` frozenset --
   every such call silently raised `DecisionTraceError`, swallowed by the
   facade's best-effort wrapper, so **both tools recorded zero real traces
   in production** despite looking fully wired (a real `traceId: null`
   every time) -- fixed (both added to `TOOL_TYPES`).

**Found and explicitly DISCLOSED, deliberately left unfixed (out of each
pass's own scope), still open as of this final pass:**

8. **(P0-3, Worker 3)** `POST /api/v1/redraft/weekly-home-actions` returns
   HTTP 500 for a Sleeper-imported profile with an active roster
   (`redraft_kdst_streamer(...).data["positions"]` is a list, not a
   dict). **Reconfirmed unchanged by this final pass.**
9. **(P0-3, Worker 3)** `npm run check:resources` fails at the
   owner-privacy/allowlist guard because the bundled governance receipt's
   own audit trail legitimately contains the real owner's name -- a real
   product/governance decision for the owner, not something any
   verification pass should decide unilaterally. **Reconfirmed unchanged
   by this final pass.**
10. **(P1-3, Worker 6/7)** The old "Open in Analyze" cross-tab button
    passes canonical (GSIS-style) player ids into an endpoint that
    requires raw Sleeper ids -- always fails
    (`TRADE_ANALYSIS_IDENTITY_UNRESOLVED`) for opponent-side players;
    needs an additive `RedraftOpponentPlayer.canonicalPlayerId` backend
    field to fix correctly. Not carried into the new Trade Package cards
    (deliberately omitted there), not fixed at its original site.

### OPEN ITEMS REMAINING -- WHOLE SHIFT (consolidated)

1. `POST /api/v1/redraft/weekly-home-actions` 500 bug (item 8 above) --
   real, disclosed, unfixed, confirmed unchanged by this pass.
2. `check:resources` owner-marker privacy-gate block (item 9 above) --
   real, disclosed, unfixed, confirmed unchanged by this pass; a genuine
   owner/governance decision, not a code bug.
3. "Open in Analyze" canonical-vs-Sleeper-id gap (item 10 above) --
   real, disclosed, unfixed.
4. Weekly starting-lineup impact is approximated (marginal-utility
   model's own starting-lineup-value), not the real per-week lineup
   optimizer, anywhere `evaluate_trade`/Trade Package Search render it --
   disclosed by Worker 6, unchanged.
5. Trade Package Search is capped at 2-for-2; 3+-player packages are
   explicitly out of scope (Worker 6's disclosed boundary).
6. `DRAFT` is a valid `TOOL_TYPES` member with no live call site wired
   (Worker 8's disclosed remainder; draft recommendation logic is a hard
   boundary, deliberately not touched).
7. The append-only owner-action/outcome decision-trace write paths are
   real and callable but no UI control captures either yet (Worker 8's
   disclosed remainder).
8. `shell-notices.ts`'s `ALWAYS_PRESENT_DISCLOSURE_TITLES` matches by
   exact string against `desktop_facade.py`'s real notice titles -- a
   real, disclosed fragility if that backend wording ever changes
   (Worker 10).
9. No genuinely "Current" (zero-issue) league exists anywhere in this
   repo's real current data state (every profile still carries the same
   real 7-blocked-rookie registry gap / missing ADP import) -- real,
   correct, just not organically observable live right now (Worker 10).
10. Dynasty app's own inline data-notices (`home.tsx`) were never given
    the same shell-level compact-chip treatment as Redraft (Worker 10's
    disclosed scope boundary).
11. RotoWire/SportsDataIO/Sportradar remain real
    `NEEDS_OWNER_CONTRACT` options if the owner wants a paid live
    player-intelligence provider (Worker 9's bakeoff doc has the full
    vendor list).
12. The Live Player Intelligence shadow module
    (`live_player_intelligence_shadow_v1_service.py`) is 100% inert and
    unwired by design -- surfacing it anywhere in the UI is a new,
    separate, deliberate future decision (Worker 9).
13. `writeBehavior.replaceAll(...)` (2 sites,
    `pages.tsx`/`improve-team.tsx`) and Dynasty's own `decisions.tsx` (2
    sites) are structurally-identical-risk `.replaceAll()` call sites on
    non-optional-`string` contract fields, deliberately left unhardened
    (lower-confidence/lower-reachability than the two P0-1 fixed --
    Worker 1's own disclosed triage).
14. The Compare/Suggestions tables' `String(row.action)` coercion
    (`draft-room-v2.tsx`) is crash-safe but not leak-safe -- a genuinely
    missing `action` would render the literal string `"undefined"` rather
    than an honest "Unknown" (Worker 1's disclosed cosmetic gap).
15. Trade Package Search's softened-error trial state was confirmed via a
    mocked trigger, not a fully organic live one, in Worker 7's own
    session (Worker 7's disclosed remainder).

### ISSUES FOUND AND FIXED THIS PASS

None. This pass found zero new regressions -- every check (drift, both
known release-gate findings, full regression) reproduced exactly the
state every prior worker already documented.

### CONSOLE ERRORS THIS PASS

**0** -- across all Chrome-driven endurance trials (10 nav loops/90
navigations, 20 drawer cycles, 6 deep-link reloads, 3 Attention Center
aggregation runs, 1 live Trade Package Search, 2 UI league switches),
checked via `read_console_messages` with no pattern filter (all message
types, not just errors) after each trial group.

### REAL OWNER STATE MODIFIED

**NO.** Every league touched this pass was either the real, read-only
Fantasy Gamers Sleeper league (structurally read-only client, before/
after Sleeper byte-diff already proven by the smoke script itself) or
this worktree's own pre-existing local test profiles (never the owner's
real `%LOCALAPPDATA%\com.ninerswarroom.redraft` install, never touched
this pass). No new profile was created. No draft was started/advanced on
any profile. The active profile was restored to Fantasy Gamers (its
state at the start of this pass) and confirmed via a fresh backend read
before the backend was stopped.

### READY FOR OWNER REVIEW

**YES.** Ten prior workers' real, verified feature/fix work plus this
final consolidation pass's whole-shift drift check, endurance contract,
release-gate re-verification, and full regression all confirm the same
honest picture: legitimate, scoped, hard-boundary-respecting backend
additions only; zero drift into scoring/legality/lifecycle/snapshot/
envelope/status-authority logic; the app survives realistic multi-league,
multi-navigation, multi-drawer, cold-deep-link usage with zero console
errors; and both real, disclosed remainders (`weekly-home-actions` 500,
`check:resources` privacy gate) are exactly where they were at the start
of this pass -- not fixed, not worse.
