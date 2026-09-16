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

---

## Worker 4 — Section 3C: season-projection provenance trace + data-age/basis labeling (2026-09-16)

**Branch/worktree:** same as Workers 1-3,
`upgrade/nwr-prospective-outcomes-v1-20260914` at
`C:\NWR\prospective-outcomes-v1`. Started at HEAD `186a2b9a` (Worker 3's
commit; clean). Did not push, did not touch `main`. Frontend
(127.0.0.1:1422) and backend (127.0.0.1:18742) were NOT restarted or
touched -- confirmed still up at the end (LIVE OBSERVATION: `GET /` -> 200;
`GET /api/v1/bootstrap` -> 401 `AUTHENTICATION_REQUIRED`, same
contract-shaped response every prior worker documented). Zero backend/
Python files were changed this pass -- every change is frontend-only
(`desktop/apps/redraft/src/*`).

### Part 1 -- projection-source trace (INSPECTED CODE)

Read `docs/codex/waiver_night_v1/HARRISON_TRACY_INVESTIGATION_V1.md` and
`WAIVER_FIX_CYCLE_V1_CHECKPOINT.md` in full first, per the dispatch --
Harrison's arithmetic finding (replacement-level-by-construction, 0.0 is
correct) was NOT re-opened or re-litigated.

Traced the season-level projection's own origin and refresh mechanism,
which that investigation had explicitly left open:

- **Origin**: `docs/hq/model/nwr_redraft_2026_freeze_v7_bundled_seed_v1_20260912/
  GOVERNED_COMBINED_564_PROJECTION_SNAPSHOT.csv` (491 veteran + 73 rookie
  rows), admitted `source_as_of=2026-09-08` via the real
  `install_projection_snapshot()` governance mechanism (`docs/codex/
  NWR_PROSPECTIVE_2026_FREEZE_V7_20260908.md`). Harrison's own row:
  `source_id=NWR_REDRAFT_2026_STATUS_FILTERED_PRIOR_SEASON_PERSISTENCE_V1`,
  `provenance="nflverse seasonal stats t-1 + current nflverse GSIS
  registry"`, `games=12.0` -- a full-season stat line built from PRIOR
  SEASON (t-1) rates projected across an estimated full season of games,
  not a mid-season recomputation.
- **Scoring**: `redraft_engine_v1_service.py::score_projection` sums the
  row's raw stat fields (receptions, receiving_yards, etc.) into one
  season total. `redraft_2026_projection_model_service.py` (the model that
  built these rows) computes each stat as `per_game_rate * projected
  games` -- a FULL-SEASON total by construction. Grepped the entire
  `src/` for any in-season decay/reduction (`games_remaining`,
  `weeks_remaining` applied to `projected_points`, `/ games` on this
  specific value): **none exists**. No call site anywhere recomputes or
  reduces this value as real season weeks pass.
- **Refresh mechanism**: manual only -- a new owner-approved governance
  admission (`install_projection_snapshot()`), gated by `MAX_PROJECTION_
  AGE_DAYS` (30-day staleness check). Never automatic, never per-week.
- **FULL-SEASON vs REMAINING-SEASON determination**: **this is a
  FULL-SEASON projection, built pre-draft/pre-season, not reduced for
  games already played.** Confirmed both by the CSV's own provenance
  string and by the projection-model's per-game-rate * full-season-games
  construction.
- **Consistency across consumers**: every real consumer (Rankings, Cheat
  Sheet, Compare "Rest of Season", Waivers `REST_OF_SEASON` mode, FAAB,
  Trades) reads the exact SAME computed `replacement_adjusted_value`/
  `projected_points` from the ONE `generate_rankings()` call for a given
  profile -- confirmed by direct grep/read, no second independently-
  computed "remaining season" number exists anywhere in this codebase.
  **Computationally this is consistent** (no call site silently
  reinterprets or re-derives the number differently from another). The
  real gap found is a LABELING one, not an arithmetic one (see below).
  Also confirmed the codebase already keeps season-level `sourceAsOf`
  (`RedraftRanking.sourceAsOf`, bootstrap `status.sourceAsOf`) and
  weekly-level `sourceAsOf` (`WeeklyLineupResult.sourceAsOf`,
  `WeeklyProjectionsResult.sourceAsOf`) as genuinely SEPARATE typed
  fields -- the two horizons are not conflated in the data model itself.

### Part 1 -- consistency bug found (display-layer, not arithmetic)

