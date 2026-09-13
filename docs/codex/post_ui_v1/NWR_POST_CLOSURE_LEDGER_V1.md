# NWR Post-Closure Ledger V1

New, smaller ledger for the post-closure implementation work that follows
`docs/codex/post_ui_v1/NWR_POST_CLOSURE_RESEARCH_V1.md`. The prior
`NWR_POST_UI_WORKDAY_LEDGER.md` (2,800+ lines, covering the entire
post-UI-product-v1 shift through Closure Worker C) is kept as-is for
historical reference; start here going forward so entries stay readable.

No merge/push/deploy by any worker. No push to origin without explicit
owner authorization.

---

## Worker D — FAAB urgency enum fix + small tech-debt batch — 2026-09-13

**Scope: research doc items #1 and #5.** Branch
`upgrade/nwr-post-closure-fixes-v1-20260913`, worktree
`C:\NWR\post-closure-fixes-v1`, start HEAD `4c8ab1b0`.

### Item 1 — FAAB urgency enum mismatch (FIXED)

**Root cause**: `src/services/waiver_engine_service.py`'s `suggest_faab_bids`
set `FaabBidSuggestion.urgency` to one of its own internal, more
descriptive reason codes -- `STARTER_UPGRADE` / `BENCH_DEPTH` / `LOW_VALUE`
-- and `src/application/desktop_facade.py` (`redraft_waivers`, the
`faabUrgency` field, ~line 3435) passed that value straight through to the
JSON response with no translation. The shared contract
(`desktop/packages/contracts/src/index.ts:1109`,
`faabUrgency: "HIGH" | "MEDIUM" | "LOW" | null`) and both frontend lookup
tables that key off it (`weekly-shared.tsx`'s `FAAB_URGENCY_TONE`,
`improve-team.tsx`'s local `FAAB_URGENCY_RANK`) only ever recognized
`HIGH`/`MEDIUM`/`LOW`. Every real FAAB urgency badge fell through to the
generic "review" fallback tone (regardless of actual urgency) and the FAAB
tab's urgency-based sort silently no-opped (every row tied at the same
fallback rank 3).

**Fix direction chosen: (a) -- map the backend's existing reason codes onto
the contract's `HIGH`/`MEDIUM`/`LOW` scale, at the source.** Added a single
module-level `FAAB_URGENCY_TIER` dict in `waiver_engine_service.py`
(`STARTER_UPGRADE -> HIGH`, `BENCH_DEPTH -> MEDIUM`, `LOW_VALUE -> LOW`) and
renamed the local variable that drives the rationale text/multiplier to
`urgency_reason` (unchanged internal logic), assigning
`FAAB_URGENCY_TIER[urgency_reason]` to the field the contract actually
promises. Chosen over updating the contract/UI to the descriptive
vocabulary because:
- **Fewer real call sites**: this direction touches exactly one backend
  file (plus its test). The alternative would have required changing
  `contracts/src/index.ts`, `weekly-shared.tsx`'s `FAAB_URGENCY_TONE`,
  `improve-team.tsx`'s `FAAB_URGENCY_RANK`, and every test fixture that
  hardcodes `"HIGH"`/`"MEDIUM"`/`"LOW"` (at least 4-5 files vs. 1).
- **No information is actually lost**: the descriptive detail
  (starter-upgrade vs. bench-depth vs. low-value) is already fully
  preserved in the separate `rationale` string every call site renders
  (`improve-team.tsx`'s title tooltip and `why` prop, `in-season.tsx`'s
  inline `<small>` text) -- the tier field only ever drove badge tone/sort,
  not the visible explanation.
- `desktop_facade.py` needed zero changes (it already just passes
  `bid.urgency` through).

**Fixture correction**: no Python test previously asserted a specific FAAB
urgency string at all (`tests/test_waiver_engine_service.py` only checked
bid dollar amounts), so there was no backend fixture to "fix" per se -- the
real masking gap was the *absence* of a test connecting the backend's real
output to the contract's promised values. The frontend unit fixture
(`improve-team-explain.test.ts:22`, `faabUrgency: "HIGH"`) already used a
contract-shaped literal and needed no change under fix direction (a); it
simply never exercised the real (buggy) backend value, which is exactly
why it never caught this.

