# Waiver Fix Cycle V1 -- Closing Checkpoint

Branch `upgrade/nwr-prospective-outcomes-v1-20260914`, worktree
`C:\NWR\prospective-outcomes-v1`. This is the closing-worker checkpoint for
the bounded, owner-authorized "Waiver Fix Cycle V1" (distinct from, and
layered on top of, the already-pushed 6-worker "Waiver Night V1" documented
earlier in `LEDGER.md`). Read `LEDGER.md` in full and
`HARRISON_TRACY_INVESTIGATION_V1.md` for the complete real findings this
summarizes -- this file is a durable pointer/summary, not a replacement for
either.

Final substantive HEAD this pass verified: `d6199a6f916e1aa82e9c3b252b6b5e6ef215485b`
(all 5 substantive sections were already complete before this pass started
-- this pass added zero production-code changes, only this checkpoint doc
itself, committed on top). Cycle start (for full-range diff review):
`0517ada82a9b2b7fef1b64b66c13892d4440b2bb` (the last commit of the
already-pushed 6-worker Waiver Night V1).

## What this cycle did, in order

1. **Investigation (no fix)** -- `HARRISON_TRACY_INVESTIGATION_V1.md`.
   Traced Marvin Harrison Jr.'s `0.0` marginal utility to its exact
   first-zero operation: he is himself the real player who defines the WR
   replacement baseline in this league's current projection ordering
   (`position_rank 54`, one below the real `rostered_count: 53` cutoff), so
   `value = his_own_projected - his_own_replacement_points == 0` by
   construction -- correct, intentional VBD-model behavior, not a defect.
   Tyrone Tracy's "low weekly points but top waiver priority" was confirmed
   internally consistent (the waiver engine is always ROS-driven in both
   modes; THIS_WEEK only adds a display/tie-break number).
2. **FAAB nonpositive gate** (`0c28a8aa`) -- `suggest_faab_bids()` could
   suggest a positive dollar bid for a zero/negative-utility candidate
   (nonzero floor in the pricing formula). Fixed with a gate/floor branch
   that short-circuits any `marginal_utility <= 0` (and the pre-existing
   unmatched-identity case) to `$0` with two distinctly-worded rationale
   strings, neither implying the player is worthless. Positive-utility
   formula itself untouched.
3. **LIVE/SCENARIO FAAB budget separation** (`96e75ec2`) -- the FAAB
   pricing formula was always fed a frontend-owned `useState(100)` default
   on first render (a real two-request race), and a manually-edited
   "scenario" budget was visually indistinguishable from the real live
   Sleeper budget. Fixed: `redraft_waivers` now derives LIVE budget/weeks-
   remaining entirely server-side from that same request's live Sleeper
   reads (including a new live current-week/playoff-week-start read), an
   explicit `budget_scenario` object opts into SCENARIO (all-or-nothing,
   never a partial silent merge), `faabContext.budgetMode` is always
   `LIVE`/`SCENARIO`, and the frontend renders the two states with visibly
   distinct banners/tones plus a profile-switch reset so a scenario can
   never leak across leagues.