Traced `redraft_weekly_home_actions` (`desktop_facade.py`, Weekly Home's
"NWR Actions" list): WAIVER and TRADE action cards are built from
`redraft_waivers(mode="REST_OF_SEASON")` / `redraft_trade_finder()` --
both driven entirely by the season-level governed ranking above. START_SIT
/ START_SIT_CLOSE_CALL cards are built from the real live weekly lineup
optimizer. The frontend (`in-season.tsx`, `WeeklyHomePage`) rendered
**every** action card's `freshness` caption from the SAME
`freshnessNote` (derived from `lineup.providerHealth`, the WEEKLY Sleeper
provider) regardless of category -- so a WAIVER/TRADE recommendation
(actually driven by the season snapshot, admitted `2026-09-08`,
potentially days/weeks old) was labeled with a same-day "Sleeper ·
updated <time>" freshness caption that has nothing to do with the data
actually backing it. This is the concrete, reproducible instance of "one
surface treats a season-basis number as if it shared the weekly
provider's freshness" the dispatch asked to check for. **No computed
value was ever wrong** -- only the freshness label borrowed an unrelated
source. Not a Harrison-class arithmetic bug; a display-basis mismatch.

**Fix** (`weekly-shared.tsx`): added `resolveHomeActionFreshness(category,
weeklyFreshnessNote, seasonSourceAsOf)`, a pure function that routes
WAIVER/TRADE categories to a `"NWR season ranking · admitted <date>"`
caption (falling back to the weekly note only if the season date is
itself unavailable) and leaves START_SIT/START_SIT_CLOSE_CALL/STREAMER on
the existing weekly note unchanged. Wired into `WeeklyHomePage`'s action
card map in `in-season.tsx`. 5 new tests in `weekly-shared.test.ts`.

### Part 2 -- data-age/basis labeling surfaced (all using ALREADY-COMPUTED
### backend provenance, no invented data, no backend changes)

Checked every surface the dispatch named (Start/Sit, Trades, Players/
Rankings, Cheat Sheet, Weekly Home) for whether backend-carried
provenance was already threaded through but not shown:

- **Start/Sit** (`LineupPage`): already well-labeled (own
  `providerHealth`/`freshnessNote`, `ProviderStatusLine`, an explicit
  "never confused with rest-of-season rankings" page description,
  confirmed `WeeklyLineupResult` is a genuinely separate weekly-sourced
  contract). No gap found -- not modified.
- **Weekly Home**: fixed the WAIVER/TRADE freshness-basis mismatch above.
- **Players/Rankings** (`pages.tsx`, `RankingsContent`): the ranking table
  already has a "Source as of" column (non-compact) but no caption
  explaining what that season-level number actually represents. Added a
  `resolveSeasonProjectionBasisCaption(data.status.sourceAsOf)` line above
  the table.
- **Compare** (`pages.tsx`, `CompareContent`): the "Rest of Season" mode
  reads the identical value Rankings calls "Season points"/"Proj pts" --
  two different labels for one unchanging number, with no caption
  connecting them. Added the same basis caption under the Mode toggle
  when `mode === "Rest of Season"`.
- **Cheat Sheet** (`cheat-sheet.tsx`): had `ballersStatusText`/
  `marketStatusText` compact status lines already but nothing for NWR's
  own season model. Added `nwrSeasonStatusText(data)` (same convention,
  reads `data.status.sourceAsOf`) into the existing compact header row.
- **Trades** (`trades.tsx`): had ZERO freshness/basis labeling anywhere
  (confirmed by grep before this pass -- no `sourceAsOf`/`providerHealth`/
  `freshness` references at all), despite `TradePlayerImpact.
  rosReplacementValue`/`marginalUtility` being driven by the same season
  ranking. Added the basis caption to both the Analyze tab's result panel
  and the Find Trades tab (using `data.status.sourceAsOf`, already
  bootstrap-level and already shown on the Data Health page -- no new
  backend field, no per-player plumbing needed since the whole snapshot
  shares one admission date).
- **Improve Team / Waivers-FAAB-Add-Drop** (`improve-team.tsx`, not
  explicitly named by the dispatch but the primary REST_OF_SEASON
  consumer): the existing "THIS_WEEK honesty" caption explained mode
  ranking-consistency but not projection basis. Extended Targets and FAAB
  tabs with the same `resolveSeasonProjectionBasisCaption`.

All of the above reuse ONE new pure function,
`resolveSeasonProjectionBasisCaption(sourceAsOf)` (`weekly-shared.tsx`),
following the same "small pure function, not scattered inline JSX"
precedent as `resolveFaabDisplay`/`resolveWeekDisplay`. It reads only
`data.status.sourceAsOf` -- an ALREADY-COMPUTED bootstrap field (verified
by inspection: `desktop_facade.py`'s `redraft_bootstrap()` sets
`source_as_of = _text(getattr(snapshot, "source_as_of", ""))`, the same
value `generate_rankings()`'s output rows all share, since one admission
covers the whole snapshot) that was already displayed on the Data Health
page but not on any of these five other surfaces. No backend file was
touched; no new provenance was invented; per-player `sourceAsOf` plumbing
into `WaiverAddCandidate`/`TradePlayerImpact` (which genuinely IS dropped
at `sleeper_free_agent_pool`/`rank_waiver_candidates`, confirmed by
reading those functions) was considered and explicitly NOT done this pass
-- the single shared admission date already answers the "what basis is
this" question without a bigger contract change; flagged below if a
future worker wants true per-player granularity (e.g. after a future
snapshot migration mid-season with mixed dates).

