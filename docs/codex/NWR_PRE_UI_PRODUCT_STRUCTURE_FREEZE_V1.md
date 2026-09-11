# NWR Pre-UI Product Structure Freeze V1

**Verdict: STRUCTURE FREEZE CUT.** Written by the NWR pre-UI
product-architecture hardening program's CLOSURE pass, part 3
(2026-09-10). This is the first cut of this freeze doc -- no prior
version existed to update (`git log` on this branch before this pass
shows no `NWR_PRE_UI_PRODUCT_STRUCTURE_FREEZE` file).

**HEAD frozen at:** `d1754d797ab5d05d9ddb4b62cd968be26d2c3fbc`
(branch `upgrade/nwr-pre-ui-architecture-v1-20260910`, worktree
`C:\NWR\upgrade-pre-ui-architecture-v1`).

This freeze covers the PRODUCT ARCHITECTURE only (routing, context,
snapshot/envelope/status contracts, the player-detail primitive). It does
NOT freeze any decision engine's computation, any data-admission state,
or the historical backtest/Team-Score-V2 research program -- those have
their own, separate, already-frozen/burned states documented elsewhere
(see the operator's own memory ledger: Team Score V1 frozen 2016/2024/2025
burned, `marginal_roster_utility` promotion at commit `c318a10c`/
`11770580`, Freeze V7 at commit `0ae4b039`, etc.). This document is scoped
strictly to what the three prior passes on this branch actually built.

## What is frozen

### LeagueWorkspaceContext contract
Backend `src/services/league_workspace_context_service.py`
(`LeagueWorkspaceContext` dataclass), exposed at
`GET /api/v1/redraft/league-workspace-context`
(`redraft_league_workspace_context`). Fields: `profileId`, `provider`,
`providerLeagueId`, `season`, `lifecycle`, `lifecycleBasis`,
`currentWeek` (always `null` -- disclosed gap, see below),
`scoringProfileHash`, `rosterStateHash`, `leagueSnapshotId`,
`syncStatus`, `syncAsOf`, `issues`. See `LEAGUE_CONTEXT.md`.

### Routing contract
Canonical deep-linkable tree `/league/:leagueKey/<page>` (`leagueKey` =
`LeagueProfile.profileId`), gated by `LeagueScopedPage`. Legacy flat
paths remain mounted as `<Navigate>` compatibility redirects via
`legacyRedirectTarget` (pure, unit-tested). Canonical owner task map
(HOME/DRAFT/LINEUP/IMPROVE TEAM/TRADES/PLAYERS/LEAGUE) documented in
`PRODUCT_ARCHITECTURE.md`. See that doc's "Routing" and "Canonical owner
task map" sections.

### Lifecycle resolver
ONE authority, two mirrored implementations (backend
`league_lifecycle_service.py::resolve_league_lifecycle`, frontend
`league-context.ts::resolveLeagueLifecycle`), same four real signals,
same branch order, same disclosed gap (no live NFL-calendar signal
exists anywhere in this repo -- OFFSEASON only reachable via an archived
profile; `currentWeek` always `null`). See `LEAGUE_CONTEXT.md`.

### LeagueSnapshot contract
`leagueSnapshotId` -- a `provenance_hash` over `{scoringProfileHash,
rosterStateHash, week, extra}`, not a stored object. Wired into
`redraft_weekly_lineup`, `redraft_waivers`, `redraft_trade_analysis`,
`redraft_trade_finder`, `redraft_kdst_streamer`,
`redraft_league_workspace_context`, and (CLOSURE pass part 2)
`redraft_weekly_home_actions` at its top level, sourced from that
endpoint's own internal lineup sub-call -- Weekly Home renders every
decision card from ONE response (`PRODUCT_ARCHITECTURE.md` invariant F,
PASS). See `LEAGUE_CONTEXT.md`.