**Regression tests added**:
- `tests/test_waiver_engine_service.py`: three new tests --
  `test_faab_urgency_uses_the_shared_contracts_high_medium_low_scale`
  (asserts exact `HIGH`/`MEDIUM`/`LOW` per becomes-starter/bench/low-value
  candidate, using real `WaiverCandidate` fixtures, not just "some
  string"), `test_faab_urgency_tier_maps_every_internal_reason_onto_the_
  contract_scale` (locks the mapping dict itself), and
  `test_faab_urgency_for_unmatched_identity_is_the_contracts_low_value`.
- `desktop/apps/redraft/src/weekly-shared.test.ts`: one new test asserting
  `FAAB_URGENCY_TONE` covers exactly the real contract type's 3 literal
  values (typed as `WaiverAddCandidate["faabUrgency"]`, not a hand-rolled
  string, so it fails to compile if the union and the table drift apart
  again), with the exact expected tone per value.

**Live verification against the real Fantasy Gamers Sleeper league**
(ID `1312983576827920384`, read-only): ran
`desktop/scripts/nwr_release_gate_smoke.ps1 -KeepRunning -SleeperLeagueId
1312983576827920384 -SleeperUsername scolety`, which starts the real
Python desktop API backend (port 18742) and a real production `vite
preview` build (port 1422) against the already-imported real profile.
- Direct `POST /api/v1/redraft/waivers {"mode":"REST_OF_SEASON"}` against
  the running backend returned 25 real candidates with `faabUrgency`
  values of exactly `MEDIUM` (bench-depth adds, marginal utility > 0) and
  `LOW` (marginal utility <= 0) -- never the old
  `STARTER_UPGRADE`/`BENCH_DEPTH`/`LOW_VALUE` strings. (No `HIGH` in this
  particular real pool, since no free agent currently becomes a starter on
  this roster -- consistent with the roster's real state, not a gap in the
  fix.)
- Drove the real app in Chrome (`http://127.0.0.1:1422/#/league/<id>/
  waivers?tab=faab`, real Fantasy Gamers league already active): the FAAB
  tab correctly renders `MEDIUM URGENCY` badges (amber/gold, "review"
  tone) and `LOW URGENCY` badges (green, "safe" tone), sorted MEDIUM before
  LOW as `FAAB_URGENCY_RANK` intends, with bid text reading e.g. "BID
  $30-50 - MEDIUM urgency for Juwan Johnson" -- not blank, not the raw
  backend enum, not miscolored. The Targets tab's suggested-bid line
  ("SUGGESTED BID $30-50 - MEDIUM urgency") renders identically.
  **Zero console messages of any kind** on a fresh reload of the FAAB tab
  (checked via `read_console_messages` with no filter after a hard
  navigation).
- Sleeper writes: 0. `redraft_waivers` only issues `GET` calls through
  `SleeperHttpClient.get_json` (rosters/players); no POST/PUT/PATCH/DELETE
  call site targets `api.sleeper.app` anywhere in `src/` (same structural
  guarantee every prior worker has verified). Backend + vite preview
  processes stopped and cleaned up (`taskkill`) after verification.

### Item 5 — small cosmetic/tech-debt batch

- **Stale comment (FIXED)**: `src/services/waiver_engine_service.py`'s
  module docstring claimed the DST/K streamer lane "has a real
  nflreadpy-backed matchup signal." Confirmed false by direct read of
  `fantasypros_kdst_consensus_service.py` (pure FantasyPros ECR passthrough
  + live Sleeper roster-ownership matching, no schedule/matchup signal at
  all) -- corrected the comment to say so honestly.
- **`.replaceAll()` hardening on `writeBehavior` (pages.tsx / improve-team.tsx)
  -- VERIFIED UNREACHABLE, SKIPPED**: `result.writeBehavior.replaceAll("_",
  " ")` in both `WeeklyToolsPage` (pages.tsx:538) and its `improve-team.tsx`
  equivalent (line 630) reads a field that is a hardcoded literal string
  (`"NO_SLEEPER_WRITES"` / `"NO_SLEEPER_WRITES_NO_FANTASYPROS_WRITES"`) on
  every single success-path return in `desktop_facade.py` (11 emission
  sites checked, all literal, none conditional on a variable that could be
  `None`); every error path raises `FacadeError` instead of returning a
  partial payload, so the frontend's `results` array can never contain an
  object missing this field. Confirmed by direct code read of
  `redraft_kdst_streamer` end to end. Hardening a field that cannot
  actually be null/undefined under the current backend contract would add
  dead defensive code, not fix a real risk -- skipped per the directive's
  own "don't harden something that's actually unreachable" guidance.
- **`.replaceAll()` hardening on dynasty `decisions.tsx` -- VERIFIED
  UNREACHABLE, SKIPPED**: `decision.recommendation.replaceAll(...)` and
  `dimension.outcome.replaceAll(...)` both read fields that flow through
  `desktop_facade.py`'s `_trade_decision_payload` (the single call site
  that builds this response), which wraps every field in the `_text()`
  helper -- `_text` guarantees a real string is always returned (coercing
  `None`/`"nan"`/`"none"`/`"null"`/`"<na>"` to `""`), never `None`/
  `undefined`. `"".replaceAll(...)` is safe (returns `""`). Same
  conclusion: not a reachable crash or leak site, skipped rather than
  force a no-op change.
- **`String(row.action)` "undefined" leak in Compare/Suggestions
  (draft-room-v2.tsx) -- VERIFIED NOT REPRODUCIBLE, SKIPPED**: traced both
  the Suggestions candidate table's Action/Value columns (lines 2288-2301,
  no null guard before `String(row.action)`) and the Compare table's
  equivalent (lines 3673-3683, which does guard with
  `if (row.action == null) return "-"`). Empirically verified with a
  throwaway vitest test exercising `resolveDisplayAction`/
  `splitActionValue`/`actionToBadgeTone` directly with `undefined` and
  `null`: `splitActionValue`'s own ternary chain has a catch-all default
  (`"Review data"` for the action label, `"Unknown"` for the value when
  geometry is also missing) for any string it doesn't recognize, including
  the literal `"undefined"`/`"null"` that `String(...)` produces --  so the
  visible badge always reads "Review data" and never leaks the raw
  coercion text. The research doc's description of this item does not
  survive direct inspection/testing; documenting honestly and skipping
  rather than forcing an unneeded change. (Scratch test file used for this
  check was not committed.)
- **Dead button cleanup ("Open in Analyze") -- NOTHING TO DO**: grepped for
  the button; it no longer exists anywhere in the code (only historical
  comments in `trades-explain.ts`/`trades-explain.test.ts`/`trades.tsx`
  referencing its removal during an earlier closure pass, one explicitly
  reading "Deliberately NO 'Open in Analyze' cross-tab jump on these
  cards"). Already cleaned up by prior work; no action needed here.

### Tests

- `python -m pytest tests/test_waiver_engine_service.py`: 12 passed (9
  pre-existing + 3 new).
- `python -m pytest tests/test_desktop_facade_architecture_wiring.py
  tests/test_weekly_home_single_snapshot.py
  tests/test_trade_package_search_facade_wiring.py`: 23 + 6 passed (safety
  sweep of every other consumer of `waiver_engine_service`/FAAB-adjacent
  facade wiring -- no regression).
- `npx tsc -b apps/dynasty/tsconfig.json apps/redraft/tsconfig.json`: clean,
  zero errors.
- `npm run test` (full monorepo vitest, from `desktop/`): **28 test files,
  368 tests, all passed** (includes the 1 new `weekly-shared.test.ts`
  case; still >= the 367-baseline the directive named).
- Console errors during live Chrome verification: **0**.

### Files changed

- `src/services/waiver_engine_service.py` -- the FAAB urgency tier mapping
  fix + the stale streamer-schedule-signal comment correction. Justified:
  this is the exact, narrowly-scoped root cause of the shipping bug;
  `marginal_roster_utility_v2` and every other hard-boundary function are
  untouched (only called, as before).
- `tests/test_waiver_engine_service.py` -- 3 new regression tests, no
  existing test changed (none needed fixing, per the fixture analysis
  above).
- `desktop/apps/redraft/src/weekly-shared.test.ts` -- 1 new regression
  test for the frontend tone table.

No draft recommendation/scoring/roster-legality file, `LeagueSnapshot`/
`LeagueWorkspaceContext`/lifecycle-resolver/`DecisionResultEnvelope`/
`PlayerAvailabilityStatus` file was touched.

### Open issues for the next worker

- Item 5's `.replaceAll()`/`String(row.action)` sites are genuinely
  unreachable/non-reproducible today under the current backend contract --
  re-verify if `desktop_facade.py`'s `writeBehavior`/`_text()` guarantees
  or `splitActionValue`'s catch-all default ever change; they'd become
  real risks again if any of those invariants are relaxed.
- The build-machine-path leak in the shipped `.exe` Rust panic strings
  (`--remap-path-prefix`, research doc item in the "not recommended for
  now" tier) and the install-and-launch verification gap remain untouched
  -- out of this worker's scope (items #1/#5 only).
- Per the directive: next up is a real profiling pass on Waivers
  (THIS_WEEK, ~16.3s) and Weekly Home aggregation (~7.9s) latency (research
  doc item #3 / Area J) -- likely root causes already named there
  (`redraft_weekly_home_actions` re-invoking several live-Sleeper-backed
  sub-calls separately; THIS_WEEK mode's live per-candidate weekly-
  projection resolution across the whole free-agent pool). Neither
  profiled nor touched this pass.

## Worker E -- Waivers/Weekly Home latency profiling + one evidence-backed fix -- 2026-09-13

**Scope: research doc item #3 / Area J.** Same branch
`upgrade/nwr-post-closure-fixes-v1-20260913`, worktree
`C:\NWR\post-closure-fixes-v1`, start HEAD `cd7131f4`.

### Method

Profiled with real `cProfile` runs directly in-process (no HTTP server
needed -- `DesktopBackendFacade(repo_root=".", mode="redraft")` with the
default `redraft_root` already resolves to this worktree's real,
already-Sleeper-imported "Fantasy Gamers" profile in
`local_exports/redraft_v1`, read-only, GET-only against the real league).
Real Sleeper NFL state confirmed week 1 (`GET
https://api.sleeper.app/v1/state/nfl`) before profiling `THIS_WEEK` mode.

### Waivers (THIS_WEEK) profiling -- no fixable inefficiency found

`redraft_waivers(mode="THIS_WEEK")` makes exactly 3 real network calls per
request: `league/{id}/rosters`, `players/nfl`, and one weekly-projections
fetch (`get_weekly_projections`, which already has its own 5-minute
on-disk TTL cache in `weekly_projection_provider_service.py`, unrelated to
this pass). cProfile's own `tottime` ranking shows these three network
reads (TLS connect/handshake + `_ssl._SSLSocket.read`) account for
essentially all wall time; the entire `rank_waiver_candidates`/
`rank_drop_candidates` loop (which DOES call `marginal_roster_utility_v2`
once per free agent plus once per roster player -- the "once per candidate"
pattern the directive said to check for) totals well under 100ms even
across the real ~280-candidate free-agent pool. Real runs (5 each, this
worktree, live network): before-change median 2,119ms, after-change (see
below -- this file's fix doesn't touch this method's call count at all)
median 1,461ms; the ~660ms spread is real network/TLS variance between
runs, not a code-path difference (confirmed: `redraft_waivers` standalone
issues the identical 2 rosters/players GETs plus 1 projections GET in both
the before and after trees). Historical 16.3s readings for this endpoint
are consistent with real, one-off network conditions (a cold/contended
connection to `api.sleeper.app`), not a redundant-computation bug --
**verdict: proportional to real, necessary network I/O; no fixable
inefficiency found; correctly left untouched.**

One real, IRRELEVANT-TO-LATENCY finding surfaced while reading
`shadow_numeric_authorities_service.py`: `marginal_roster_utility_v2` calls
`_asset_pool(ranking, manual_assets)` directly AND indirectly (via its own
call to `explain_marginal_roster_reason`, which also calls `_asset_pool`) --
two rebuilds of the same pure, input-stable dict per candidate. cProfile
shows `_asset_pool` costing only ~50ms cumulative across a full ~280-
candidate waiver pool (out of a ~1.1-1.5s real run) -- real, but small, and
`marginal_roster_utility_v2` is an explicit hard-boundary function this
pass will not touch even for a provably byte-identical caching change,
given the small, uncertain payoff relative to working adjacent to a
frozen, historically-validated formula. **Left untouched; flagged for a
future pass IF a much larger free-agent pool ever makes this cost
material** (it grew to ~450ms/9.2s, ~5%, in the busier Weekly Home
request after the real fix below removed the dominant network cost --
still a minority contributor, not chased this pass).

### Weekly Home Actions profiling -- real, fixable redundant-fetch bug found and fixed

`redraft_weekly_home_actions` fans out to five sub-facade calls
(`redraft_weekly_lineup`, `redraft_waivers(mode="REST_OF_SEASON")`,
`redraft_trade_finder`, `redraft_kdst_streamer`, `redraft_free_agents`).
cProfile showed **11 separate live `SleeperHttpClient.get_json` network
round trips in one request** (2 rosters + 2 players from
`redraft_weekly_lineup`, 2+2 from `redraft_waivers`, 3 from
`redraft_trade_finder` [rosters+users+players], 2+2 from
`redraft_kdst_streamer`, 2+2 from `redraft_free_agents` -- 5 rosters + 5
players + 1 users = 11), totalling ~11s of a real ~13s in-process run --
almost entirely redundant identical GETs to the SAME league/season/instant,
each paying a full fresh TLS handshake (`connect`+`do_handshake` alone
summed to ~5s across the 13 calls in one profiled run). This is exactly the
"repeated network/file reads that could be cached within one request"
pattern the directive named as a common, real culprit -- confirmed by
profiler evidence, not guessed.

**Fix (evidence-backed, equivalence-proven, no hard-boundary file
touched):** added a thread-local, OPT-IN, per-top-level-request cache to
`DesktopBackendFacade` (`_sleeper_fetch_cache_local` set in `__init__`;
`_sleeper_get_json(client, path)` helper). `redraft_weekly_home_actions`
turns the cache on (`{}`) for the duration of its own five sub-calls (now
split into a small `_redraft_weekly_home_actions_impl` wrapped in
try/finally) and always turns it back off (`None`) afterward. The five
sub-methods' own `sleeper.get_json(...)` call sites were changed to
`self._sleeper_get_json(sleeper, ...)` -- a pure pass-through when the
cache is inactive (every other caller of these five methods, including
every existing test and every standalone HTTP request to Waivers/Trade
Finder/K-DST Streamer/Free Agents/Start-Sit on their own) is byte-for-byte
unaffected; a distinct URL is fetched from the network only once when the
cache IS active. Used `threading.local()`, not a bare instance attribute,
because `DesktopApiServer` (`src/desktop_api/server.py`) is a real
`ThreadingHTTPServer` sharing one `DesktopBackendFacade` instance across
concurrently-handled requests -- a shared dict would let one in-flight
request's cache leak into or get wiped by another's `finally`; proven
safe under actual concurrent threads by
`test_cache_scope_is_thread_local_not_shared_across_concurrent_requests`.
The weekly-projections fetch inside `redraft_weekly_lineup` (a DIFFERENT
Sleeper endpoint, `projections/nfl/...`) is untouched -- it already has its
own disk-backed 5-minute TTL cache in
`weekly_projection_provider_service.py` and was deliberately left alone.

**Real before/after numbers** (median of 5 runs each, same real
already-imported Fantasy Gamers league, live network, this worktree;
`git stash`/`git stash pop` used to get a true before/after on the exact
same code path):
- Weekly Home Actions: before median **7,188.2 ms** (raw runs 9471/7050/
  6337/7188/9246 ms) -> after median **2,713.2 ms** (raw runs 2854/1876/
  2713/2204/4436 ms) -- a real ~62% reduction, consistent with cutting 11
  network round trips down to 3 (1 rosters + 1 players + 1 users) plus the
  one still-necessary, still-uncached-across-different-weeks weekly-
  projections fetch inside `redraft_weekly_lineup`.
- Waivers (THIS_WEEK), unaffected by this fix (confirmed by code read: its
  own call count is unchanged before/after): before median 2,119.3 ms,
  after median 1,461.1 ms -- within real network variance, not a code
  effect (this file's own profiling section above already established
  Waivers has no redundant-fetch pattern to fix).

**Tests**:
- New `tests/test_weekly_home_sleeper_fetch_caching.py` (5 tests): (1)
  `_sleeper_get_json` is a byte-for-byte pass-through when the cache is
  inactive; (2) it dedupes within an active scope and returns the exact
  same cached object (`is`, not just `==`), then correctly tears back down
  to a fresh fetch afterward; (3) an end-to-end
  `redraft_weekly_home_actions` run (real governed ranking bootstrapped
  into a fresh tmp store, real Sleeper mocked via
  `SleeperHttpClient.get_json`) fetches `league/9999/rosters` and
  `players/nfl` exactly once each (not five times) and `users` exactly
  once, with a well-formed, correct response (a real free-agent identity
  match -- Christian McCaffrey, a real row from the repo's bundled Freeze
  V7 ranking -- correctly surfaces in the embedded `freeAgents` payload);
  (4) every one of the five sub-methods called STANDALONE (the everyday,
  non-Weekly-Home path) still fetches fresh every single call, proving
  zero behavior change outside the one method that opts in; (5) a real
  concurrent-threads test proves the `threading.local()` scoping never
  leaks or gets wiped across two simultaneously-running requests.
- Full existing regression sweep, unchanged pass rate: `tests/
  test_weekly_home_single_snapshot.py` (4/4), `tests/
  test_desktop_facade_architecture_wiring.py` (23/23... run together: 105
  passed across the 9-file focused sweep including the new file),
  `tests/test_waiver_engine_service.py`, `tests/
  test_trade_package_search_facade_wiring.py`,
  `tests/test_prospective_recommendation_ledger_v1.py`, `tests/
  test_redraft_identity_boundary_opponent_and_trade_finder.py`, `tests/
  test_league_workspace_context_sleeper_p1_1.py`, `tests/
  test_decision_envelope_consumer_migration.py`.
- Full `pytest tests/`: 330 failed / 4294 passed / 72 skipped / 13 errors
  -- confirmed via `git stash` that this exact failure count (and every
  individual failing test id checked, e.g. `test_desktop_application_api.
  py`'s 4 real pre-existing failures) is IDENTICAL on the unmodified
  `cd7131f4` tree, i.e. zero regressions introduced by this change (this
  count is close to, and consistent with, the previously-documented
  ~323-pre-existing-failures baseline for this worktree's missing
  `local_exports` data packs/Streamlit UI-contract drift -- unrelated to
  this pass). Two of the tests in this run write/regenerate committed
  `docs/model_v4/*.md` audit-report files as a side effect of running the
  full suite -- reverted (`git checkout --`) after the run, not part of
  this pass's real change.
- `npx tsc -b apps/dynasty/tsconfig.json apps/redraft/tsconfig.json`:
  clean, zero errors (no TS file touched this pass).
- `npm run test` (full monorepo vitest, from `desktop/`): 28 test files,
  368 tests, all passed (unchanged from Worker D's baseline; no frontend
  file touched this pass).

### Files changed

- `src/application/desktop_facade.py` -- the thread-local per-request
  Sleeper GET cache (`_sleeper_fetch_cache_local`, `_sleeper_get_json`),
  wired into the five call sites `redraft_weekly_home_actions` fans out
  to. `redraft_weekly_home_actions` itself was split into a thin outer
  method (turns the cache on/off) and `_redraft_weekly_home_actions_impl`
  (the original body, logic byte-for-byte unchanged). No scoring/ranking/
  roster-legality/`LeagueSnapshot`/`LeagueWorkspaceContext`/lifecycle-
  resolver/`DecisionResultEnvelope`/`PlayerAvailabilityStatus` file
  touched; `marginal_roster_utility_v2` and `shadow_numeric_authorities_
  service.py` were read for profiling but NOT edited.
- `tests/test_weekly_home_sleeper_fetch_caching.py` -- new, 5 tests (see
  above).

### Open issues for the next worker (owner-action/outcome capture UI, per the directive)

- The `_asset_pool` double-computation inside `marginal_roster_utility_v2`/
  `explain_marginal_roster_reason` (real, ~50ms on a ~280-candidate
  Waivers pool today, ~450ms/~5% of a busier Weekly Home request after
  this pass's network fix) is real but small and sits directly inside a
  hard-boundary function -- deliberately NOT touched this pass. Revisit
  only if the free-agent pool or roster size grows enough to make this a
  material fraction of total latency, and only with the same byte-
  identical-output equivalence rigor this pass used for its own change.
- A real, PRE-EXISTING, unrelated bug surfaced incidentally while building
  this pass's test fixtures: `redraft_waivers`' decision-envelope
  rationale string (`f"...{top_add.marginal_utility:.1f}"`,
  `desktop_facade.py` around line 3505) raises `TypeError: unsupported
  format string passed to NoneType.__format__` whenever the single
  best-ranked add candidate is genuinely `UNMATCHED_IDENTITY` (marginal
  utility legitimately `None`) rather than `MATCHED`. Reproduced directly
  (not from the real Fantasy Gamers league, which currently has zero
  unmatched top candidates) via a minimal test fixture; NOT fixed here
  (out of this pass's profiling/latency scope, and not something the
  directive asked for) -- worth a small, separate, low-risk fix (e.g. an
  `if top_add.marginal_utility is not None else` guard matching the
  pattern already used elsewhere in this same function).
- Per the directive's own queue: next up is the owner-action/outcome
  capture UI (closing P1-4's real, disclosed gap -- `record_owner_action`/
  `record_outcome` are real, tested, backend-ready; `decision-history.tsx`
  has no capture control for either yet).