### TESTS ADDED (all ACTUAL TEST RESULT, passing)

- `weekly-shared.test.ts`: 2 new cases for `resolveSeasonProjectionBasisCaption`
  (real date named; honest degrade with no fabricated date for `null`/
  `undefined`/`""`), 5 new cases for `resolveHomeActionFreshness`
  (weekly-sourced categories keep the weekly note; WAIVER/TRADE route to
  the season caption; WAIVER/TRADE fall back to the weekly note only when
  the season date is itself unavailable).
- `cheat-sheet.test.ts`: 2 new cases for `nwrSeasonStatusText` (real date;
  honest degrade).

### Regression scope check (ACTUAL TEST RESULT)

`cd desktop && npx vitest run`: **451 passed, 0 failed** (29 test files;
443 baseline + 8 new). `npm run typecheck` (`tsc -b apps/dynasty/tsconfig.json
apps/redraft/tsconfig.json`): clean, 0 errors. The same incidental
`frontend_bench_results.json` vitest-run side effect every prior worker
has hit was reverted via `git checkout --` before committing. No backend
tests were run this pass since zero Python files changed (confirmed via
`git status`).

### Files changed this pass

- `desktop/apps/redraft/src/weekly-shared.tsx` -- added
  `resolveSeasonProjectionBasisCaption`, `resolveHomeActionFreshness`.
- `desktop/apps/redraft/src/weekly-shared.test.ts` -- 7 new tests.
- `desktop/apps/redraft/src/in-season.tsx` -- `WeeklyHomePage` action
  cards wired to `resolveHomeActionFreshness`.
- `desktop/apps/redraft/src/pages.tsx` -- Rankings table and Compare's
  "Rest of Season" mode both wired to the new caption.
- `desktop/apps/redraft/src/cheat-sheet.tsx` -- added `nwrSeasonStatusText`,
  wired into the compact header row.
- `desktop/apps/redraft/src/cheat-sheet.test.ts` -- 2 new tests.
- `desktop/apps/redraft/src/improve-team.tsx` -- Targets and FAAB tabs
  both gained a `seasonSourceAsOf` prop and the new caption.
- `desktop/apps/redraft/src/trades.tsx` -- Analyze tab and Find Trades tab
  both gained the new caption (Analyze via a new `seasonSourceAsOf` prop).

### Hard boundary check

Did not touch `marginal_roster_utility_v2`, its weights, the governed
valuation model, draft recommendation logic, roster legality,
`LeagueSnapshot`/`LeagueWorkspaceContext`/lifecycle-resolver/
`DecisionResultEnvelope`/`PlayerAvailabilityStatus` semantics -- all of
those were only read (to confirm what they already carry), never
restructured. Did not re-open or touch Harrison's already-settled
arithmetic finding. Did not replace or invent any projection data -- every
caption reads an already-computed field (`data.status.sourceAsOf`) that
was already displayed elsewhere in the app (the Data Health page). Zero
backend/Python files changed.

### Open issues for next worker

1. **Per-player season `sourceAsOf` is still not threaded into
   `WaiverAddCandidate`/`TradePlayerImpact`** -- confirmed by reading
   `sleeper_free_agent_pool` (`fantasypros_kdst_consensus_service.py`) and
   `rank_waiver_candidates` (`waiver_engine_service.py`): both read a
   `ranking` row that DOES carry `sourceAsOf` but neither copies it
   through to the candidate/payload. Not fixed this pass because the
   single shared bootstrap-level `data.status.sourceAsOf` already answers
   the practical question (one snapshot, one admission date, covers every
   row) -- worth revisiting only if a future snapshot ever mixes rows from
   different admission dates.
2. **DecisionResultEnvelope.generatedAtUtc** (already backend-carried on
   `TradeAnalysisResult`/`TradeFinderResult`/`TradePackageSearchResult`,
   confirmed present in the contract) is still unused by the frontend --
   it records when the DECISION was computed, not the projection's own
   basis, so it's a different (also real, also currently invisible) kind
   of freshness signal from what this pass surfaced. Considered, not
   wired this pass to keep the diff focused on the projection-basis
   question the dispatch actually asked about.
3. Section 3D (completing small broken/incomplete interactions found
   during the Workers 1-3 walkthrough) and the Section 2 tool-by-tool
   walkthrough coverage inventory (routes/tools not yet covered) are next,
   per the dispatch -- neither started this pass.