### DecisionResultEnvelope contract + Draft's exclusion
`src/services/decision_envelope_service.py` (`DecisionResultEnvelope`).
Full envelope live on Start/Sit, Waivers, Trade Analysis, Trade Finder,
K/DST Streamer (one per position). **Draft (`redraft_decision_bundle{,
_v2}`) deliberately does NOT carry this envelope.** This pass
re-examined that exclusion on the merits (directive section 3) rather
than re-stamping the prior pass's conclusion, and validated it as a
genuine architectural difference:

1. Draft's own `ScoreProvenance` (`score_provenance_service.py`) is a
   richer, 13-field hashed provenance bundle purpose-built for a
   full-candidate-set simulation result -- not a gap the envelope would
   fill, but a system the envelope would duplicate or flatten.
2. Draft has no backend-declared single recommendation --
   `DecisionBundle` returns many live-ranked candidates with their own
   per-candidate confidence signals (`metricStatus`, `uncertainty`);
   "NWR PICK NOW" is a frontend-computed UI convenience
   (`findPickNow`), never a backend concept.
3. `in_season_decision_trace_service.TOOL_TYPES` is a week-scoped
   taxonomy; a pick-scoped draft record does not fit it without a real,
   non-trivial schema change, and the draft board itself is already a
   more complete permanent record than a trace-id would add.

Full reasoning: `DECISION_CONTRACTS.md`'s "Draft's exclusion,
re-examined" section. No code change follows from this finding -- the
correct action was to leave Draft as-is and document precisely why,
which is what this closure pass did.

### PlayerAvailabilityStatus authority + now-complete surface coverage
`src/services/player_availability_status_service.py` -- an honest
WRAPPER over the real, single intake mechanism
(`PlayerStatusOverride`/`current_player_status_overrides_service.py`),
never a second data source. Backend attachment via the shared facade
helper `DesktopBackendFacade._player_availability_status_map()`:
Draft, Lineup, Waivers, Trade Analysis, Trade Finder all attach it to
their own rows (proven byte-identical/consistently-keyed by
`tests/test_player_availability_status_consumer_consistency.py`).

