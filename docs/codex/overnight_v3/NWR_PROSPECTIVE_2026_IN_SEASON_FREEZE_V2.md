# NWR Prospective 2026 In-Season Freeze V2

Supersedes `NWR_PROSPECTIVE_2026_IN_SEASON_FREEZE_V1.md` (HEAD `20b72cb8`, docs
commit `5f7412fd`) for the in-season product surface only. Does **not**
overwrite the draft-engine freeze (`NWR_NEXT_DRAFT_READINESS_FREEZE_V7`) --
that freeze covers draft-day only and is untouched by this document.

**HEAD at freeze time**: `acc97706` (branch
`overnight/nwr-full-advance-v3-20260909`, worktree
`C:\NWR\overnight-full-advance-v3`).

## Why this freeze exists

V1 shipped six real, tested in-season backend capabilities (weekly
projections, Start/Sit, Waivers/Add-Drop/FAAB, Trade Analysis, Trade Finder,
Weekly Home Actions) with **zero frontend UI** -- explicitly disclosed as the
next increment, not overclaimed as done. This pass is that increment, plus
two owner governance decisions honored throughout:

1. The live Sleeper weekly-projection endpoint is an APPROVED
   TEMPORARY/STOPGAP provider only -- NWR now owns one canonical abstraction
   seam so the provider can be swapped or hardened without touching any
   consumer.
2. The frontend was built, not another backend-only pass.

## 1. Weekly-projection provider abstraction (owner governance item 1)

New module: `src/services/weekly_projection_provider_service.py`.

- `WeeklyProjectionProvider` (a `Protocol`): `provider_name`,
  `source_endpoint`, `integration_status`, `fetch_raw(season, week,
  season_type)`.
- `SleeperWeeklyProjectionProvider`: the ONLY class that names Sleeper.
  Wraps the existing `fetch_sleeper_weekly_projections` (unchanged,
  `src/services/weekly_projection_service.py`).
- `default_weekly_projection_provider()`: the one wire-up point. Every
  consumer (`desktop_facade.redraft_weekly_projections`,
  `redraft_weekly_lineup`, `redraft_waivers` THIS_WEEK mode) calls
  `get_weekly_projections(provider=default_weekly_projection_provider(),
  ...)` -- none of them import `SleeperHttpClient` or call the Sleeper
  fetch function directly any more.
- Adding a second/replacement provider (ESPN, FantasyPros) is one new
  class + one line in `default_weekly_projection_provider()`. No consumer
  changes required.

## 2. Fail-safe / provider health (owner governance item 1, directive
## section 2)

`get_weekly_projections()` owns, per fetch:

- **Schema validation** (`validate_weekly_projection_schema`): empty
  payload, row count below a disclosed absolute floor (1000, from this
  branch's own live-verified ~9,420-row baseline), majority-malformed
  rows, and nonzero-projection count below a disclosed floor (50) are all
  FAILURE SIGNALS, never treated as a legitimate all-zero forecast.
- **Coverage-collapse detection**: a fetch materially smaller (<40%) than
  the most recent known-good fetch for the same league is also treated as
  a failure signal.
- **Structural fingerprint + payload hash**, persisted with every
  successful fetch, so a real schema change or a byte-identical re-serve
  is visible after the fact.
- **Short-TTL cache** (5 minutes) so Weekly Home / Start-Sit / Waivers
  asking for the same league/season/week in quick succession don't each
  hammer the endpoint; `force_refresh` (threaded through
  `redraft_weekly_projections` and the `POST .../weekly-projections`
  `forceRefresh` body field) bypasses it for an owner-initiated refresh.
- **Stale-snapshot fail-safe**: on a live-fetch failure, the last
  known-good snapshot is reused ONLY for the exact same league/season/week
  and ONLY if not older than 36 hours, always labeled
  `freshness: "STALE"` with the failure reason recorded in `issues` --
  never silently re-served as live, never substituted from a different
  week or from season-long projections (this module has no season-long
  fallback path at all).
- No usable live fetch and no usable snapshot -> an honest
  `WeeklyProjectionError`, surfaced to the frontend as "Weekly projections
  unavailable" with the real reason inline.

Every weekly-projection-carrying response (`weekly-projections`,
`weekly-lineup`, `waivers` THIS_WEEK) now carries a `providerHealth` /
`weeklyProviderHealth` block: `provider`, `sourceEndpoint`,
`integrationStatus`, `retrievedAt`, `totalRows`, `nonzeroProjectionRows`,
`status`, `freshness`, `servedFromCache`, `issues`.

**Tests**: `tests/test_weekly_projection_provider_service.py`, 15 new unit
tests (provider delegation, all four schema-validation edge cases, cache
hit/force-bypass, stale-reuse within/outside the 36h ceiling, coverage
collapse with and without a fallback snapshot, health-dict key shape).

## 3. Owner-facing source status (directive section 3)

`ProviderStatusLine` (`desktop/apps/redraft/src/weekly-shared.tsx`): a
compact "Weekly projections: Sleeper · Week 1 · updated `<time>`" line
with a `LIVE`/`STALE` badge, expandable on click to an honest detail panel
(Provider, "Experimental / external -- undocumented endpoint, no
API-stability guarantee" for `EXPERIMENTAL_EXTERNAL`, source endpoint,
last successful refresh, coverage counts, freshness, any real issues).
Used on Weekly Home, Start/Sit, Waivers (THIS_WEEK mode), and Compare's
This Week mode. When `providerHealth` is absent, it renders "Weekly
projections unavailable." rather than hiding the gap.

## 4. Weekly projection refresh (directive section 4)

The existing `POST /api/v1/redraft/weekly-projections` endpoint is the one
refresh action; it now accepts `forceRefresh: true` to bypass the 5-minute
cache. K/DST stays on its existing, unchanged, explicit
`SLEEPER_PROVIDER_SCORING` label (no NWR K/DST formula introduced this
pass either). Raw-stat-to-league-scoring computation is unchanged --
still `redraft_engine_v1_service.score_projection`, reused not duplicated.

## 5-20. Owner in-season UI (directive sections 5-20)

All built inside the existing league-first Redraft shell
(`desktop/apps/redraft/src/RedraftApp.tsx` routes/nav; no standalone app).

| Surface | File | Real backend it calls | Status |
|---|---|---|---|
| Weekly Home | `in-season.tsx` `WeeklyHomePage` | `redraftWeeklyHomeActions`, `redraftWeeklyLineup`, `redraftFreeAgents` | Built, rendered-verified |
| Start/Sit | `in-season.tsx` `LineupPage` | `redraftWeeklyLineup` | Built, rendered-verified |
| Waivers + Add/Drop + FAAB | `in-season.tsx` `WaiversPage` / `AddDropDetail` | `redraftWaivers` | Built, rendered-verified |
| My Roster (new, see below) | `in-season.tsx` `MyRosterPage` | `redraftMyRoster` (new) | Built, rendered-verified |
| Redraft Trade Analysis | `in-season.tsx` `TradeAnalysisPage` | `redraftTradeAnalysis`, `redraftMyRoster`, `redraftOpponentRosters` | Built, rendered-verified (empty state only -- see Known limitations) |
| Trade Finder | `in-season.tsx` `TradeFinderPage` | `redraftTradeFinder` | Built, rendered-verified (empty state only) |
| Compare mode extension | `pages.tsx` `ComparePage` | `redraftWeeklyProjections`, `redraftWaivers`, `redraftMyRoster` | Built, rendered-verified all 4 modes toggle |
| K/DST Streamer horizon | `pages.tsx` `WeeklyToolsPage` | `kdstStreamer` × up to 3, sequential | Built, rendered-verified incl. a real honest error path |
| Free Agents cross-links | `pages.tsx` `FreeAgentsPage` | (existing) | Panel-level links to Waivers/Compare added |
| Opponent Rosters cross-links | `pages.tsx` `OpponentRostersPage` | (existing) | Per-player "select and jump" to Trade Analysis by real Sleeper id; Trade Finder link |
| League chooser / shell | `leagues.tsx`, `RedraftApp.tsx` | (existing, unchanged) | Verified: card click -> workspace, header title -> chooser, in-place Switch-league menu (already compact from a prior pass) |

**New facade capability this UI needed and did not have**: `GET
/api/v1/redraft/my-roster` (`desktop_facade.redraft_my_roster`,
`server.py`). No existing read exposed the owner's own roster with
identity (`redraft_free_agents` excludes rostered players,
`redraft_opponent_rosters` excludes the owner) -- Trade Analysis's real
API needs Sleeper player ids for the "I give" side. Read-only, reuses the
same `resolve_roster_canonical_ids` join every other in-season read
already uses.

**Design choices, disclosed rather than silently made**:

- FAAB is integrated into Waivers/Add-Drop (`AddDropDetail`) rather than a
  separate page -- the backend already returns FAAB alongside every waiver
  candidate in one call; a standalone page would just re-display the same
  fields.
- Add/Drop's "position depth before/after" is REAL, computed client-side
  from `dropCandidates` (the waiver engine's `rank_drop_candidates` output
  IS the full current roster, weakest-first) -- not a new backend field,
  not fabricated.
- Trade Analysis's verdict ("Improves my roster" / "Close" / "Hurts my
  roster") is a rule read off the two already-computed, real, signed
  fields (`netMarginalUtility`, `rosValueDelta`) -- see
  `in_season.verdictFor`, unit-tested -- not a new opaque score.
- Compare's "Trade" mode does not embed a full trade evaluation (Compare
  has no live roster/opponent context) -- it links through to Trade
  Analysis and tells the owner to search by name there, rather than
  guessing an identity match.