4. Everything still open from Workers 1-3's own ledger sections (Draft
   Room not exhaustively audited, Attention Center residual cross-surface
   risk, Players/Market tab not line-by-line audited, Trades AnalyzeTab's
   stale-form-until-resubmit UX note, the pre-existing K/DST practical-mode
   freshness-window test failures, native Tauri packaging) remains open
   and unchanged by this pass.

---

## Worker 5 — Section 3D closure + Redraft walkthrough coverage begins (2026-09-16)

**Branch/worktree:** same as Workers 1-4,
`upgrade/nwr-prospective-outcomes-v1-20260914` at
`C:\NWR\prospective-outcomes-v1`. Started at HEAD `fa955d81` (Worker 4's
commit; clean). Did not push, did not touch `main`, did not force anything.
Frontend (127.0.0.1:1422, real `vite preview` static build) and backend
(127.0.0.1:18742) were NOT restarted -- confirmed still up throughout (LIVE
OBSERVATION: real 200s from `/api/v1/redraft/*` inside an authenticated
browser session, see below).

### IMPORTANT correction to prior workers' assumption: the running
### frontend/backend serve OLD code, confirmed LIVE, not just inferred

Workers 1-4 each correctly reasoned (INFERENCE) that their own pass's
changes would not be live without a restart. This pass got a real
authenticated Chrome session against the actual running app (Workers 1/3
could not) and confirms it directly: the header badge / Data Health page's
"7 rookies remain blocked" text (LIVE OBSERVATION, screenshot-verified)
still reads the single OLD blanket phrase ("...conflict with the current
factual registry; no values were imputed") for all 7 names, NOT Worker 1's
corrected per-reason breakdown from `_blocked_seed_reason_breakdown`. This
means the running frontend build (a static `vite preview` bundle, not a
hot-reloading dev server) and backend process both predate Worker 1's very
first commit this cycle -- EVERY frontend/backend change from Workers 1-5
(including this pass's own Part A/B work) is invisible in the live app
until a real restart. This closes Worker 1's open item #3
("confirm ... once the backend is next restarted") with a definitive
"still not live, confirmed by direct observation" rather than leaving it an
open question.

### PART A.1 -- Attention Center residual cross-surface risk (Worker 3's
### open item #2): REAL, REACHABLE race -- FIXED

INSPECTED CODE: grepped every `.activateRedraftProfile(` call site in
`desktop/apps/redraft/src/`. Found SIX total: two internal to
`attention-center.ts`'s own sweep (`fetchLeagueAttention`'s activate, and
the `finally`-block restore), already serialized against each other via the
existing `attentionCenterQueue`; and FOUR entirely independent external
call sites that had ZERO awareness of that queue --
`RedraftApp.tsx`'s `LeagueScopedPage` (the deep-link/bookmark/route
activation gate every `/league/:leagueKey/*` route passes through),
`shell-identity.tsx`'s `ShellIdentity.switchLeague` (the header
quick-switcher), `leagues.tsx`'s `LeaguesPage.activate` (Manage Leagues),
and `profile.tsx`'s `ProfilePage.activate` (the Profile page's own league
switcher). Each of those four has its own LOCAL guard against a second
call from ITSELF (`inFlightFor`/`switchRequestRef`/`activationInFlight`),
but none of them guarded against a concurrent call from Attention Center's
background sweep (or from each other) hitting the SAME backend single
active-profile pointer at the same time. Confirmed (INSPECTED CODE,
backend) no server-side lock exists either --
`src/application/desktop_facade.py`'s `activate_redraft_profile` /
`active_profile_id` has no per-request mutex. **Verdict: real, live race,
reachable any time Attention Center's sweep is mid-flight and the owner
follows ANY direct link/header-switch/Manage-Leagues click/Profile-page
switch to a different league** -- not merely theoretical.

**Fix**: generalized the existing sweep-only `attentionCenterQueue` into an
exported `serializeActiveProfileCall<T>(run: () => Promise<T>): Promise<T>`
in `attention-center.ts` (same swallow-failures-so-one-rejection-never-jams
-the-queue design as before). `runAttentionCenterAggregation` now routes
through it as before (unchanged behavior for sweep-vs-sweep). All 4
external call sites (`RedraftApp.tsx`, `shell-identity.tsx`, `leagues.tsx`,
`profile.tsx`) now wrap their own `client.activateRedraftProfile(...)` call
in the same `serializeActiveProfileCall`, so no two calls from ANY
combination of these 5 real surfaces can ever interleave against the shared
backend pointer again. Each site's own pre-existing local guard
(`inFlightFor`/`switchRequestRef`/etc.) is unchanged and still decides
whether ITS caller-side response is still wanted once its turn comes up --
this queue only decides ORDERING against the shared backend pointer.
`profile.tsx`'s `create`/`duplicate` actions (which also implicitly
activate a profile server-side, per their own success messages) were
deliberately NOT wrapped this pass -- lower-frequency, one-shot form
actions, not the "in-app navigation" class the dispatch specifically named;
flagged below as a residual, smaller-risk gap.

