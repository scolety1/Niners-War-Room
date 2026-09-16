# NWR Full Cycle V1 — Durable Ledger

Shared ledger for the large, multi-worker, full-product NWR upgrade-and-test
cycle (Redraft + Dynasty) starting 2026-09-16. Each worker appends its own
dated section. Do not delete or rewrite a prior worker's section — append
only, and correct forward (a later note superseding an earlier one) rather
than editing history.

---

## Worker 1 — Baseline verification + "3 data issues" badge investigation (2026-09-16)

**Branch/worktree:** `upgrade/nwr-prospective-outcomes-v1-20260914` at
`C:\NWR\prospective-outcomes-v1`. Started at HEAD `8a517da3` (clean,
matched origin exactly). Ended at a new commit on the same branch (see
handoff below) — no reset, no force-push, no push performed.

### Baseline (INSPECTED CODE / ACTUAL TEST RESULT / LIVE OBSERVATION)

- `git log -1` / `git status`: HEAD `8a517da3619e1c08aa365918acff523f2f25ea14`,
  branch `upgrade/nwr-prospective-outcomes-v1-20260914`, up to date with
  origin, clean tree (ACTUAL).
- Frontend `vite preview` (PID 23004) and backend (PID 7924, real command
  line: `python scripts/run_nwr_desktop_api.py --host 127.0.0.1 --port 18742
  --mode redraft --repo-root C:\NWR\prospective-outcomes-v1`, no
  `--reload`) both confirmed alive and genuinely serving (LIVE
  OBSERVATION): frontend HTTP 200 at `http://127.0.0.1:1422/`; backend
  returns real structured JSON (`AUTHENTICATION_REQUIRED` contract-shaped
  error) rather than hanging or erroring at the transport level. Backend
  API calls made from the real browser session (with its own session
  token) returned real 200 responses for `/api/v1/bootstrap`,
  `/api/v1/redraft/data-health`, `/api/v1/redraft/status-overrides`.
- No commit-SHA marker exists anywhere in the UI (acknowledged known gap,
  not investigated further this pass).
- Data isolation (INSPECTED + ACTUAL): `local_exports/` under the worktree
  is a genuine directory, not a symlink or junction
  (`os.path.realpath` resolves to itself). The owner's real install at
  `C:\Users\codex-agent\AppData\Local\com.ninerswarroom.redraft` exists and
  was not touched. Active profile in the isolated copy is the real,
  already-imported read-only Fantasy Gamers league
  (`941b99ade350410391b1b67c0890af79`).

### "3 data issues" badge — investigation (LIVE OBSERVATION + INSPECTED CODE)

Badge source: `desktop/apps/redraft/src/shell-notices.ts`
(`summarizeShellNotices`) — a pure client-side classifier over
`RedraftBootstrap.notices` (built server-side in
`src/application/desktop_facade.py`, `redraft_bootstrap()`) plus two
header-level signals (player-identity availability, ADP availability).
Real Chrome session against `http://127.0.0.1:1422/#/league/.../draft`
confirmed the live badge popup lists exactly 3 items, and `#/data-health`
(`Data Health` page) confirms the same 3 underlying conditions in more
detail.

**Issue 1 — Market ADP unavailable.**
- Root cause (INSPECTED): `load_adp_snapshot`
  (`src/services/redraft_draft_room_v1_service.py:464`) checks, in order,
  a global owner-platform ADP snapshot
  (`adp_provider_cache/owner_platform_snapshot/snapshot.json`), a
  profile-scoped FFC cache, an owner-paste cache, then a legacy
  profile-scoped file — none exist in this isolated worktree's
  `local_exports/redraft_v1` (ACTUAL: no `adp_snapshots/` or
  `adp_provider_cache/` directory exists at all under that root).
- Consumers: `desktop_facade.py` `_category("MARKET_ADP", ...)` (Data
  Health card) and the Draft-day Value/Reach/Cost-of-Waiting fields in the
  Draft Room/Rankings (per the facade's own documented impact string).
- Verdict: **GENUINELY UNAVAILABLE DATA** for this specific isolated test
  copy — nobody has ever imported an ADP snapshot into this worktree's
  isolated state (confirmed by absence of any ADP file on disk, not an
  inference from the badge alone). This is expected/correct behavior for a
  freshly isolated worktree, not a code defect. Real recovery action: the
  owner (or a later worker with explicit authorization) would import a
  market ADP snapshot through the Market Data / ADP control center, the
  same real global-snapshot flow already documented in a prior session
  (`nwr-market-data-control-center-v1`). Not fabricated/imputed — left
  showing correctly.

**Issue 2 — Sleeper scoring needs review.**
- Root cause (INSPECTED + ACTUAL, read directly from the real import
  receipt `local_exports/redraft_v1/sleeper_imports/<profile_id>.json`,
  `scoring_reconciliation`/`unsupported_scoring` fields): 31 Sleeper
  scoring-rule keys are non-zero in the real Fantasy Gamers league but have
  no NWR-side mapping — mostly DST/special-teams/kicker granularity
  (`blk_kick`, `def_st_ff`, `def_st_td`, `fgm_0_19`…`fgm_60p`, `pts_allow_*`
  bands, `st_ff`, `xpm`, etc.) plus three genuinely broader offensive
  fields: `pass_2pt`, `rec_2pt`, `rush_2pt` (2-point conversions, worth 2
  each in this league).
- Consumers: shown verbatim in the header badge and the Data Health
  "Sleeper scoring needs review" notice; NWR's scoring engine deliberately
  never silently maps any of these to zero.
- Verdict: **GENUINELY UNAVAILABLE / OUT-OF-SCOPE MODELING**, not a bug.
  This is the governed scoring model's documented boundary (explicitly
  listed, non-silent) and modifying it would mean touching the governed
  valuation/scoring model, which is inside this pass's hard boundary (not
  touched). Noted for visibility: the 2-point-conversion gap is broader in
  real fantasy-scoring impact than the mostly-DST remainder of the list,
  worth a future worker's attention as a scoped scoring-model enhancement
  (NOT done this pass).