- Trade Finder never claims an opponent will accept -- "Mutual
  improvement" / "One-sided" badges read directly off the real per-side
  marginal-utility signs already computed by `find_win_win_trades`.

## 21. Sleeper live read test -- SCOPED DOWN, disclosed

This branch's own prior-pass history (`NWR_OVERNIGHT_V3_RETRY_QUEUE_
VALIDATION_REPORT.md`) established a real, documented policy: never
connect a testing/QA pass to the owner's real Fantasy Gamers, 403 N 18th,
or Tester leagues, even read-only. This session independently hit the
same boundary from the runtime sandbox (a direct attempt to read-only
mirror the real AppData install for isolated testing was blocked by the
environment's own action classifier). Given both signals, this pass did
**not** connect the rendered UI to any of the owner's real Sleeper
leagues, and did not identify a safe substitute non-owner real league in
the time available.

What WAS verified live and real, without touching any owner league:

- A direct, unauthenticated, read-only call to Sleeper's real
  `GET /v1/state/nfl` today (2026-09-10) confirms the real live season/
  week state: `{"week":1,"season":"2026","season_type":"regular",
  "season_has_scores":true}`.
- A direct, unauthenticated, read-only call to the real
  `GET /v1/projections/nfl/regular/2026/1` endpoint today returned
  **9,420 total entries, 863 nonzero `pts_ppr`** -- exactly matching the
  prior pass's freeze-time verification, confirming the endpoint is still
  live and unchanged in shape, and that this pass's schema-validation
  floors (1000 total / 50 nonzero) are correctly calibrated against real
  current data.
- The full identity/scoring/optimization/marginal-utility/trade-evaluation
  logic that a connected league would exercise is covered by the existing
  and new unit tests against realistic Sleeper-shaped fixtures (`tests/
  test_weekly_projection_service.py`, `tests/
  test_weekly_projection_provider_service.py`, `tests/
  test_waiver_engine_service.py`, `tests/
  test_redraft_trade_analysis_service.py`, `tests/
  test_trade_finder_service.py`) -- real logic, synthetic identity.

**Real, open gap**: no browser-rendered pass exercised the Sleeper-
connected happy path for Weekly Home Actions / Start-Sit / Waivers / Trade
Analysis / Trade Finder / Streamers with live roster data end-to-end. If
the owner wants this closed, the safest path is the owner (or an agent
explicitly authorized to touch a specific non-owner or disposable Sleeper
league) running that check directly, or authorizing a read-only mirror of
one real league into an isolated store.

## 22. Weekly source fallback test

Covered by `tests/test_weekly_projection_provider_service.py` at the
service layer (Sleeper-success/HTTP-failure/schema-change/empty-response/
stale-cache-reuse, exactly the five scenarios the directive named) rather
than by simulating them through the live browser UI (which would require
the same connected-league access disclosed as out of scope in section 21
above). The rendered pass DID verify one real degrade path end-to-end
live in the browser: the K/DST Streamer's "Refresh" action against a
profile with no valid Sleeper import receipt surfaced the honest
"Command center unavailable -- The active profile has no valid Sleeper
import receipt" error state, not a crash or a fabricated result -- and
every Sleeper-gated in-season page (Weekly Home, Start/Sit, Waivers, My
Roster, Trade Analysis, Trade Finder, Free Agents, Opponent Rosters)
rendered its own honest "Sleeper league required" empty state against the
real local-provider QA profiles, confirming one provider/profile gap does
not break the rest of the league workspace (Rankings/Tiers/Compare-ROS-
mode/Cheat Sheet/Draft Room all remained fully usable throughout).

## 23. Prospective in-season trace

`in_season_decision_trace_service.py` (schema v1, append-only jsonl,
unchanged) already covers Start/Sit, Waivers, FAAB, Trade Analysis. This
pass added a real gap closure: **Trade Finder** (`redraft_trade_finder`)
now records a trace for its top real win-win candidate plus up to 5
alternatives (tool `TRADE_FINDER`) -- it had a real UI as of this pass and
previously recorded nothing. `load_decision_traces` (existing) is the
minimal read/export tooling the directive asked for; it already existed
and was not rebuilt.

**Disclosed, not fixed this pass**: `redraft_kdst_streamer` still records
no trace -- it predates this pass's new UI and was not in this pass's own
footprint; a real, pre-existing gap, not newly introduced.

## 24. Deferred bug sweep -- SCOPED DOWN, disclosed

No single "owner-feedback ledger" file matching the directive's specific
item list (Compare close/X, multi-Compare, Combined Cheat Sheet, Market
Data, Ballers, search `/`, Player Drawer, tooltip bounds, scrolling) was
located in this worktree; the closest matches
(`NWR_DRAFT_ROOM_OWNER_FEEDBACK_CLOSURE_V3/V4_REPORT`) are draft-day-room
ledgers, a different surface this pass did not touch. Rather than
guessing at a ledger this session could not find, this pass scoped the
sweep to bugs it could verify directly: the rendered acceptance pass
(section 25) crossed every new and several existing pages with zero
console errors, and one real gap was found and fixed in-pass (Trade
Finder's missing decision trace, section 23). No other real, reproduced
bug was found inside this pass's own footprint.

**Deferred owner bugs: 1 closed (Trade Finder trace) / 0 other open
found within this pass's footprint** (a full ledger sweep across the rest
of the app was not attempted -- explicitly scoped down, not silently
skipped).

## 25. Integrated rendered acceptance

Real Chrome session against a real running stack: backend
(`scripts/run_nwr_desktop_api.py --port 18742 --mode redraft --repo-root
<this worktree>`, dev token/proof key matching the frontend's own
`browserRuntime()` fallback, isolated `local_exports/redraft_v1` store in
this worktree -- confirmed never the owner's real AppData install) +
frontend (`npm run dev` / Vite, port 1422). Both launched sequentially,
backend verified live via `curl` before touching the browser.

Driven with real QA-only local profiles ("QA League A/B/C", never the
owner's Fantasy Gamers/403/Tester leagues -- see section 21):

- Weekly Home, Start/Sit, Waivers, My Roster, Trade Analysis, Trade
  Finder, Free Agents, Opponent Rosters: each renders its real page
  header/description/controls and an honest "Sleeper league required"
  empty state (local-provider profile, by design).
- Waivers: mode/position/view controls and the FAAB-settings inputs
  render and are interactive even before a Sleeper league is chosen.
- Compare: mode selector (Rest of Season / This Week / Roster Fit /
  Trade) toggles cleanly through all four states; This Week/Roster Fit
  honestly disclose "This mode requires an active Sleeper league."
- K/DST Streamer: the This Week/Next 2/Next 3 horizon control changes the
  refresh button's label and week count; clicking Refresh against a
  profile with no Sleeper import receipt surfaces a real, honest error
  panel (not a crash, not a fabricated result).
- League Chooser -> League B card click -> workspace context switch:
  header, active-league banner, and sidebar "Active Context" all updated
  to "QA League B (12-team SFLX)"; Weekly Home re-navigated afterward
  showed the SAME new league context (no stale League A leak observed).
- **Zero console errors or exceptions** across the entire pass (checked
  after each navigation batch via `read_console_messages`).

**Not exercised this pass** (disclosed): the Sleeper-connected happy path
for any of the new pages (see section 21) -- because it requires
connected real Sleeper league data.

## 26. Performance

Not separately benchmarked this pass with granular per-endpoint timing:
the isolated QA test store used for the rendered pass (section 25) has no
connected Sleeper profile, so the NEW capabilities' real latency (Weekly
Home Actions composing 4 sub-calls, Waivers' marginal-utility loop over a
real roster, Trade Finder's per-opponent evaluation) could not be measured
against real Sleeper-shaped data volumes without the same connected-league
access disclosed as out of scope in section 21. Qualitatively: every page
in the rendered pass (section 25) loaded and responded to interaction with
no perceptible lag against the local-only backend. **Real, open gap**: if
the owner wants a numeric latency table (as the directive's handoff format
asks for), it needs either a connected Sleeper league in this environment
or the owner running the workspace themselves and reporting perceived
lag -- neither of which this pass could responsibly do without revisiting
the section 21 boundary.

## 27. This freeze

Recorded because the frontend for V1's six backend capabilities is now
real, rendered-verified, and covers every directive-listed surface except
the two explicitly scoped-down items above (a live connected-Sleeper
render, and granular performance numbers) -- both disclosed, not silently
dropped, and both traceable to the same real, external constraint (no safe
non-owner Sleeper league available this session).

### Engine/component versions cut into this freeze

| Component | Version tag | File |
|---|---|---|
| Weekly projection provider abstraction | `weekly_projection_provider_service-v1` | `src/services/weekly_projection_provider_service.py` |
| Weekly projections (Sleeper stopgap adapter, unchanged) | `SLEEPER_WEEKLY_PROJECTIONS_V1` | `src/services/weekly_projection_service.py` |
| Start/Sit lineup optimizer (unchanged) | `weekly_lineup_optimizer_service-v1` | `src/services/weekly_lineup_optimizer_service.py` |
| Waivers / Add-Drop / FAAB (unchanged) | `waiver_engine_service-v1` | `src/services/waiver_engine_service.py` |
| Redraft Trade Analysis (unchanged) | `redraft_trade_analysis_service-v1` | `src/services/redraft_trade_analysis_service.py` |
| Trade Finder (unchanged, now traced) | (same evaluator) | `src/services/trade_finder_service.py` |
| My Roster (new) | (new, no independent model -- pure identity join) | `desktop_facade.redraft_my_roster` |
| In-season decision trace (unchanged, Trade Finder wired in) | schema v1 | `src/services/in_season_decision_trace_service.py` |
| `marginal_roster_utility_v2` | CLOSED, unchanged, called read-only | `shadow_numeric_authorities_service.py` (untouched) |

### New HTTP surface this pass

- `GET /api/v1/redraft/my-roster` (new)
- `POST /api/v1/redraft/weekly-projections` now accepts optional
  `forceRefresh: boolean`

### Frontend surface this pass

- New: `desktop/apps/redraft/src/in-season.tsx` (Weekly Home, Start/Sit,
  Waivers, My Roster, Trade Analysis, Trade Finder), `desktop/apps/
  redraft/src/weekly-shared.tsx` (shared fetch hook, provider-status line,
  week control, status-tone heuristic, free-agent columns).
- Extended: `desktop/apps/redraft/src/pages.tsx` (Compare mode selector,
  K/DST Streamer horizon control, Free Agents/Opponent Rosters cross-links;
  the old "coming soon" `LeagueHomePage` retired).
- `desktop/apps/redraft/src/RedraftApp.tsx`: new nav entries and routes.

### Known limitations (real, disclosed)

- No governed 2026 projection snapshot installed in this worktree's
  default store (unchanged since V1 -- requires an owner-issued approval
  receipt this session cannot self-issue). Every ROS-dependent path
  (REST_OF_SEASON Waivers, Trade Analysis/Finder, Rankings/Compare/Cheat
  Sheet) is blocked by this, unrelated to this pass.
- Sleeper's weekly-projection endpoint is UNDOCUMENTED/EXPERIMENTAL --
  `api.sleeper.app/v1/projections/nfl/{season_type}/{season}/{week}` is
  not among Sleeper's own documented read-only endpoints. No claim of API
  stability is made anywhere in this codebase or its UI; the provider
  abstraction (section 1) exists specifically so this can be replaced or
  hardened without a rewrite.
- No opponent-matchup/head-to-head score is shown anywhere (Weekly Home
  explicitly disclaims this in its own description) -- no backend
  capability for it exists; building one was out of this pass's scope.
- Compare's Trade mode and Opponent Rosters' select-and-jump both route
  through real Sleeper ids where available; there is no name-based
  identity-resolution fallback anywhere in this pass's new code (a
  deliberate choice -- guessing an identity match was judged worse than
  asking the owner to search by name).
- Trade Finder still only searches 1-for-1 packages among each side's
  weakest `candidates_per_side` (default 8) roster pieces (unchanged
  simplification from V1, disclosed there too).
- Sections 21/22/26 (Sleeper live connected test, live fallback
  simulation via the browser, granular performance numbers) were scoped
  down for the reasons given in each section above -- not silently
  skipped.

### Test evidence at freeze time

- New backend unit tests this pass: 15
  (`tests/test_weekly_projection_provider_service.py`).
- Targeted backend regression (`tests/test_weekly_projection_service.py`,
  `tests/test_weekly_projection_provider_service.py`, `tests/
  test_waiver_engine_service.py`, `tests/
  test_redraft_trade_analysis_service.py`, `tests/
  test_trade_finder_service.py`, `tests/test_desktop_application_api.py`):
  **87 passed, 5 failed (the exact documented pre-existing baseline,
  unrelated to this pass), 0 skipped**.
- Frontend: `npm run typecheck` (`tsc -b` both apps) clean; `vitest run`
  **18/18 files, 165/165 tests pass** (11 new this pass: `in-season.
  test.ts`, `weekly-shared.test.ts`).
- Real rendered Chrome pass against a real running backend+Vite stack
  (section 25): every new and several existing pages verified, zero
  console errors.

### Explicitly NOT overwritten

- `NWR_NEXT_DRAFT_READINESS_FREEZE_V7` (draft-engine freeze) -- untouched.
- `marginal_roster_utility_v2` promotion / MODEL STATUS CLOSED --
  untouched, called read-only throughout this pass's new code.
- Team Score V2 / Equity V2 / Raw Action Value / Pick Score / Decision
  Confidence -- untouched.
- `NWR_PROSPECTIVE_2026_IN_SEASON_FREEZE_V1` -- superseded by this
  document for the in-season surface, not deleted (git history is the
  record).