**Test**: new regression test in `attention-center.test.ts`
("never interleaves a sweep with an UNRELATED direct
activateRedraftProfile call routed through the same shared queue") --
fires a real 3-league sweep and an unrelated `serializeActiveProfileCall`
navigation call concurrently against a fake client with call-order
tracking; asserts the sweep's own activate/restore sequence stays fully
contiguous and the navigation's call is queued strictly after it, landing
the backend pointer on the navigated-to league rather than being clobbered
by the sweep's later restore.

### PART A.2 -- Trades Analyze stale-result gap (Worker 3's open item #4):
### FIXED

Confirmed (INSPECTED CODE) Worker 3's characterization: `AnalyzeTab` is a
single explicit "Analyze trade" button (disabled while `working`), safe
from the FAAB-class auto-refetch race, but the result panel never marked
itself stale when `gives`/`receives` were edited after a result was shown
and before re-clicking Analyze. Fixed with a new pure function
`isTradeAnalysisStale(analyzedGiveIds, analyzedReceiveIds, currentGiveIds,
currentReceiveIds)` in `trades-explain.ts` -- order-independent set
comparison (re-picking the same two players in a different order is not a
real trade change). `TradeAnalysisResult.gives`/`.receives` carry NWR's own
canonical player ids, not the raw Sleeper ids the picker tracks (the same
id-space gap already documented in this file for Find Trades' deliberately
-omitted "Open in Analyze" jump), so staleness compares against a snapshot
of the exact Sleeper ids submitted at analyze-time
(`analyzedGiveIds`/`analyzedReceiveIds`, new state in `TradesPage`, updated
only on a SUCCESSFUL analysis) rather than against the response's own
echoed ids. Wired into `AnalyzeTab` as an "Updating…"-style
`alert-strip alert-strip--pending` banner ("This trade has changed...
Analyze trade again to refresh it."), same convention Worker 3 established
for Find Trades' mode-staleness banner.

**Tests**: 7 new cases in `trades-explain.test.ts` for
`isTradeAnalysisStale` (never-stale-before-first-analysis, exact match,
order-independence, added give, removed receive, swapped player, clears
after re-analyzing).

### PART A.3 -- K/DST practical-mode test triage: FIXTURE STALENESS,
### FIXED (not a product bug)

TRIAGED (INSPECTED CODE + ACTUAL TEST RESULT), not merely re-flagged.
Reproduced the 3 failures Worker 1 found
(`test_redraft_profile_practical_mode_toggle.py`): all fail inside
`_install_fresh_test_snapshot`, which installs the real bundled
`GOVERNED_COMBINED_608_PROJECTION_SNAPSHOT.csv` (from the
`nwr_redraft_2026_rookie_projection_candidate_v1_20260809` dir) under a
receipt with `valid_until=2099-01-01`. Read the CSV directly: its own
`source_as_of=2026-08-08` (ACTUAL). `install_projection_snapshot`'s
`_source_as_of_reason` (`redraft_engine_v1_service.py`) enforces a SEPARATE
30-day freshness gate computed against real wall-clock
`datetime.now(UTC).date()` -- confirmed correct, no off-by-one/timezone bug
(INSPECTED CODE) -- independent of the receipt's own `valid_until`. As of
today (2026-09-16), 2026-08-08 is 39 days old, so every one of these 3
tests now fails purely on calendar drift, unrelated to anything any worker
changed. **Verdict: fixture staleness, not a product bug, not a design
flaw** -- the 30-day gate is the real, intentional "no stale projections
without an explicit draft-day authorization" governance rule working
exactly as designed. Found the EXACT same problem already solved for a
sibling test file: `test_redraft_engine_v1_service.py`'s
`_fresh_projection_rows()` (search that file for "environmental
source_as_of date-cliff") rewrites `source_as_of` to `today - 1 day` at
test-run time instead of hardcoding a real date.

**Fix**: applied the identical, already-repo-blessed pattern to
`_install_fresh_test_snapshot`: read the real bundled CSV's 608 rows,
rewrite every row's `source_as_of` to `datetime.now(UTC).date() -
timedelta(days=1)`, write the rewritten CSV to a temp file under
`tmp_path`, and bind the receipt's `source_sha256` to THAT rewritten file's
real hash (a receipt's hash must match the exact bytes installed --
confirmed by reading `_validate_approval_receipt`) instead of the original
bundled file's now-irrelevant hash. Never touches the real committed CSV or
its real receipt -- only this test's own hermetic tmp_path copy. All 5
tests in the file now pass (`python -m pytest
tests/test_redraft_profile_practical_mode_toggle.py -q` -> `5 passed`),
and this fixture is now durably immune to the same calendar-drift failure
recurring every ~30 days.

**Regression check**: `tests/test_redraft_engine_v1_service.py` has its own
3 pre-existing failures + 13 errors, confirmed via `git stash` to be
BYTE-IDENTICAL before/after this pass's changes (unrelated to this fix,
not investigated further -- out of this pass's scope, flagged below).
`tests/test_redraft_page_v1.py`, `test_desktop_facade_architecture_wiring.py`,
`test_desktop_http_api.py`: 50 passed, 0 failed.
`test_desktop_application_api.py`: 4 failed / 46 passed, confirmed
BYTE-IDENTICAL to Worker 2's own documented baseline for this worktree (not
the separate Draft Upgrade HQ 5-failure baseline from memory -- a
different worktree).

### PART B -- Redraft tool-by-tool walkthrough (route inventory + coverage
### begun)

**Route inventory** (INSPECTED CODE, grepped `RedraftApp.tsx`'s
`<Route>` list in full): real distinct Redraft pages behind
`/league/:leagueKey/*` are WeeklyHomePage(home), LineupPage(lineup),
ImproveTeamPage(waivers/improve), LeagueWorkspacePage(my-roster/league/
opponent-rosters, tabs Overview/My Roster/Teams/Scoring/Settings/Sync),
TradesPage(trade-analysis/trades/trade-finder, tabs Analyze/Find),
FreeAgentsPage(free-agents), DraftRoomV2Page(draft), PlayersPage(rankings/
players/tiers/compare/adp, tabs Rankings/Tiers/Compare/Market),
CheatSheetPage(cheat-sheet), ProfilePage(profile, also non-league-scoped),
WeeklyToolsPage(weekly-tools), DataHealthPage(data-health),
DecisionHistoryPage(decision-history); plus non-league-scoped
LeaguesPage(/leagues, Manage Leagues) and AttentionCenterPage
(/attention-center).

Got a REAL authenticated Chrome session against the running app (something
Workers 1/3 explicitly could not do) -- active league is the real,
already-imported, read-only Fantasy Gamers Sleeper league (10-team PPR
1QB, PRE_DRAFT lifecycle). All findings below marked LIVE OBSERVATION were
a real browser session against the real running backend (confirmed via
`read_network_requests` showing real 200s from `/api/v1/redraft/*`), not
inference. No draft/roster/lineup writes were attempted against this or
any real league; no state-mutating buttons (ADP refresh/import, Ballers
import, K/DST ECR refresh, profile edits) were clicked.

- **League page** -- PASS. All 6 tabs (Overview, My Roster, Teams,
  Scoring, Settings, Sync) verified LIVE with real, data-backed content:
  My Roster shows the real 15-player roster with real lineup slots
  (STARTER/Bench) and real NWR identity match status (K/DST correctly
  UNMATCHED, matches the K/DST-always-manual finding from Worker 1);
  Teams shows all 9 real opponent rosters; Scoring shows the real PPR
  scoring config; Settings loads the real `ProfileEditor` form; Sync shows
  real `LIVE`/`CURRENT` Sleeper sync status with a real last-synced
  timestamp. Tab consistency confirmed (same header/tab-bar shape across
  all 6).
- **Data Health page** -- PASS. Renders correctly with real backend
  authority cards (League sync, Rest-of-season projections, Weekly
  projections, Market/ADP, Player status, Decision engine, League
  Workspace snapshot), a real readiness banner ("Ready · 7 blocked players
  visible"), real readiness checks (Player universe/Current forecast/
  Scoring profile/Replacement model all real statuses), and a real notices
  list. All 3 of Worker 1's data issues (Market ADP unavailable, Sleeper
  scoring needs review, 7 rookies blocked) each have a working detail path
  (the header badge popup and this page's own notices both show real
  per-issue detail text) -- confirmed the corrected per-reason breakdown
  text is NOT yet visible live (see the "running old code" finding above,
  not a new bug). Market ADP's real recovery path (the Market/ADP control
  center under Players > Market) was confirmed to actually exist and
  render, not just referenced in text (see next item) -- Data Health
  itself has no separate "fix it now" button on the card, which is
  existing, unchanged behavior, not a Worker-5-introduced regression.
- **Draft Room** -- PASS for the scoped "basic functionality only" check.
  Loads correctly and shows the correct PRE_DRAFT lifecycle state for this
  real non-drafting league ("CHOOSE YOUR DRAFT SLOT BELOW TO BEGIN", full
  564-player board rendered, Suggestions/Cheat Sheets/Draft Board/Rankings/
  Teams/Queue tabs all present). No draft actions were attempted (directive
  boundary). One real, LIVE-OBSERVED finding NOT fixed this pass (in scope
  conflicts with the hard boundary on draft-recommendation logic): the
  page's own DecisionBundle fetch (`POST .../decision-bundle` and
  `.../decision-bundle-v2`) both return real HTTP 500s in this pre-draft,
  no-slot-selected state -- but the UI degrades GRACEFULLY ("DecisionBundle
  unavailable -- The DecisionBundle request failed -- backend calculation
  unavailable.", no crash, no console exception), which is itself correct
  empty/error-state handling per the directive's "check loading/error/empty
  states" ask. Root cause not investigated (would require touching
  DecisionBundle computation, inside the hard boundary) -- flagged for the
  next worker as a real, reproducible 500 worth a closer look, though it
  may simply be expected given no draft slot/pick context exists yet.
- **Players' Market/ADP tab** -- PASS. Full ADP control center renders:
  "Active ADP source" card correctly shows "No active ADP snapshot" /
  `UNAVAILABLE`, consistent with Data Health's own Market ADP finding
  (this IS that issue's real, working recovery path, confirmed reachable
  from this tab); "Import Multi-Platform ADP" (CSV/paste importer, source
  label, parser modes, Preview/Save/Export buttons), "League Platform
  Selection" (Auto-detected Sleeper, override dropdown, Activate button),
  and "Ballers / UDK" import section (correctly shows "No Ballers cheat
  sheet imported yet.") all rendered with real state. Not clicked (would
  mutate the real Fantasy Gamers profile's stored ADP/Ballers config).
- **Search/filter behavior (Rankings tab)** -- PASS. Live-tested: text
  search ("mccaffrey") correctly case-insensitively substring-matches
  across the full 564-row board (found both Christian McCaffrey #1 and
  Luke McCaffrey #275, correctly showing "SHOWING 2 OF 2 MATCHES"
  regardless of the separate Board Depth filter); position filter (DST)
  correctly returns a real, honest empty state ("SHOWING 0 OF 0 MATCHES" /
  "No rows match this view.") rather than a blank/broken table, consistent
  with K/DST being permanently outside NWR's ranked universe by design;
  Reset control restores defaults.
- **Free Agents page** (not explicitly named in the directive's list, but
  not yet mentioned by any prior worker) -- PASS, spot-checked. Real live
  Sleeper read-only data: 721 real unrostered players, correct NWR
  rank/season-points/replacement-value for ranked players and an honest
  "Unranked" fallback (not a fabricated 0) for out-of-universe players
  (K/DST, practice-squad-caliber players, etc.).
- **Weekly Tools page** (K/DST ECR streamer; not explicitly named, not
  yet mentioned by any prior worker) -- PASS, spot-checked (render only,
  no refresh clicked to avoid a real external FantasyPros API call).
  Renders correctly: "PROVIDER CONFIGURED", real FantasyPros-key-configured
  messaging, NFL Week input, Horizon selector (This Week/Next 2/Next 3),
  Refresh button.

### Hard boundary check

Did not touch `marginal_roster_utility_v2`, its weights, the governed
valuation model, draft recommendation logic, roster legality,
`LeagueSnapshot`/`LeagueWorkspaceContext`/lifecycle-resolver/
`DecisionResultEnvelope`/`PlayerAvailabilityStatus` semantics. No real
Sleeper/ESPN writes; no draft/roster/lineup actions attempted against any
real league (the live browser walkthrough was read-only navigation plus
one text-search and one position-filter interaction, both client-side/
read-only). The one Python file changed (`test_redraft_profile_practical_mode_toggle.py`)
is test-only.

### Files changed this pass

- `desktop/apps/redraft/src/attention-center.ts` -- generalized
  `attentionCenterQueue` into exported `serializeActiveProfileCall`.
- `desktop/apps/redraft/src/attention-center.test.ts` -- 1 new
  sweep-vs-unrelated-call regression test.
- `desktop/apps/redraft/src/RedraftApp.tsx`,
  `desktop/apps/redraft/src/shell-identity.tsx`,
  `desktop/apps/redraft/src/leagues.tsx`,
  `desktop/apps/redraft/src/profile.tsx` -- each wraps its own
  `activateRedraftProfile` call in `serializeActiveProfileCall`.
- `desktop/apps/redraft/src/trades-explain.ts` -- added
  `isTradeAnalysisStale`.
- `desktop/apps/redraft/src/trades-explain.test.ts` -- 7 new tests.
- `desktop/apps/redraft/src/trades.tsx` -- `TradesPage`/`AnalyzeTab` track
  `analyzedGiveIds`/`analyzedReceiveIds` and render a stale banner.
- `tests/test_redraft_profile_practical_mode_toggle.py` -- rewrote
  `_install_fresh_test_snapshot` to use a dynamically-fresh, hermetic CSV
  fixture instead of the real bundled file's fixed, now-stale date.

### TESTS ADDED (all ACTUAL TEST RESULT, passing)

- `attention-center.test.ts`: 1 new case (sweep-vs-unrelated-call
  no-interleave). Full file: 29 passed.
- `trades-explain.test.ts`: 7 new cases for `isTradeAnalysisStale`. Full
  file: 45 passed.
- `tests/test_redraft_profile_practical_mode_toggle.py`: all 5 tests now
  pass (3 previously-failing + 2 already-passing).

### FULL FRONTEND/BACKEND TEST SUITE RESULTS

`cd desktop && npx vitest run`: **459 passed, 0 failed** (29 test files;
451 baseline + 8 new). `npm run typecheck`: clean, 0 errors. The
incidental `frontend_bench_results.json` vitest side effect (same as every
prior worker) was reverted via `git checkout --` before committing.
Backend: `test_redraft_profile_practical_mode_toggle.py` 5/5 passed;
`test_redraft_page_v1.py` + `test_desktop_facade_architecture_wiring.py` +
`test_desktop_http_api.py` 50/50 passed; `test_desktop_application_api.py`
4 failed / 46 passed (confirmed BYTE-IDENTICAL pre-existing baseline via
`git stash`); `test_redraft_engine_v1_service.py` 3 failed + 13 errors / 77
passed (confirmed BYTE-IDENTICAL pre-existing via `git stash`, unrelated to
this pass, not investigated further -- likely more of the same
`source_as_of` calendar-drift class this pass just fixed in a sibling
file, flagged below as a good next target). Did not run the full `tests/`
suite (the documented ~323-pre-existing-failure baseline from memory is
for a reason unrelated to this pass's changes).

### RUNNING PROCESSES STATUS

Frontend (127.0.0.1:1422) and backend (127.0.0.1:18742) were NOT
restarted -- confirmed still up via a real authenticated browser session
(LIVE OBSERVATION, not just an HTTP-200 probe: real navigation across 7
pages, real data rendered from real backend responses). See the "running
old code" finding above: this pass's own changes (and Workers 1-4's) are
NOT yet live in this process pair and will not be until a real restart.

### Open issues for next worker

1. **`test_redraft_engine_v1_service.py`'s 3 failures + 13 errors** are
   pre-existing and unrelated to this pass (confirmed via `git stash`),
   but at least one (`test_review_only_stale_and_shallow_projection_evidence_fail_closed`)
   looks like it could be more `source_as_of`-calendar-drift fallout --
   worth triaging with the same method this pass used, rather than
   re-flagging again undocumented.
2. **Draft Room's DecisionBundle 500s** (both v1 and v2 endpoints) in this
   real pre-draft, no-slot-selected league -- gracefully handled by the UI
   ("DecisionBundle unavailable"), not reproduced as a crash, root cause
   NOT investigated (would touch draft-recommendation-adjacent code, inside
   this pass's hard boundary). Worth a closer look by a worker scoped to
   touch that code: is this expected (no pick context yet) or a real
   backend regression?
3. **`profile.tsx`'s `create`/`duplicate` profile actions** still call
   `client.createRedraftProfile`/`client.duplicateRedraftProfile` directly,
   NOT routed through `serializeActiveProfileCall`, even though their own
   success messages ("Profile created and activated.") confirm they also
   mutate the shared active-profile pointer server-side. Deliberately not
   wrapped this pass (lower-frequency, one-shot form actions, not the
   "in-app navigation" class Worker 3's item specifically named) -- a
   smaller residual version of the same risk class, worth closing if a
   future worker wants full coverage.
4. **Confirmed, not just inferred: the running frontend/backend serve code
   from before Worker 1's first commit this cycle.** Every Python/TS change
   from Workers 1-5 (including this pass's own Part A fixes) needs a real
   restart before it is observable live. The next restart will also make
   Worker 2's Sleeper player-catalog cache live for the first time -- note
   that explicitly if/when it happens (per the dispatch's own standing
   instruction).
5. **Section 2 Redraft walkthrough remaining coverage**: this pass covered
   League page, Data Health page, Draft Room (basic), Players Market/ADP
   tab + search/filter, plus spot-checks of Free Agents and Weekly Tools.
   Still NOT walked through by any worker: Decision History's OwnerActionCell
   recording flow end-to-end (only reviewed for the stale-response bug
   class, not a full functional walkthrough), Improve Team's Targets/
   Drop-Candidates/FAAB tabs as a full functional walkthrough (only
   reviewed for staleness/labeling), Start/Sit's swap mechanics, Cheat
   Sheet's export/print paths, and Manage Leagues' create/import/archive
   flows beyond the activate race just fixed. Dynasty app coverage has not
   been started at all this cycle -- per the dispatch, next worker should
   pick one: finish remaining Redraft walkthrough items above, or pivot to
   starting Dynasty.