**Issue 3 — 7 rookies remain blocked. REAL BUG FOUND AND FIXED.**
- Root cause (INSPECTED + ACTUAL, read directly from the real bundled CSV
  `docs/hq/model/nwr_redraft_2026_freeze_v7_bundled_seed_v1_20260912/BLOCKED_2026_ROOKIES.csv`):
  the CSV's own `block_reason` column shows **three genuinely distinct**
  real reasons across the 7 blocked rows — only 2 (Max Bredeson, Riley
  Nowakowski) are true draft-position-vs-current-position conflicts; 4
  (Joe Royer, Emmanuel Henderson Jr., Lewis Bond, Anthony Smith) are
  blocked because their current factual roster status is not a
  currently-rostered status (reserve/development); 1 (Jam Miller) is
  blocked because its exact current identity is unresolved.
- **The bug:** every place this was surfaced to the owner (the header
  badge popup text, the `redraft_bootstrap` warning, and the Data Health
  readiness message in `_redraft_health_payload`) asserted a single
  blanket phrase — "position conflicts with the current factual registry"
  — for all 7 rows, even though the correct per-row `reason` was already
  parsed by `_bundled_redraft_blocked_rows` and simply discarded before
  reaching any of the three message-construction sites
  (`src/application/desktop_facade.py` lines ~1936, ~2087-2090, ~7651).
  Confirmed live: the real running badge popup (pre-fix) read "...remain
  excluded because their draft positions conflict with the current
  factual registry; no values were imputed" for all 7 names, which is
  factually wrong for 5 of them.
- Consumers: header badge popup, `redraft_bootstrap` warnings array, Data
  Health page readiness message (`Ready · 7 blocked players visible` /
  the accompanying message line).
- Verdict: **FIXABLE — a real, narrow display/classification-accuracy
  bug.** Fixed by adding
  `DesktopBackendFacade._blocked_seed_reason_breakdown` (static method,
  groups the already-computed per-row `reason` into a counted,
  human-readable breakdown, e.g. "2 rows -- draft position conflicts with
  current factual registry position; 4 rows -- current factual roster
  status is not a currently-rostered status; 1 row -- exact current GSIS
  identity unresolved") and wiring it into all three message-construction
  sites. Nothing about which rows are blocked, why they're blocked in the
  underlying data, or the CSV itself changed — this is purely a text
  accuracy fix that surfaces data already computed and previously thrown
  away. Does not touch roster legality core rules, the governed valuation
  model, or `LeagueSnapshot`/lifecycle-resolver/envelope semantics.

### Refresh behavior (LIVE OBSERVATION)

Clicked the Data Health page's "Refresh" button in the real running
browser session. It issued real `GET` calls to
`/api/v1/redraft/data-health`, `/api/v1/bootstrap`, and
`/api/v1/redraft/status-overrides` (all real 200s, confirmed via
`read_network_requests`, not inferred from UI alone). None of the 3 real
issues are refresh-resolvable in this isolated environment (ADP has never
been imported here; the Sleeper scoring gap and rookie-block CSV are both
static configuration/seed state, not something a refresh re-fetches or
changes). This is correct, expected behavior, not a bug.

### Header consistency (LIVE OBSERVATION)

Badge showed "3 data issues" before and after refresh — count stayed
consistent, not stuck on a stale cached value (it re-queried the backend
and got the same real 3-issue state back, which is the correct outcome
since nothing about the real underlying data changed).

### Note on verifying the fix live

The backend process (PID 7924) has no `--reload` flag and was correctly
**not restarted or killed** in this pass (explicit constraint from the
dispatch). This means the live badge text observed in this session still
shows the pre-fix wording — the fix itself is verified by direct code
inspection plus 4 passing regression tests
(`tests/test_redraft_blocked_rookie_reason_breakdown.py`), not by a
second live browser round-trip. A later worker (or a backend restart) can
confirm the corrected wording renders live.

### Files changed this pass

- `src/application/desktop_facade.py` — added
  `_blocked_seed_reason_breakdown` static helper; updated 3 message sites
  (`redraft_bootstrap` warning, `redraft_bootstrap` notice, and
  `_redraft_health_payload`) to use it instead of a hardcoded blanket
  "position-conflict" phrase; `_redraft_health_payload` gained an optional
  `blocked_reason_breakdown: str = ""` keyword parameter (backward
  compatible, single real caller updated).
- `tests/test_redraft_blocked_rookie_reason_breakdown.py` (new) — 4 tests:
  grouping of distinct real reasons, missing-reason fallback text,
  empty-input handling, and a guard against the real bundled CSV
  regressing back to a uniform reason (which would make the fix's premise
  stale).

### Regression scope check

Ran the directly-related existing suites after the change:
`tests/test_redraft_profile_practical_mode_toggle.py`,
`tests/test_redraft_page_v1.py`,
`tests/test_desktop_facade_architecture_wiring.py`,
`tests/test_desktop_http_api.py`. 3 pre-existing failures in
`test_redraft_profile_practical_mode_toggle.py`
(`test_rostering_k_dst_without_practical_mode_now_works_automatically`,
`test_manual_kdst_assets_reach_bootstrap_without_practical_mode`,
`test_enabling_practical_mode_lets_the_same_k_dst_profile_generate_a_ranking`)
— confirmed via `git stash`/rerun that these fail identically **before**
this pass's change too (real cause: a time-based projection-freshness
fixture, "source_as_of exceeds the 30-day freshness window", unrelated to
this pass and not previously catalogued in this session's memory of known
worktree baseline failures — flagging for the next worker as a possibly
new/undocumented pre-existing failure worth adding to the baseline list).
All other tests in those 4 files passed. No test that asserts on the old
"position-conflict" wording existed anywhere in the repo (grepped first).