**Frontend UI coverage, now complete** (CLOSURE pass part 3): rendered
via ONE shared, pure, tested mapping --
`playerAvailabilityBadgeTone()`/`playerAvailabilityBadgeLabel()`
(`player-detail-state.ts`) -- in the global Player Detail drawer, Draft's
Suggestions table + its own separate PlayerDrawer, Trade Analysis's
impact table, and Trade Finder's candidate cards. No surface computes a
second status transformation. `weekly-shared.tsx`'s `statusTone` remains
a legitimate, disclosed, PRESENTATION-only mapping of a different field
(the lineup slot's own already-override-derived `status` string) and was
correctly left alone, not merged into this one.

### Global Player Detail primitive + now-complete surface coverage
`player-detail-state.ts` (pure logic, tested) / `player-detail-
context.tsx` (React singleton, mounted once in `RedraftApp.tsx` above
the router) / `player-detail-drawer.tsx` (the one global drawer
component). **Adoption, as of this freeze:**

| Surface | Adopted | Notes |
|---|---|---|
| Lineup | YES (prior pass) | |
| Waivers | YES (prior pass) | |
| Trade Analysis | YES (this pass) | + Availability column |
| Trade Finder | YES (this pass) | + availability badges both sides |
| Free Agents | YES (this pass) | via new shared `appendPlayerDetailColumn()` |
| Opponent Rosters | YES (this pass) | kept alongside the existing "add to Trade Analysis" link |
| Players/Rankings | YES (this pass) | covers Players/Search too -- Search is the existing `SearchInput` inside Rankings, not a separate page |
| Players/Tiers | YES (this pass) | |
| Players/Compare | YES (this pass) | |
| Draft Room | Deliberately NOT adopted | its own existing `PlayerDrawer` is deeply draft-specific (roster legality, DecisionBundle candidate, queue/draft actions with no equivalent outside a draft in progress) and already reuses this primitive's own `PlayerIdentityHeader` -- it now ALSO renders the same `PlayerAvailabilityStatus` badge mapping (section above), so Draft is fully consistent on STATUS even though it keeps its own drawer shell |

Zero second drawer systems exist -- verified directly: exactly one
`<PlayerDetailProvider>` mount (`RedraftApp.tsx`), exactly one place
`playerAvailabilityBadgeTone`/`Label` are defined, every adopter imports
them rather than redefining them.

### Data Health authority
`src/application/desktop_facade.py::redraft_data_health` -- seven real
categories (`LEAGUE_SYNC`, `WEEKLY_PROJECTIONS`, `ROS_PROJECTIONS`,
`MARKET_ADP`, `PLAYER_STATUS`, `DECISION_ENGINE`, `SNAPSHOT`), unchanged
by this pass. See `DATA_AUTHORITY.md`.

### Canonical task map
HOME / DRAFT / LINEUP / IMPROVE TEAM / TRADES / PLAYERS / LEAGUE, each
mapped to real existing pages + route aliases, unchanged by this pass.
See `PRODUCT_ARCHITECTURE.md`'s "Canonical owner task map".

### Compatibility routes
Every legacy flat path (`/lineup`, `/waivers`, `/draft-room-v2`,
`/tiers`, `/data-health`, `/free-agents`, `/opponent-rosters`,
`/compare`, `/weekly-tools`, `/adp`, `/profile`, ...) still resolves via
`legacyRedirectTarget` into the active league's scoped route. None were
deleted. Unchanged by this pass.

### Governance / data state (test-seed vs. Freeze V7)
This worktree's bundled 2026 projection seed is a DIFFERENT, EXPIRED
artifact from the real-install Freeze V7 snapshot
(`DIFFERENT_ARTIFACT_TEST_SEED_EXPIRED`, verdict recorded by the prior
CLOSURE pass in `DATA_AUTHORITY.md`'s "Governance reconciliation"
section -- read-only, not renewed, not blocking this architecture work).
This is why every live-rendered check this pass performed shows
`PROJECTIONS BLOCKED` / `0 ranked players` -- a real, disclosed,
pre-existing environment gap, not a regression from this pass's changes.
Renewing it requires real owner authorization this agent cannot
self-issue, same as the repo's own established precedent.

## The one external caveat

**Live Sleeper IN_SEASON verification: `BLOCKED_EXTERNAL_TEST_FIXTURE`.**
No safe, non-owner Sleeper test league exists in this environment, and no
explicit owner authorization to use a real league was given for this
pass. This is the ONLY thing this freeze does not cover end-to-end live.
The precise, ready-to-run procedure for closing this gap later is
`docs/codex/NWR_LIVE_SLEEPER_INSEASON_ACCEPTANCE_PROCEDURE.md` -- run it
in full the first time either (1) a dedicated safe test Sleeper league
exists, or (2) the owner gives explicit, recorded, bounded, read-only
authorization to use a real league. Everything this procedure would
check is currently proven only by: pure-function/logic unit tests
(this repo's only test infrastructure with real component-render
coverage -- there is none), Sleeper-mocked facade tests, and a bounded
live Chrome session against LOCAL QA profiles only (see "Regression
evidence" below) -- never a real live Sleeper read.

## Regression evidence (directive section 5, re-run after adoption
## breadth completed)

- **One LeagueSnapshot authority:** unchanged, still true (no code in
  this pass touched `league_workspace_context_service.py` or
  `decision_envelope_service.py`'s hashing).
- **One PlayerAvailabilityStatus authority, now rendered more broadly,
  no duplicate transformations introduced:** confirmed directly by
  source search -- see "PlayerAvailabilityStatus authority" table above.
- **One player-detail primitive across the now-extended surfaces, no
  second drawer system:** confirmed directly by source search -- see
  "Global Player Detail primitive" section above.
- **DecisionResultEnvelope coverage is deliberate and documented:** see
  "DecisionResultEnvelope contract + Draft's exclusion" above and
  `DECISION_CONTRACTS.md`.
- **Lifecycle/routes/deep-links/context-isolation still correct:**
  unchanged this pass (no code touched `league_lifecycle_service.py`,
  `league-context.ts`'s resolver, or `LeagueScopedPage`); re-confirmed
  live during this pass's own Chrome session (a direct deep link to
  `/league/<unknown>/players` correctly rendered "League not found",
  not a crash).
- **Zero new console errors (real Chrome session, local QA profile
  only, clean start/stop):** a real, isolated backend
  (`scripts/run_nwr_desktop_api.py --port 18742 --mode redraft
  --repo-root <this worktree>`, isolated `NWR_REDRAFT_HOME` inside this
  worktree's own `local_exports/`, confirmed never the owner's real
  AppData install) + frontend (`npm run dev:redraft`, Vite port 1422)
  were started, a local QA profile ("QA Closure V3 Local") was created,
  and every newly-touched surface was visited: Rankings, Tiers &
  Positions, Compare, Free Agents, Opponent Rosters, Trade Analysis,
  Trade Finder, Draft Room. `read_console_messages` (onlyErrors) showed
  zero errors across the whole session. Every surface rendered its
  honest degraded state correctly (no crash) given this environment's
  real, disclosed `PROJECTIONS BLOCKED` gap -- the same constraint the
  prior two passes' own rendered-acceptance sections already disclosed,
  not new to this pass. The isolated store and its logs were deleted
  and both dev processes stopped cleanly afterward (confirmed via a
  failed `curl` against both ports post-teardown).
- **Existing engine behavior remains green, `marginal_roster_utility_v2`
  untouched:** guaranteed by construction -- `git diff --stat` from the
  start of this pass (`6f2220c0`) to this freeze's HEAD touches ONLY 4
  markdown docs, 7 frontend `.ts`/`.tsx` files, and adds 1 new doc; zero
  `src/**/*.py` files changed. Confirmed via test evidence too: targeted
  architecture tests (`test_league_workspace_context_service.py`,
  `test_decision_envelope_service.py`,
  `test_desktop_facade_architecture_wiring.py`,
  `test_player_availability_status_consumer_consistency.py`,
  `test_weekly_home_single_snapshot.py`) 28/28 passing;
  `tests/test_desktop_application_api.py` shows the SAME 5 pre-existing
  failures as before this pass, 0 new
  (`test_dynasty_facade_composes_real_governed_workflows`,
  `test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`,
  `test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`,
  `test_redraft_league_switching_isolates_draft_state_and_persists_active_profile`,
  `test_facade_has_no_streamlit_or_app_component_dependency` -- all 5
  pre-date this pass and its predecessors, per this branch's own
  established baseline).
- **Documentation matches reality:** `PRODUCT_ARCHITECTURE.md`,
  `DATA_AUTHORITY.md`, and `DECISION_CONTRACTS.md` were all updated this
  pass to reflect the completed adoption breadth and the Draft
  reconciliation finding. `LEAGUE_CONTEXT.md` and `RUN_POLICY.md` needed
  no changes -- nothing this pass did altered snapshot hashing, the
  lifecycle resolver, or the live-network policy.
- **Frontend build health:** `desktop`'s `npm run typecheck` (`tsc -b
  apps/dynasty/tsconfig.json apps/redraft/tsconfig.json`) clean, zero
  errors. `npx vitest run --no-file-parallelism` (single-process, per
  this pass's sequential-execution constraint): 196/196 passing (19
  test files), up from 173 at the start of this pass, 0 failures, 0 new
  failures introduced.

## Known remaining P2 items (unchanged from before this pass)

Richer Trade Finder (currently one-for-one only, no multi-player
packages), playoff-equity modeling, write-back transactions (this
product remains read-only to Sleeper by design), mobile, new projection
providers beyond the approved Sleeper stopgap, broader real-time news
coverage beyond the manual override mechanism, opponent-manager
behavioral modeling, and deeper historical analytics surfaces. None of
these were in scope for this architecture-only program.

## Final handoff

```
NWR_PRE_UI_ARCHITECTURE_CLOSURE_PASS_3
FINAL HEAD: d1754d797ab5d05d9ddb4b62cd968be26d2c3fbc
PLAYER_DETAIL_SURFACE_COVERAGE: COMPLETE -- Lineup, Waivers (prior pass),
  Trade Analysis, Trade Finder, Free Agents, Opponent Rosters,
  Players/Rankings (covers Players/Search), Players/Tiers,
  Players/Compare (this pass). NOT adopted, deliberately: Draft Room
  (keeps its own existing, deeply draft-specific drawer, which now also
  renders the shared PlayerAvailabilityStatus badge mapping).
PLAYER_AVAILABILITY_UI_COVERAGE: COMPLETE -- Draft (Suggestions table +
  PlayerDrawer), Trade Analysis (impact table), Trade Finder (candidate
  cards) now render the authority via one shared, tested mapping
  (playerAvailabilityBadgeTone/Label), on top of Lineup/Waivers' prior
  coverage via the global drawer.
DECISION_ENVELOPE_RECONCILIATION: Draft's exclusion RE-EXAMINED and
  VALIDATED as a genuine architectural difference (richer existing
  ScoreProvenance hash system, no backend-declared single recommendation,
  a trace-id schema that is genuinely the wrong shape for a pick-scoped
  record) -- not deferred effort. No migration performed; reasoning
  recorded in DECISION_CONTRACTS.md.
REGRESSION: GREEN -- desktop typecheck clean; desktop vitest 196/196
  (0 new failures); targeted backend architecture tests 28/28; backend
  baseline (test_desktop_application_api.py) same 5 pre-existing
  failures, 0 new; live Chrome session against a local QA profile shows
  0 console errors across every newly-touched surface; zero src/**/*.py
  files changed this pass (marginal_roster_utility_v2 and every other
  engine untouched by construction).
LIVE_SLEEPER_IN_SEASON: BLOCKED_EXTERNAL_TEST_FIXTURE
DUPLICATE_SYSTEMS_CREATED: NO -- verified directly: exactly one
  <PlayerDetailProvider> mount app-wide (RedraftApp.tsx), exactly one
  definition each of playerAvailabilityBadgeTone()/Label() reused by
  every render site (the global drawer itself was refactored to use
  them instead of its own inline ternary), exactly one
  PlayerAvailabilityStatus authority on the backend
  (_player_availability_status_map()), exactly one LeagueSnapshot
  hashing scheme, exactly one lifecycle resolver (two mirrored
  implementations by design, documented as such since the original
  pass, not a duplicate).
STRUCTURE_FREEZE: YES
  Frozen: LeagueWorkspaceContext contract, routing contract (canonical
  tree + compatibility redirects), lifecycle resolver, LeagueSnapshot
  contract, DecisionResultEnvelope contract (5 tools migrated, Draft's
  exclusion validated with recorded reasoning), PlayerAvailabilityStatus
  authority with now-complete backend AND frontend surface coverage,
  the global Player Detail primitive with now-complete surface coverage
  (Draft Room deliberately excluded, with reasoning), Data Health
  authority, the canonical task map, all compatibility routes, and the
  governance/data-state distinction (this worktree's expired test seed
  vs. the real-install Freeze V7 snapshot).
  Remaining: exactly one external-verification gap -- a real live
  Sleeper IN_SEASON round trip through every adopted surface, blocked on
  the unavailability of a safe test fixture (section 4 / the
  BLOCKED_EXTERNAL_TEST_FIXTURE line above), NOT on anything locally
  controllable. Run
  docs/codex/NWR_LIVE_SLEEPER_INSEASON_ACCEPTANCE_PROCEDURE.md in full
  the first time a safe test league or explicit bounded owner
  authorization exists, then update this freeze doc's verdict line to
  record that result.
```