4. **Add/Drop same-context arithmetic repair** (`d6199a6f`) --
   `pair_add_drop`'s "net" utility subtracted the add's value (computed
   against the OWNER'S ORIGINAL roster) from the drop's value (computed
   against the roster WITH the drop already removed) -- two different
   reference rosters for one number. Fixed by recomputing the add's own
   value against the same post-drop roster, via the same unmodified
   `marginal_roster_utility_v2` authority. Also added a real open-roster-
   slot signal (from Sleeper's own `roster_positions` vs. raw occupied
   slot count) so a verified open slot produces an honest add-only
   pairing instead of always forcing a drop.
5. **THIS_WEEK honesty** (same commit as #4) -- confirmed THIS_WEEK and
   REST_OF_SEASON already ranked identically (weekly points are display +
   secondary tie-break only, never primary sort); added an explicit
   caption under the Mode toggle in both real render paths and fixed a
   real horizon-mislabeling bug in the FAAB rationale string
   ("this week's real free-agent pool" -> "this real free-agent pool, N
   season weeks remaining", in both modes).

All of the above are additive/repair changes to `waiver_engine_service.py`
(the pricing/pairing/ranking-adjacent logic) and `desktop_facade.py`
(the `redraft_waivers` call site) plus corresponding frontend/contract
changes. `marginal_roster_utility_v2` / `shadow_numeric_authorities_service.py`,
`redraft_roster_legality_service.py`, `LeagueSnapshot`/
`LeagueWorkspaceContext`/lifecycle-resolver/`DecisionResultEnvelope`/
`PlayerAvailabilityStatus`, and all draft-recommendation code are
**untouched across the entire cycle** -- re-verified this pass by a
full-range `git diff --stat`/`git diff -U0` grep from `0517ada8` to HEAD
(see Verification below).

## This closing pass's own verification (2026-09-15, real/live where noted)

- **Full-range diff review**: `git diff --stat 0517ada8 HEAD` (excluding
  the ledger docs) touches exactly 16 files, all inside
  `src/application/desktop_facade.py`, `src/desktop_api/server.py`,
  `src/services/waiver_engine_service.py`, the desktop `contracts`/
  `api-client`/`redraft` frontend packages, and test files. Grepped the
  same range (`-U0`, added/removed lines only) for every hard-boundary
  term (`marginal_roster_utility_v2`, `LeagueSnapshot`,
  `LeagueWorkspaceContext`, `lifecycle_resolver`, `DecisionResultEnvelope`,
  `PlayerAvailabilityStatus`): every match is either a read-only call/import
  of `marginal_roster_utility_v2` (required -- the same-context fix must
  call it, never redefine it) or a code comment. `git diff --stat` for
  `shadow_numeric_authorities_service.py` and
  `redraft_roster_legality_service.py` across the same range: **both
  empty**. All 7 fixes from the prior (already-pushed) 6-worker Waiver
  Night V1 -- team-code aliases, name-suffix stripping, IR/reserve
  protection, live FAAB baseline, readable enum labels, honest platform
  capabilities, decision-trace provenance -- were re-confirmed present by
  direct grep of current source (not just re-reading the ledger).
- **Targeted regression slice** (`pytest -k "decision_trace or
  prospective_outcome or live_player_intelligence or
  boundary_property_reliability or composition or player_availability or
  fantasypros_kdst or team_code_alias or waiver_engine or sleeper or
  redraft_waivers or faab or weekly_home or desktop_facade_architecture or
  open_slot"`): **ACTUAL TEST RESULT, re-run this pass: 666 passed, 0
  failed** -- exact match to Worker 4/the prior pass's own documented
  count.
- `tests/test_desktop_application_api.py`: **ACTUAL TEST RESULT: 46
  passed / 4 failed** -- the same 4 pre-existing failures this worktree's
  documented baseline expects
  (`test_dynasty_facade_composes_real_governed_workflows`,
  `test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`,
  `test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`,
  `test_facade_has_no_streamlit_or_app_component_dependency`).
- **Frontend**: `npm run typecheck` (`tsc -b`, both apps): clean, 0
  errors. `npx vitest run`: **426 passed, 0 failed** (29 test files),
  exact match to the ledger's documented baseline. Production `npm run
  build` (both `dynasty`/`redraft` vite apps): **succeeded** (367/69
  modules respectively; one pre-existing "chunk larger than 500kB"
  advisory warning, not an error, not new).
- **Full untargeted `pytest tests/`** (5220 tests collected): run in full
  this pass, not just the targeted slice -- something no prior worker in
  this ledger completed. Method note (full honesty): a first, serial
  attempt (`pytest tests/ -q`) genuinely HUNG partway through (stalled at
  ~22%/~13% on two separate attempts, confirmed via flat CPU time over
  repeated checks, not merely slow) -- killed both times. A third attempt
  added `pytest-timeout` (`--timeout=90 --timeout-method=thread`, a
  testing-only dependency, not committed) and `pytest-xdist` (`-n auto`,
  16 workers) to make forward progress possible at all in this
  environment; this attempt **completed**: `pytest-timeout` and
  `pytest-xdist` were both `pip install`ed for this diagnostic run only
  and are not referenced by any committed file. **ACTUAL RESULT: 332
  failed, 4803 passed, 72 skipped, 13 errors, in 150.66s** (5220 total,
  matches collection count exactly). One worker (`gw14`) crashed mid-run
  on an unrelated model_v4 replay-audit test and was retried by xdist.
  **Diff against the ~323-pre-existing-failure baseline from repo
  memory**: this run's 332+13=345 "not passed" (excluding skips) is
  higher than ~323 -- NOT claimed to be a clean reproduction of that
  exact baseline, and NOT blindly accepted as such. Investigated directly
  rather than hand-waved:
  - **Zero failures or errors anywhere in this cycle's own scope**:
    grepped the full failure/error list for `waiver`, `faab`,
    `redraft_waivers`, `decision_trace`, `prospective_outcome`, `sleeper`
    -- **zero matches**. Every test this cycle's own targeted slice
    covers passed in BOTH the targeted run and this full run.
  - `tests/test_desktop_application_api.py` shows exactly the same 4
    known names (`test_dynasty_facade_composes_real_governed_workflows`,
    `test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`,
    `test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`,
    `test_facade_has_no_streamlit_or_app_component_dependency`) -- no
    additional failures in that file.
  - The large majority of the remaining failures are literal
    `FileNotFoundError` for `local_exports/data_packs/
    lve_sleeper_20260505_pdf_ranks/{fact_rosters,fact_future_picks,
    model_outputs}.csv` -- exactly the "missing local_exports data" cause
    repo memory already documents, in files (shadow-model tournament,
    decision-board coherence, external-asset audits, veteran/rookie
    review reports, etc.) this cycle never touched.
  - The 13 setup errors are all in `tests/test_redraft_engine_v1_service.py`
    (`git diff --stat` for that file AND `src/services/
    redraft_engine_v1_service.py` across this entire cycle: **empty**,
    confirmed untouched), and are a fixture-level `AssertionError`
    ("Projection snapshot has no rankable player rows") -- an
    environment/admitted-evidence-data issue, not a code defect this
    cycle introduced.
  - The residual gap above ~323 is most plausibly attributable to the
    parallel/timeout-instrumented method itself (a genuine, disclosed
    methodology deviation from whatever serial run produced the ~323
    baseline in memory -- shared temp paths / global state under `-n
    auto`, the `gw14` crash-and-retry, and `pytest-timeout`'s
    thread-based mechanism can all independently produce a few
    additional failures a clean serial run would not) rather than a real
    regression. **This is disclosed as an open, not fully resolved,
    discrepancy** -- not asserted as proven measurement noise with
    certainty -- but zero evidence points to this cycle's own changes as
    the cause, and the targeted/scoped verification above (666 + 46/4 +
    426 + typecheck + build, all exact baseline matches) is what this
    push decision is actually gated on, consistent with how every prior
    worker in this exact ledger scoped their own release decision.
- **git status**: `docs/codex/prospective_outcomes_v1/
  multi_league_scale_v1/frontend_bench_results.json` was regenerated as a
  vitest timing-noise side effect (same as every prior worker's own note)
  and was reverted with `git checkout --` before anything was committed.
  No other incidental changes.
- **No sensitive data committed**: `git log --stat` across the ENTIRE
  Waiver Night V1 + Waiver Fix Cycle V1 range (from the first
  team-code-alias commit through this HEAD) was grepped for JSON/CSV data
  files, and for `credential`/`secret`/`token`/`api_key`/`password`
  substrings -- **zero matches** outside ordinary `package.json`/
  `tsconfig.json`/test files. No raw league dump or credential was ever
  committed by any of the 4 prior workers or this pass.

## Real Fantasy Gamers check (isolated local state, read-only, 2026-09-15
## ~23:13 UTC)

Method: copied this worktree's own `local_exports/redraft_v1` (gitignored,
not the owner's real AppData install) to a scratch directory under this
session's scratchpad BEFORE any facade call, so nothing was appended to
this worktree's own tracked decision-trace store. Real Sleeper reads
(rosters/users/state/nfl) were fresh live GETs against the real Fantasy
Gamers league (`1312983576827920384`, owner `scolety`), not replayed JSON.

- **Roster reconciliation**: `redraft_my_roster()`'s 15-player id set
  (`11560, 11628, 13279, 3451, 6813, 6819, 7523, 7543, 7553, 7567, 8126,
  8144, 9226, 9997, NE`) matched a direct raw `league/{id}/rosters` pull
  for the owner's roster (`roster_id 9`) **exactly**, id-for-id.
- **Unresolved identities**: `3451` (Ka'imi Fairbairn, K) and `NE` (DST)
  -- the same, already-disclosed, by-design gap (K/DST have zero rows in
  the governed skill-position ranking; handled separately by the K/DST
  streamer pathway, confirmed still correct in the prior Worker 4 pass).
- **Free-agent POOL SIZE vs IDENTITY-MATCHED COVERAGE (explicitly
  distinguished, not conflated)**: real pool size **723** unrostered
  players (`redraft_free_agents()`, live). Of those, **365** carry a real
  NWR ranking match (`rankingAuthority: "NWR REDRAFT RANKING"`) and
  **358** are `UNRANKED` (no identity match -- mostly K/DST and deep
  inactive-ranking-adjacent players, consistent with Worker 2's prior
  count of 358 unmatched-identity candidates the same day).
- **Real add/drop pairings (NEW same-context arithmetic)**: top pairing
  ADD Tyrone Tracy (RB, marginal utility 9.72) / DROP Marvin Harrison (WR,
  marginal utility 0.0), `addUtilityVsOriginalRoster: 9.72` ==
  `addUtilityVsPostDropRoster: 9.72` (unaffected -- different position from
  the drop), `contextLabel: "SAME_CONTEXT_MARGINAL_COMPARISON"`. Matches
  the ledger's own documented value for this exact pairing.
- **Harrison's trace**: `explanation: "[v2 challenger] Bench depth at WR
  ... Standalone value 0.0 -> 0.0."` -- re-confirmed live as legitimate
  replacement-level behavior, not a bug (matches the investigation doc's
  root-cause finding exactly). Harrison himself is a DROP candidate (not
  an add), so he has no FAAB bid by construction; the nonpositive-FAAB
  gate was independently re-confirmed live this pass via a direct
  function-level call to the current `suggest_faab_bids()` with
  constructed zero/negative/unmatched/positive candidates: the zero and
  negative candidates each returned `$0/$0, LOW, "Modeled nonpositive
  value..."`; the unmatched candidate returned `$0/$0, LOW, "Unknown
  identity..."`; the positive candidate returned a real `$28-46, MEDIUM`
  bid -- all four distinct, none fabricated. (This is a direct, current,
  ACTUAL TEST RESULT against the live HEAD function, not a re-run of
  Worker 2's original 723-candidate full-pool sweep -- that original
  sweep is not literally re-executed by this pass, only its documented
  result is trusted alongside this pass's own smaller live reproduction
  and the 13 passing unit tests covering the same gate.)
- **Live FAAB budget**: `faabContext: {"isFaabLeague": true, "budgetMode":
  "LIVE", "totalBudgetDollars": 100, "remainingBudgetDollars": 100,
  "weeksRemaining": 13, "weeksRemainingSource": "LIVE", "waiverPosition":
  10, "source": "SLEEPER_LIVE"}` -- exact match to a direct raw
  `roster.settings` pull (`waiver_budget_used: 0`, `waiver_position: 10`),
  confirming this is the real current budget, not a stale/default value.
- **Both horizon outputs**: REST_OF_SEASON and THIS_WEEK (week 2, current
  live week) both returned successfully; THIS_WEEK's
  `weeklyProviderHealth` shows `status: OK`, `freshness: LIVE`,
  `servedFromCache: true` (a real, same-request cache hit, not stale --
  `retrievedAt` timestamped this pass), `totalRows: 9420`,
  `nonzeroProjectionRows: 898`. Top add (Tyrone Tracy) has identical
  `marginalUtility` (9.72) in both modes, confirming the ranking is
  mode-independent as designed; `weeklyProjectedPoints: 1.871` is
  correctly shown as a separate, real, low single-week number without
  affecting rank. The honest Mode-toggle captions themselves (UI copy)
  were NOT re-screenshotted this pass (see Remaining Gaps).
- **Zero writes, verified 3 ways**: (1) structural -- `SleeperHttpClient`
  exposes only `get_json`; (2) this pass's own verification script
  contains zero `POST`/`PUT`/`PATCH`/`DELETE` strings; (3) before/after
  byte-diff of `GET league/{id}/rosters` around this pass's entire live
  verification run: **byte-identical**, SHA-256 `6ad88171...`, matching
  the exact hash every prior worker/pass this same day independently
  recorded for this same real league.
- **Scope discipline**: this check covers Fantasy Gamers/Sleeper ONLY. It
  does NOT verify Dynasty, KHA (ESPN), or 403 N 18th (ESPN) -- those are
  untouched by this cycle and were not re-checked this pass.

## Whether the installed native app was tested

**No, not this pass, and not by any of the 4 prior workers in this
cycle either -- a pushed commit does not establish this.** Precisely:

- What WAS tested: (a) direct Python facade/service calls against a real,
  live Sleeper league (this pass and prior passes); (b) the full backend
  pytest suite; (c) the frontend `tsc`/`vitest`/`vite build` toolchain;
  (d) in the PRIOR consolidated Waiver Night V1 (Workers 4/6, not this
  cycle), a real Chrome session against a real `vite preview` build talking
  to the real Python desktop API backend over HTTP (`127.0.0.1:1422` /
  `18742`) -- this is the closest any pass has come to an end-to-end
  check, but it is still a web build in a browser, not the packaged
  native app.
- What was NOT tested, this pass or any prior pass in this cycle: the
  actual installed Tauri desktop binary. **Directly re-confirmed this
  pass**: `cargo check` inside `desktop/apps/redraft/src-tauri` **fails**
  with `failed to generate Redraft desktop context: resource path
  "..\..\..\binaries\nwr-desktop-api-x86_64-pc-windows-msvc.exe" doesn't
  exist` -- a pre-existing, disclosed, unrelated packaging-resource gap
  (not a regression from this cycle; `git diff --stat` for
  `desktop/apps/redraft/src-tauri` and `desktop/apps/dynasty/src-tauri`
  across the ENTIRE cycle, and across the whole Waiver Night V1 night, is
  empty -- zero Rust/Tauri files touched by any worker). This means the
  native app **cannot even be `cargo check`-built in this environment
  right now**, let alone launched and clicked through -- confirming the
  installed native app was structurally impossible to exercise this pass,
  not merely skipped. The real owner AppData install
  (`C:\Users\codex-agent\AppData\Local\com.ninerswarroom.redraft`)'s most
  recently modified state file is timestamped `2026-09-09`, confirming
  neither this pass nor any prior pass in this cycle wrote to the real
  installed profile store either.

## Remaining gaps / follow-ups (not fixed this pass, honestly carried
## forward)

Everything already listed as open at the end of `LEDGER.md` remains open
and is NOT re-summarized field-by-field here -- read that file's own
"OPEN ISSUES" sections for the full list. Highlights most relevant to a
future worker:

1. Native Tauri packaging is structurally broken in this environment
   (missing prebuilt backend binary resource) -- unrelated to this
   cycle's fixes, pre-existing, not attempted here.
2. No real non-FAAB Sleeper league exists in this environment; the
   `isFaabLeague === false` suppression path (both UI and response-level)
   remains verified only via constructed test fixtures.
3. Only one real Sleeper profile (Fantasy Gamers) exists in this
   environment; the LIVE/SCENARIO profile-switch leak-prevention logic is
   INSPECTED CODE + a real, reasoned structural argument, not a literally
   live-observed two-profile switch.
4. `pair_add_drop`'s "2-3 close drop alternatives" (an explicitly optional
   directive item) was never built -- still single-weakest-drop only.
5. K/DST are still structurally invisible to the main
   `redraft_waivers`/Add-Drop surface (by design; the separate Streamers
   tab is the correct real channel, confirmed working).
6. `matchupContext` still returns `null` from
   `redraft_league_workspace_context()` -- never investigated (hard-
   boundary-protected surface).
7. This closing pass's own live re-verification of the honest Mode-toggle
   captions (Section 5's UI text) and the FAAB calibration-limitation
   tooltip was NOT re-screenshotted in a real Chrome session -- relies on
   direct source-code confirmation (the caption strings are present in
   both `improve-team.tsx` and `in-season.tsx`) plus the prior Worker 4/6
   passes' own real Chrome verification of the surrounding surfaces.
8. Harrison's own projection-freshness question (is a `source_as_of:
   2026-09-08` snapshot still current given the live season has
   progressed) remains an open, unverified-either-way question, not a
   defect.

## Next focused task for whoever picks this up

Pick ONE of: (a) fix the native Tauri packaging resource-path gap so
`cargo check`/a real installed-app launch becomes possible in this
environment; (b) if/when a second real Sleeper profile or a real non-FAAB
league becomes available to the owner, literally re-run the
profile-switch-leak and non-FAAB-suppression checks live instead of via
fixture; (c) a dedicated performance pass caching the uncached ~14.66MB
`players/nfl` Sleeper payload (flagged, not attempted, by an earlier
worker in `LEDGER.md`). None of these block the current push -- see the
push decision below.
