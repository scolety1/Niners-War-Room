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