### Open issues for next worker

1. `test_redraft_profile_practical_mode_toggle.py`'s 3 K/DST
   practical-mode tests fail on a time-based freshness-window check
   against a fixture built from `GOVERNED_COMBINED_608_PROJECTION_SNAPSHOT.csv`
   — pre-existing, unrelated to this pass, not yet in the documented
   5-failure or 323-failure baselines. Worth confirming whether this is a
   new regression from a recent commit or an existing, just-undocumented
   staleness issue.
2. Data Issue 1 (Market ADP unavailable) and Data Issue 2 (Sleeper scoring
   needs review) remain open by design — genuinely unavailable/
   out-of-scope, not fixed, left showing (correct). Issue 1's real
   recovery path is an owner-driven ADP import through the existing Market
   Data / ADP control center; Issue 2 is a scoring-model scope boundary
   (2-point-conversion support specifically is worth a future scoped
   look — flagged, not touched).
3. The fix to Data Issue 3's message text has not been re-verified live
   (backend process intentionally left running/unrestarted per this
   pass's constraints) — confirm the corrected wording renders correctly
   in the real header badge and Data Health page once the backend is next
   restarted.
4. Shared upgrade A (Sleeper catalog caching) is the next scoped workstream
   per the dispatch — not started this pass.

---

## Worker 2 — Shared upgrade A: Sleeper player-catalog cross-request cache (2026-09-16)

**Branch/worktree:** same as Worker 1, `upgrade/nwr-prospective-outcomes-v1-20260914`
at `C:\NWR\prospective-outcomes-v1`. Started at HEAD `a5c3bcf6` (Worker 1's
commit; clean, matched Worker 1's own reported end state). Did not push,
did not touch `main`, did not force anything.

### Problem confirmation (INSPECTED CODE)

Grepped every real `players/nfl` call site in `src/`. The broader
cross-request problem flagged as explicitly-left-open by the prior
same-night fix was confirmed STILL PRESENT: 12 separate call sites inside
`DesktopBackendFacade` (`src/application/desktop_facade.py` — practical
K/DST setup, opponent rosters, free agents, my roster, weekly projections,
weekly lineup, K/DST streamer, trade analysis, trade package search, trade
finder, Sleeper draft sync) each independently re-fetched the full
~14.66MB / 12,227-player catalog on its OWN separate HTTP request, with
zero sharing across requests. The prior fix
(`_sleeper_fetch_cache_local`/`_sleeper_get_json`) is a `threading.local()`,
OPT-IN, PER-REQUEST cache that only `redraft_weekly_home_actions` turns on
for the duration of its own 5 sub-calls, then tears down — every other
endpoint (Waivers alone, Trade Finder alone, Weekly Projections alone,
etc.) still re-fetched the catalog fresh, every single call, exactly as
the prior fix's own docstring disclosed. Also found 4 more `players/nfl`
call sites outside the facade (`sleeper_redraft_owner_service.py`'s
resync, plus 3 explicit one-shot export/preview tools — `sleeper_import_
service.py`'s `export_sleeper_snapshot`, `public_data_preview_import_
service.py`, `real_draft_pool_preview_service.py`) — deliberately left
these OUT of scope (see below).

### Fix (exact design)

New module `src/services/sleeper_player_catalog_cache.py`:
`SleeperPlayerCatalogCache` — a bounded (default TTL 15 minutes,
`DEFAULT_TTL_SECONDS`), in-memory, PROCESS-lifetime cache holding exactly
one entry: the player catalog. `get(client, force_refresh=False)` holds a
single `threading.Lock` for its ENTIRE duration, including the real
network fetch when one is needed — this is the real de-duplication
mechanism: any concurrent caller blocks on the same lock and, once it
acquires it, finds the now-fresh cache already populated, so it returns
without ever calling `client.get_json` itself. A failed fetch raises
`SleeperPlayerCatalogError`/the underlying exception WITHOUT touching
cached state (never poisons the cache, never falls back to silently
serving expired data as if fresh — the caller gets an honest error). A
module-level singleton (`_default_cache`) plus `get_sleeper_player_catalog
(client, force_refresh=False, cache=None)` is the real shared entry point.

Reuse decision (per the dispatch's explicit ask to check the existing
mechanism first): the existing `_sleeper_fetch_cache_local` is
thread-local BY DESIGN and caches every path generically, including
rosters — extending it directly to cross-request scope would either break
its careful non-caching guarantee for roster/user data, or require
building a path-allowlist inside it anyway. Instead, `_sleeper_get_json`
(the ONE existing seam every facade Sleeper call already goes through) was
extended with a single special case: the literal path `"players/nfl"` now
routes to `get_sleeper_player_catalog(client).players`; every other path
is completely unchanged (still only the pre-existing per-request
thread-local cache, never cross-request). All 12 facade call sites that
previously called `client.get_json("players/nfl")`/`SleeperHttpClient().
get_json("players/nfl")` directly were changed to go through `self.
_sleeper_get_json(client, "players/nfl")` instead, so every one of them
now benefits. `sleeper_redraft_owner_service.py`'s resync path was
DELIBERATELY left un-cached (see Open Issues) — a real, principled scoping
decision, not an oversight.

### Verification (REAL MEASUREMENTS, not inference)

- **Cold vs warm (LIVE OBSERVATION against the real Sleeper API,
  read-only, authorized):** cold fetch (real network call) `0.697s` for
  the real, live catalog (`12,227` players — matches Worker 1's/the prior
  session's figure). Warm cache hit immediately after: `0.00001s`. ~87,000x
  for this one comparison — the number itself is not the generalizable
  claim; the qualitative claim (a warm hit is a dict lookup under a lock,
  not a network round trip) is.
- **Concurrent dedup (LIVE OBSERVATION against the real Sleeper API):** 6
  real `threading.Thread`s released simultaneously via a `threading.
  Barrier`, all calling the shared cache against the REAL, unmocked
  `SleeperHttpClient`. Instrumented `get_json` counted exactly **1** real
  network fetch for the 6 concurrent callers; total elapsed `0.676s` (≈ one
  fetch's worth of time, not 6x). All 6 threads received real, valid
  catalog data. Also independently proven with a fake, artificially-
  delayed (0.2s) client and 8 threads in `tests/test_sleeper_player_
  catalog_cache.py::test_concurrent_callers_trigger_exactly_one_real_fetch`
  (ACTUAL TEST RESULT, passes).
- **Expiry (ACTUAL TEST RESULT):** `test_expiry_forces_a_real_refetch` —
  TTL=0.05s, real `time.sleep(0.08)`, second `get()` performs a real
  second fetch (`client.calls == 2`).
- **Refresh (ACTUAL TEST RESULT):** `test_force_refresh_bypasses_a_still_
  valid_cache` and `test_invalidate_forces_a_real_refetch` — both force a
  real second fetch despite a still-valid cached entry.
- **Provider failure (ACTUAL TEST RESULT):** `test_provider_failure_is_
  never_cached_and_raises_honestly` — a failed fetch raises a real
  `OSError` to the caller AND the very next call performs a real fetch
  (not a cached failure, not a cache-poisoned bad state).
  `test_provider_failure_after_a_prior_success_does_not_serve_stale_
  forever` — a forced-refresh failure after a prior successful cache
  raises rather than silently re-serving the old value.
  `test_malformed_response_raises_a_typed_error_and_is_not_cached` — a
  non-dict payload raises `SleeperPlayerCatalogError`, not cached.
- **Data separation (ACTUAL TEST RESULT):** `test_roster_ownership_
  transaction_faab_paths_never_enter_the_catalog_cache` — drives
  `DesktopBackendFacade._sleeper_get_json` directly for
  `league/.../rosters`, `.../users`, `.../traded_picks`, `.../drafts`,
  `state/nfl` (live week), and `league/{id}` (settings/FAAB budget): every
  one is fetched fresh on each of 2 calls (never memoized), and none of
  them move the catalog cache's own fetch counter — only the literal
  `players/nfl` path does.

### A real regression this pass found in its OWN new code, and fixed

The new process-wide singleton cache initially broke test isolation
ACROSS THE WHOLE SUITE: any test that monkeypatches `SleeperHttpClient.
get_json` with a per-test-varying fake player-catalog fixture (several
Waivers/Trade-Finder/identity-boundary tests do exactly this) could
silently receive a STALE catalog cached by an earlier test within the same
pytest process, since the singleton has no reason to know the underlying
fake client "changed." Caught this via a real full-suite regression run
(14 test failures, all order/pollution-dependent, e.g. `add_candidates`
length or `identityStatus` flipping between runs). Fixed with a new,
narrowly-scoped `tests/conftest.py` (did not exist before this pass): one
autouse fixture that invalidates the catalog-cache singleton before and
after every test. Re-ran the full previously-failing set plus a further
~300 related tests afterward — all green. This does not affect real
production behavior (the singleton is correctly long-lived there); it only
prevents the new cache from leaking state between test functions.

### Regression scope check

Ran (all ACTUAL TEST RESULT): the new test files, `test_weekly_home_
sleeper_fetch_caching.py` (updated — 2 of its assertions changed to
reflect the new, INTENTIONALLY different cross-request catalog-cache
behavior; roster/user freshness assertions unchanged), `test_sleeper_
redraft_owner_service.py`, `test_desktop_facade_architecture_wiring.py`,
`test_desktop_http_api.py`, plus ~21 more Sleeper/waiver/trade/identity-
adjacent files — **327 passed, 0 failed**. `test_desktop_application_api.
py`: 4 failed / 46 passed, confirmed via `git stash` to be BYTE-IDENTICAL
before and after this pass's change (pre-existing, unrelated —
`app`-import boundary assertion and 3 others, not the 5-failure baseline
Worker 1/prior sessions documented for a different worktree). `test_
redraft_profile_practical_mode_toggle.py`: same 3 pre-existing
freshness-window failures Worker 1 already flagged, confirmed unaffected
by this pass. `test_routine_refresh_service.py`: 1 pre-existing failure,
confirmed via `git stash` to be identical before/after.

### Deliberate scoping decisions (what was NOT changed, and why)

- `sleeper_redraft_owner_service.py`'s `resync_sleeper_redraft_profile`
  still calls `http.get_json("players/nfl")` directly, NOT through the new
  cache. Tried routing it through the cache first; this broke 2 real
  existing tests (`test_resync_refreshes_the_stored_roster_snapshot_
  without_any_sleeper_write`, `test_resync_records_unresolved_players_
  without_dropping_them`) that deliberately pass a DIFFERENT fake client
  (with a different fake catalog) per call to prove resync always reflects
  whatever `client` it's given. Resync is a rare, explicit, one-shot owner
  action, not part of the repeated-many-times-per-session hot path this
  fix targets — reverted cleanly, left uncached, documented in the module
  with a comment.
- `sleeper_import_service.py`'s `export_sleeper_snapshot` and the two
  preview/export services (`public_data_preview_import_service.py`,
  `real_draft_pool_preview_service.py`) were left untouched — these are
  explicit, infrequently-run, point-in-time archival/export tools, not the
  live interactive multi-endpoint hot path the dispatch described.
- No UI "refresh player catalog" action exists today (grepped
  `src/desktop_api/server.py` — the only existing `forceRefresh` wiring is
  for weekly projections, unrelated). `SleeperPlayerCatalogCache.
  invalidate()` and `get(..., force_refresh=True)` both exist and are
  tested, ready for a future explicit UI action to call if one is ever
  added — not wired to any endpoint this pass, since none was asked for.

### Running processes status

Frontend (127.0.0.1:1422) and backend (127.0.0.1:18742) were NOT restarted
this pass — confirmed still up and responding at the end (`GET /` → 200;
`GET /api/v1/bootstrap` → 401 `AUTHENTICATION_REQUIRED`, the same
contract-shaped response Worker 1 documented, not a crash). Following
Worker 1's own precedent: the backend has no `--reload` flag, and a
restart would issue a NEW random API token, invalidating any already-open
real browser session's stored auth — a real cost to other workers/the
owner not worth paying here, since this pass already obtained genuine LIVE
measurements (real network calls against the actual Sleeper API, real
threads, real wall-clock timings — see above) WITHOUT needing to touch the
shared desktop backend process. Net effect: this pass's code changes are
NOT yet live in the currently-running backend process; they will take
effect on the next real restart (by the owner or a later worker).

### Files changed this pass

- `src/services/sleeper_player_catalog_cache.py` (NEW) — the cache itself.
- `src/application/desktop_facade.py` — added the import; `_sleeper_get_
  json` special-cases `"players/nfl"` to route through the new cache
  (docstring rewritten to explain the two-tier split); all 12 direct
  `players/nfl` call sites changed to go through `self._sleeper_get_json`.
  No other behavior touched — roster/user/traded_picks/drafts/state paths
  are byte-for-byte the same code path as before.
- `src/services/sleeper_redraft_owner_service.py` — comment-only change
  (documents the deliberate decision NOT to cache this call site).
- `tests/test_sleeper_player_catalog_cache.py` (NEW) — 11 tests: cold/warm,
  concurrent dedup, expiry, force-refresh, invalidate, 2 provider-failure
  variants, malformed-response, default-TTL-bound, singleton-sharing, and
  the roster/ownership/transaction/FAAB data-separation regression test.
- `tests/test_weekly_home_sleeper_fetch_caching.py` — updated 3 existing
  tests to reflect the new, intentional cross-request catalog-cache
  behavior (2 tests renamed/re-asserted; roster/user freshness assertions
  unchanged) plus singleton-cache isolation calls.
- `tests/conftest.py` (NEW — did not exist before this pass) — one
  autouse fixture resetting the catalog-cache singleton between tests
  (see "A real regression this pass found" above).

### Hard boundary check

Did not touch `marginal_roster_utility_v2`, its weights, the governed
valuation model, draft recommendation logic, roster legality,
`LeagueSnapshot`/`LeagueWorkspaceContext`/lifecycle-resolver/
`DecisionResultEnvelope`/`PlayerAvailabilityStatus` semantics, or any
FAAB/Add-Drop/waiver DECISION logic — only the underlying catalog-fetch
performance/plumbing feeding into those consumers, exactly as scoped.

### Open issues for next worker

1. The currently-running backend process does not yet have this pass's
   code — confirm the corrected cross-request caching behavior renders
   live once the process is next restarted (same open item pattern as
   Worker 1's #3).
2. `resync_sleeper_redraft_profile` (owner "resync from Sleeper" action)
   deliberately still fetches the catalog fresh on every resync, uncached
   — correct today, but worth a future look if resync ever becomes a
   high-frequency action rather than an occasional explicit one.
3. Shared upgrade B (stale-response race class across all async tools) is
   the next scoped workstream per the dispatch — not started this pass.

---

## Worker 3 — Shared upgrade B: stale-response/label-drift audit across the Redraft frontend (2026-09-16)

**Branch/worktree:** same as Workers 1-2,
`upgrade/nwr-prospective-outcomes-v1-20260914` at
`C:\NWR\prospective-outcomes-v1`. Started at HEAD `63f39ac5` (Worker 2's
commit; clean). Did not push, did not touch `main`, did not restart the
running frontend (127.0.0.1:1422) or backend (127.0.0.1:18742) -- both
confirmed still up at the end of this pass (LIVE OBSERVATION: `GET /` ->
200; `GET /api/v1/bootstrap` -> 401 `AUTHENTICATION_REQUIRED`, same
contract-shaped response every prior worker documented, not a crash).

### Task

Audit every other async tool/surface for the SAME bug class Worker/prior
session found and fixed in FAAB (`resolveFaabDisplay`, a single-resolved-
response-derived display, proven via `@ts-expect-error`): a visible
label/provenance following current React INPUT state while the data next
to it still comes from a stale resolved response. `useAsync` +
`createStaleResponseGuard` (weekly-shared.tsx) is the existing shared
ordering-safety mechanism.

### Methodology note

Every finding below is INSPECTED CODE plus, where noted, ACTUAL TEST
RESULT (`npx vitest run`, `npm run typecheck`, both from
`C:\NWR\prospective-outcomes-v1\desktop`) -- no LIVE Chrome session was
used this pass (the running backend's auth token was not available to this
worker's session, and per the dispatch a restart was to be avoided unless
needed; it was not needed since every finding was reachable and provable
by direct code inspection + unit test, matching how Worker 2 already
verified its own new cache logic without touching the shared process).

### PASS (already safe, with evidence) -- no changes needed

- **`createStaleResponseGuard`/`useAsync` (weekly-shared.tsx) itself**:
  already has thorough adversarial-ordering test coverage
  (`weekly-shared.test.ts`, 4 cases: stale-resolves-late, non-stale,
  rapid multi-switch, same-profile reload) proving requirement 3 (an
  older in-flight response can never overwrite a newer one) holds for
  every consumer of this shared hook.
- **Manage Leagues / league switcher (highest-priority item)**:
  `leagues.tsx` (`LeaguesPage.activate`) uses a `useRef` in-flight guard
  plus a disabled-while-working button, and navigates only with the
  FRESH bootstrap the activation call itself returned. `shell-identity.tsx`
  (`ShellIdentity.switchLeague`, the header quick-switcher) already has a
  documented, previously-fixed per-call request-id guard
  (`switchRequestRef`) for exactly the "owner follows a different route
  mid-switch" race. `RedraftApp.tsx`'s `LeagueScopedPage` -- the ONE gate
  every `/league/:leagueKey/*` route passes through -- activates an
  inactive target profile before rendering anything, and renders its
  children under `<div key={leagueKey}>`, which forces a full REMOUNT of
  the entire page subtree (and therefore every in-flight fetch's cleanup)
  on every league switch. Net effect: a previous league's roster/budget/
  recommendations structurally cannot survive a switch into another
  league on any routed page. Already hardened; no changes made.
- **Attention Center** (`attention-center.ts`/`attention-center-page.tsx`):
  already has a 3-layer defense (sequential per-league reads inside one
  sweep with an unconditional `finally`-restore of the originally-active
  profile; a page-level `generation`/`inFlight` ref guard; a MODULE-LEVEL
  serialization queue so two sweeps can never interleave their
  `activateRedraftProfile` calls) plus dedicated regression tests
  (`attention-center.test.ts`, not modified this pass). Read in full;
  found no gap. One residual, NOT reproduced or fixed this pass: a
  background sweep and an unrelated in-app league navigation both call
  the same shared single-active-profile backend pointer -- see Open
  Issues.
- **Cheat Sheet** (`cheat-sheet.tsx`): has NO independent async fetch at
  all -- every field it renders is a pure derivation from the single
  `data: RedraftBootstrap` prop, which the app replaces atomically on
  every refresh/switch. Safe by construction; the FAAB bug class requires
  two independently-timed data sources to exist in the first place.
- **Decision History** (`decision-history.tsx`): `DecisionHistoryPage`
  and `ClassSummaryPanel` are single-fetch, no-filter `useAsync` readers
  (title/eyebrow read straight off the resolved `result`, e.g.
  `result.leagueName`/`result.totalCount`, never a separate input state)
  -- no selector/filter exists that could desync label from data. Also
  fully remounted on league switch via `LeagueScopedPage`'s `key`.
  `OwnerActionCell`'s per-row recording state is row-local, gated by its
  own `disabled={submitting}`, keyed by `traceId` -- reviewed, no gap
  found.
- **Draft Room (spot-checked, not exhaustive)**: the whole page is force-
  remounted on league switch via `key={data.activeProfileId}` at the
  route level (`RedraftApp.tsx`), eliminating the highest-risk case
  structurally. Its own internal DecisionBundle/RAV fetches
  (`draft-room-v2.tsx` ~L1263-1352) all use the same `let cancelled =
  false` / cleanup-sets-it-true pattern `createStaleResponseGuard`
  formalizes (functionally identical, just inlined). Specifically
  checked the position-filter change path (the closest analog to FAAB's
  own input-vs-data risk): `SuggestionsTab` does NOT keep showing a stale
  table during a position-filter-triggered refetch -- it replaces the
  table with a "Computing…" `EmptyState` whenever `loading` is true
  (L2577), so there is no window where a label and stale data could both
  be on screen at once. NOT exhaustively audited (Compare tab, Board tab,
  and the rest of this 4200-line file were not individually reviewed --
  see Open Issues).
- **Market Data / ADP** (`adp-providers.tsx`): confirmed (grep) this file
  uses no `useAsync` at all -- every fetch is an explicit owner-triggered
  import/preview action with its own local `working` state, not an
  auto-refetch-on-selector-change surface, so the FAAB race precondition
  (an input change silently triggering a new fetch behind an unchanged
  label) doesn't apply here. Not deeply audited beyond confirming this
  shape.

### FIXED -- real instances of the same bug class found and fixed

1. **Weekly Home week-display race** (`in-season.tsx`,
   `WeeklyHomePage`): the page title (`"${activeName} · Week ${week}"`)
   and the "Week" chip in the THIS WEEK strip both read the raw
   `week` INPUT state (`manualWeekOverride ?? providerWeek ?? 1`), while
   the actions/lineup/free-agent panels below stayed on the PREVIOUS
   `useAsync` response (`actions`) until the new week's fetch resolved.
   Concretely reproducible by inspection: the SAME page's own
   `ProviderStatusLine` (inside the "Projected lineup" panel) already
   correctly reads its week off the resolved response
   (`health.week`), so during the pending gap after a week change the
   page could show two DIFFERENT week numbers to the owner at once (title
   says the new week; `ProviderStatusLine` still says the old one).
   **Fix**: added `resolveWeekDisplay(requestedWeek, resolvedWeek)` to
   `weekly-shared.tsx` (same structural, single-object-derivation pattern
   as `resolveFaabDisplay`) -- the contract's `WeeklyHomeActionsResult`
   already carries its own `week` field, confirmed by reading
   `contracts/src/index.ts`. Title/chip now render
   `weekDisplay.displayWeek` (the RESOLVED response's own week when one
   exists, never the raw input), and an explicit "Updating…" banner
   (structural check: `actions != null && actions.week !== week`, not a
   `working`-flag guess) now marks the pending window instead of leaving
   it unmarked.
2. **Start/Sit week-display race** (`in-season.tsx`, `LineupPage`): same
   bug, same fix. The title (`"Start / Sit — THIS WEEK (Week
   ${week})"`) read the raw input while `result` (starters/swaps/bench)
   stayed on the prior week. `WeeklyLineupResult.week` (confirmed present
   on the contract) is the resolved-response source of truth; title now
   uses `resolveWeekDisplay(week, result?.week ?? null)`, plus a new
   "Updating…" banner (this page previously had NO pending indicator of
   any kind for a week change).
3. **Find Trades mode-display race** (`trades.tsx`, `FindTradesTab`):
   `useAsync` auto-refetches whenever the search mode segmented control
   (FIND_WIN_WIN / TARGET_PLAYER / IMPROVE_POSITION) changes, but the
   candidate cards kept rendering the PREVIOUS mode's `result` -- a
   completely different kind of search -- unmarked, until the new mode's
   fetch resolved. `TradePackageSearchResult.mode` (confirmed present on
   the contract) echoes back which mode was actually searched. **Fix**:
   added `isTradePackageSearchStale(result, requestedMode)` to
   `trades-explain.ts` (structural check against the response's own
   `mode`) and wired an "Updating…" banner into `FindTradesTab` when
   `stale` is true.
4. **Compare "Roster Fit" false-negative pending bug** (`pages.tsx`,
   `CompareContent`) -- a different SHAPE of the same underlying class
   (a definitive claim rendered from data that hadn't arrived yet, not a
   stale-response overwrite): switching Compare into "Roster Fit" mode
   (or switching either compared player) resets `myRoster`/`waivers` to
   `null` while the new fetch is in flight. The pre-existing
   `rosterFitFor` fell through BOTH `myRoster?.roster.find` and
   `waivers?.addCandidates.find` whenever either was still `null` and
   confidently rendered **"Not a current free agent on this league"** --
   a FALSE claim, not an honest "still reading" state, for as long as
   either read was pending (or had failed). **Fix**: extracted and fixed
   as an exported pure function `resolveRosterFit(myRoster, waivers,
   playerId)` in `pages.tsx` -- a `null` resolved response is now treated
   as "unknown, still reading" (`"Reading your roster…"` /
   `"Reading free-agent availability…"`), never as evidence of absence;
   only a genuinely-resolved, non-null response for BOTH reads can now
   produce the "not a free agent" verdict.

### TESTS ADDED (all ACTUAL TEST RESULT, passing)

- `weekly-shared.test.ts`: 4 new cases for `resolveWeekDisplay` (first
  load, settled match, the exact pending-race window, clears once the
  new response lands).
- `trades-explain.test.ts`: 4 new cases for `isTradePackageSearchStale`
  (never stale before any response, matching mode, the exact pending-race
  window, clears on landing).
- `pages.test.ts`: 5 new cases for `resolveRosterFit` (both pending, only
  waivers pending, on-roster short-circuits before waivers resolves, the
  definitive "not a free agent" verdict only once both resolve, a real
  waiver-add-candidate verdict).
- No `@ts-expect-error` compile-time test was added this pass (FAAB's own
  precedent) -- none of these 3 fixes have a parameter shape that would
  let a caller accidentally pass mismatched label/data sources and still
  compile (`resolveWeekDisplay`/`isTradePackageSearchStale` take the
  requested value and the resolved response's own field directly;
  `resolveRosterFit` takes the two resolved responses directly) -- the
  ordinary `expect(...).toBe(...)` coverage above already exercises the
  exact race condition each function exists to prevent.

### Regression scope check (ACTUAL TEST RESULT)

`cd desktop && npx vitest run`: **443 passed, 0 failed** (29 test files,
full frontend suite, not a targeted subset). `npm run typecheck` (`tsc -b
apps/dynasty/tsconfig.json apps/redraft/tsconfig.json`): clean, 0 errors.
A benchmark artifact
(`docs/codex/prospective_outcomes_v1/multi_league_scale_v1/frontend_bench_results.json`)
was incidentally rewritten by running the full suite (a benchmark test's
own side effect, unrelated to this pass's changes) and was reverted via
`git checkout --` before committing -- not part of this pass's diff.

### Files changed this pass

- `desktop/apps/redraft/src/weekly-shared.tsx` -- added
  `resolveWeekDisplay`.
- `desktop/apps/redraft/src/weekly-shared.test.ts` -- 4 new tests.
- `desktop/apps/redraft/src/in-season.tsx` -- `WeeklyHomePage` and
  `LineupPage` both wired to `resolveWeekDisplay`; added "Updating…"
  banners.
- `desktop/apps/redraft/src/trades-explain.ts` -- added
  `isTradePackageSearchStale`.
- `desktop/apps/redraft/src/trades-explain.test.ts` -- 4 new tests.
- `desktop/apps/redraft/src/trades.tsx` -- `FindTradesTab` wired to
  `isTradePackageSearchStale`; added "Updating…" banner.
- `desktop/apps/redraft/src/pages.tsx` -- extracted/exported
  `resolveRosterFit`; `CompareContent` now calls it instead of its old
  inline (buggy) version.
- `desktop/apps/redraft/src/pages.test.ts` -- 5 new tests.

### Hard boundary check

Did not touch `marginal_roster_utility_v2`, its weights, the governed
valuation model, draft recommendation logic, roster legality,
`LeagueSnapshot`/`LeagueWorkspaceContext`/lifecycle-resolver/
`DecisionResultEnvelope`/`PlayerAvailabilityStatus` semantics. Every fix
in this pass changes ONLY whether the DISPLAYED label/pending-state
correctly corresponds to the request/response that produced the data next
to it -- no recommendation, score, or ranking value was changed anywhere.

### Open issues for next worker

1. **Draft Room was only spot-checked, not exhaustively audited** (4220
   lines) -- the Compare tab, Board tab, and the rest of
   `draft-room-v2.tsx` beyond the DecisionBundle/RAV fetch effects and
   the Suggestions position-filter path were not individually reviewed.
2. **Attention Center residual cross-surface risk (not reproduced, not
   fixed)**: Attention Center's background per-league sweep temporarily
   activates OTHER leagues on the shared single-active-profile backend
   pointer, one at a time, before restoring the original. If the owner
   navigates to a different league-scoped page (e.g. via a direct link,
   not through Attention Center itself) WHILE that sweep is mid-flight,
   that navigation's own `LeagueScopedPage` activation call and the
   sweep's own `activateRedraftProfile` calls both target the same
   backend pointer outside of Attention Center's own module-level
   serialization queue (that queue only serializes AttentionCenter-vs-
   AttentionCenter calls, not AttentionCenter-vs-everything-else). Not
   reproduced live this pass; flagged for a future worker with browser
   access to actually exercise it.
3. **Players/Market tab (`adp-providers.tsx`) was only confirmed to have
   no `useAsync` usage (grep), not line-by-line audited** for its own
   explicit-action async handlers (import/preview/apply flows) --
   plausible lower risk given the explicit-submit shape, but not proven
   safe the same rigorous way the fixed surfaces were.
4. Trades' `AnalyzeTab` (the ANALYZE tab, not FIND TRADES) was reviewed
   and judged safe-by-construction (a single explicit "Analyze trade"
   button, disabled while `working`, so no overlapping-request race is
   reachable via the UI) but the `result` panel intentionally does NOT
   clear itself when the owner edits `gives`/`receives` after seeing a
   result and before re-clicking Analyze -- an old result can sit next to
   an already-edited (not-yet-submitted) player selection. Judged
   acceptable explicit-submit-form UX (same shape as a calculator), not
   the FAAB auto-refetch race class, and NOT fixed this pass -- worth a
   second opinion if the owner reports confusion here.
5. Section 3C (data-age/recommendation-basis labeling, tracing the
   season-projection source behind Harrison/Tracy) and Section 3D
   (completing small broken interactions found along the way) are next,
   per the dispatch.
