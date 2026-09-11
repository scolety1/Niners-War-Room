# Product Architecture

**Status:** Written by the NWR pre-UI product-architecture hardening pass
(branch `upgrade/nwr-pre-ui-architecture-v1-20260910`, forked from
`research/nwr-2026-inseason-baseline-20260910` / `overnight/nwr-full-
advance-v3-20260909`). This is the current, accurate architectural truth
for the live desktop Redraft product. Root docs that predate this pass
(`README.md`, `MISSION.md`, `DATA_MODEL.md`, `MODEL_SPEC.md`,
`USER_WORKFLOW.md`, `AGENTS.md`, `docs/codex/ARCHITECTURE*.md`) describe a
Streamlit, local-only, CSV-pack, dynasty/keeper-league prototype that
predates the live desktop Redraft app entirely -- they are **legacy**,
not wrong-but-stale; they document a different, earlier product line that
still exists in this repo (the historical backtest/`marginal_roster_
utility_v2`/Team Score V2 research program) but is not what an owner
opens today. Do not delete them -- they are the real historical record --
but do not treat them as describing the live product either.

## What NWR is, today

NWR is **one league decision workspace** for a fantasy football owner,
not "Draft App + a collection of in-season tools." One React/Tauri
desktop app (`desktop/apps/redraft`), one Python backend facade
(`src/application/desktop_facade.py`, 6478 lines) served over a local
HTTP loopback (`src/desktop_api/server.py`), talking to Sleeper and
FantasyPros live for an owner's real leagues, with a separate offline
research/backtest product line (`src/services/*_backtest*`, the Dynasty
app) sharing the same facade/contracts infrastructure (documented in
`RECONCILIATION_CONFLICTS.md`).

## Layers

```
┌─────────────────────────────────────────────────────────────┐
│ React (desktop/apps/redraft/src)                             │
│  RedraftApp.tsx -- routing, AppShell, ActiveLeagueSelector    │
│  leagues.tsx -- league chooser                                │
│  in-season.tsx, pages.tsx -- owner task pages                 │
│  league-context.ts -- LIFECYCLE RESOLVER (client mirror)      │
│  player-drawer-core.tsx -- universal player identity (seed)   │
├─────────────────────────────────────────────────────────────┤
│ @nwr/api-client -- typed HTTP client (NwrApiClient)           │
│ @nwr/contracts -- shared TS types, camelCase, no server logic │
├─────────────────────────────────────────────────────────────┤
│ src/desktop_api/server.py -- local HTTP loopback, route table │
├─────────────────────────────────────────────────────────────┤
│ src/application/desktop_facade.py -- ONE facade, all product  │
│  modes (redraft, dynasty) -- every route above calls exactly  │
│  one method here                                               │
├─────────────────────────────────────────────────────────────┤
│ src/services/*.py -- real engines (weekly_lineup_optimizer,   │
│  waiver_engine, redraft_trade_analysis, trade_finder,         │
│  marginal_roster_utility (shadow_numeric_authorities), draft  │
│  roster legality, ...) -- UNCHANGED by this pass               │
├─────────────────────────────────────────────────────────────┤
│ NEW this pass, cross-cutting, additive only:                  │
│  league_lifecycle_service.py                                  │
│  league_workspace_context_service.py                          │
│  decision_envelope_service.py                                 │
│  player_availability_status_service.py                        │
└─────────────────────────────────────────────────────────────┘
```

**Principle this pass followed throughout:** every new module above is a
*wrapping/identification* layer over an existing, unchanged engine --
never a reimplementation. Every existing decision engine (draft legality,
`marginal_roster_utility_v2`, weekly projections, Start/Sit, Waivers,
Trade Analysis, Trade Finder, Streamers) computes exactly what it
computed before this pass; this pass only makes the product *speak about*
those computations in one consistent way (identity, lifecycle, snapshot,
envelope, status, health).

## Canonical owner task map (directive section 7)

The product's task-first IA. Each bucket maps to concrete existing pages
(no visual redesign this pass -- the existing sidebar `NAVIGATION` groups
in `RedraftApp.tsx` still list every page individually; this map is the
architectural truth a future visual pass should organize around):

| Canonical task | Primary existing page(s) | Route alias(es) |
|---|---|---|
| **HOME** | Weekly Home (`WeeklyHomePage`, `in-season.tsx`) | `/league/:key/home` |
| **DRAFT** | Draft Room V2 (`DraftRoomV2Page`, `draft-room-v2.tsx`) -- Suggestions/Board/Queue/Teams/Cheat Sheet all live inside it | `/league/:key/draft` |
| **LINEUP** | Start/Sit (`LineupPage`, `in-season.tsx`) | `/league/:key/lineup` |
| **IMPROVE TEAM** | Waivers/Add-Drop/FAAB (`WaiversPage`, primary), cross-linked to Free Agents (`FreeAgentsPage`) and the K/DST Streamer (`WeeklyToolsPage`) | `/league/:key/improve` (alias -> Waivers), `/league/:key/free-agents`, `/league/:key/weekly-tools` |
| **TRADES** | Trade Analysis (`TradeAnalysisPage`, primary), cross-linked to Trade Finder (`TradeFinderPage`) | `/league/:key/trades` (alias -> Trade Analysis), `/league/:key/trade-finder` |
| **PLAYERS** | Rankings (`RankingsPage`, primary), cross-linked to Tiers (`TiersPage`), Compare (`ComparePage`), Cheat Sheet, Market Data/ADP (`AdpProvidersPage`) | `/league/:key/players` (alias -> Rankings), `/league/:key/tiers`, `/league/:key/compare`, `/league/:key/cheat-sheet`, `/league/:key/adp` |
| **LEAGUE** | My Roster (`MyRosterPage`, primary), cross-linked to Opponent Rosters (`OpponentRostersPage`), Profile & Scoring (`ProfilePage`), Data Health (`DataHealthPage`) | `/league/:key/league` (alias -> My Roster), `/league/:key/opponent-rosters`, `/league/:key/profile`, `/league/:key/data-health` |

"Primary + cross-linked" (not a rebuilt tabbed mega-page) is a deliberate,
disclosed simplification -- it maps every existing working page under the
canonical name the directive asks for without touching any page's visual
layout or duplicating functionality. A future visual-redesign pass can
turn these into real in-page tab groups; this pass only had to prove the
mapping is coherent and route-addressable, which it now is.

## Routing (directive sections 1/2)

- **Canonical, deep-linkable tree:** `/league/:leagueKey/<page>`, where
  `leagueKey` is `LeagueProfile.profileId` -- already a stable, unique,
  opaque id; no second identity was invented. See `LEAGUE_CONTEXT.md`.
- **`LeagueScopedPage`** (`RedraftApp.tsx`) is the one gate every such
  route passes through: unknown key -> "League not found"; known but not
  active -> activates it (`activateRedraftProfile`) before rendering
  anything underneath; already active -> renders immediately. This is
  what makes a deep link resolve the same league regardless of what was
  previously globally active (invariant H).
- **Legacy flat paths** (`/lineup`, `/waivers`, `/draft-room-v2`, ...)
  remain mounted as `<Navigate>` compatibility redirects to
  `/league/<activeProfileId>/<same-subpage>` -- same destination content,
  now carrying real league identity in the URL (invariant I). None were
  deleted.
- **Lifecycle-aware landing** (invariant A): opening or switching to a
  league no longer hardcodes a destination. `leagues.tsx`'s card click
  used to unconditionally navigate to `/draft-room-v2` regardless of
  whether the league had already finished drafting -- a real, reproduced
  bug this pass fixed. It now calls `resolveLeagueHomeSubpath` (`league-
  context.ts`), which sends PRE_DRAFT/LIVE_DRAFT leagues to the Draft
  workspace and IN_SEASON/OFFSEASON leagues to League Home.

## Lifecycle resolver (directive section 2)

ONE authority, in two mirrored forms:

- Backend: `src/services/league_lifecycle_service.py::resolve_league_lifecycle`
- Frontend: `desktop/apps/redraft/src/league-context.ts::resolveLeagueLifecycle`

Both take the same four real signals (archived, draft-board configured,
drafted count, total draft picks, current-pick pointer) and return the
same four states in the same branch order -- see `LEAGUE_CONTEXT.md` for
the exact rules and the one disclosed gap (no live NFL-calendar signal
exists anywhere in this repo, so OFFSEASON is only reachable via an
archived profile).

## Context isolation (directive invariant G)

A real, reproduced bug this pass found and fixed: six `useAsync` call
sites (Start/Sit, Waivers, My Roster, Trade Analysis's two roster reads,
Trade Finder, Compare's This-Week/Roster-Fit modes) were keyed only by
`isSleeper`/`mode`/`week` -- switching from one Sleeper league to another
Sleeper league with the same mode/week silently kept showing the
PREVIOUS league's data. Every one is now also keyed by
`data.activeProfileId`. `LeagueScopedPage` additionally keys its rendered
subtree by `leagueKey` so page-local UI state (a selected week, a search
query) never survives a league switch either.

## What this pass explicitly did NOT do

- No visual redesign -- same `AppShell`/`Panel`/`DataTable` component
  library, same CSS, same sidebar nav grouping labels.
- No change to any decision engine's actual computation (draft legality,
  `marginal_roster_utility_v2`, weekly projections, Start/Sit, Waivers,
  Trade Analysis, Trade Finder, Streamers) -- verified by an unchanged
  backend/frontend test-failure baseline throughout (5 pre-existing
  backend failures, 0 new; 173/173 frontend tests passing, up from 165
  with only additive new tests).
- No new live data acquisition (no new provider, no new API). The
  `LeagueWorkspaceContext`'s `currentWeek` field is honestly `null` --
  this repo has no live NFL-calendar signal (confirmed by search: no
  wrapper around Sleeper's `GET /v1/state/nfl` or equivalent exists
  anywhere) and adding one was judged out of this pass's architecture-only
  scope.
- Full adoption of the universal player primitive (directive section 8)
  across Lineup/Waivers/Trades/Players/Free Agents/Opponent Rosters --
  only proven in the Draft Room this pass; see `player-drawer-core.tsx`'s
  own module docstring and the final handoff's PARTIAL disclosure.

## Rendered acceptance pass (directive section 12)

Real Chrome session against a real running stack: backend
(`scripts/run_nwr_desktop_api.py --port 18742 --mode redraft --repo-root
<this worktree>`, dev token matching the frontend's own `browserRuntime()`
fallback, isolated `NWR_REDRAFT_HOME` store inside this worktree's own
`local_exports/`, confirmed never the owner's real AppData install) +
frontend (`npm run dev:redraft`, Vite port 1422). Backend verified live
via `curl /healthz` before touching the browser; store deleted afterward.

Driven with two local QA profiles ("QA League A (pre-draft)", "QA League
B (in-season)") -- never a real Sleeper import, never the owner's real
leagues.

**Two real, live-reproduced bugs found and fixed during this pass** (not
caught by typecheck or the existing test suite, since this repo has no
React-rendering test infrastructure -- see the characterization table
below):

1. `/profile` had been mechanically swept into the legacy-route ->
   `/league/:activeProfileId/profile` redirect, but it's also the
   create-a-new-league UI, reachable with NO active league. Reproduced
   live: clicking "Set up a league" on the empty chooser bounced straight
   back to the chooser. Fixed by keeping `/profile` a direct,
   always-available route.
2. `LeagueScopedPage`'s activation effect could get permanently stuck on
   "Opening `<league>`…" after switching leagues via the header control --
   a `.finally()` callback's `setActivating(false)` was incorrectly gated
   behind the same stale-closure guard used to protect `onUpdate`.
   Reproduced live (not a timing fluke -- also reproduced by reloading
   the page with the target league already active) and fixed; see the
   commit for the full trace.

Both fixes verified live afterward: switching QA League A <-> QA League B
via the header control renders the destination immediately; a direct
deep link to the non-active league (invariant H) correctly activates and
renders it, including surviving a hard browser refresh (F5).

**What was verified live, rendered, with zero console errors across the
whole session** (checked via `read_console_messages` after every
navigation batch): league chooser -> create two local leagues -> all
seven canonical `/league/:key/<bucket>` routes (home, draft, lineup,
improve, trades, players, league) for both leagues; nine legacy flat
routes (`/lineup`, `/tiers`, `/data-health`, `/free-agents`,
`/opponent-rosters`, `/compare`, `/weekly-tools`, `/adp`,
`/draft-room-v2`) each correctly redirecting into the active league's
scoped route with identical content; the Draft Room's real setup screen
(team count/slot/CPU-opponent controls); the new Data Health page's all
seven categories rendering real, correct, honestly-degraded state; the
header "Switch league" control; a direct deep link to a non-active
league; a hard refresh on a league-scoped deep link.

**Real, disclosed blocker found while testing, precisely root-caused
(see `DATA_AUTHORITY.md`)**: the bundled 2026 projection seed's
governance approval receipt expired 2026-09-09, one day before this
session (2026-09-10) -- `redraft_engine_v1_service`'s own receipt
validator rejects any receipt where `valid_until < today`. This blocks
`RankingResult` generation for EVERY profile in this environment, which
in turn means `draftBoard` is `None` for every profile (`redraft_
bootstrap` only builds it `if ranking is not None`). Consequence: this
session could not complete a real mock draft to reach a genuine
backend-driven IN_SEASON lifecycle state, so the live-rendered pass
verified PRE_DRAFT routing (Draft Room) end-to-end but NOT the
IN_SEASON->League-Home transition end-to-end live -- that remains
verified by unit tests only (`league-context.test.ts`) plus code review,
not a live render. Renewing the governance receipt requires real owner
authorization this agent cannot self-issue (the receipt's own history
shows exactly this happening once before, with explicit owner
authorization) -- out of this pass's scope to do unilaterally.

## Characterization test invariants (directive section 10)

Honest status per invariant, with the real test evidence for each --
some are verified by an automated test, some only by code review + the
later rendered Chrome acceptance pass (this repo has no React-rendering
test infrastructure at all: `desktop/vitest.config.ts` runs `environment:
"node"` and only collects `*.test.ts`, never `*.test.tsx` -- every
existing test in this codebase, before and after this pass, is a
pure-function/logic test, not a component-render test).

| # | Invariant | Status | Evidence |
|---|---|---|---|
| A | Opening an in-season league does not auto-navigate to Draft Room | **PASS (unit-tested); IN_SEASON case not live-rendered** | `league-context.test.ts` ("sends an in-season league to League Home, not the Draft Room"); real bug found + fixed in `leagues.tsx`; the rendered Chrome pass (section 12) confirmed PRE_DRAFT correctly stays on Draft Room live, but could not reach a genuine backend-driven IN_SEASON state to confirm the League-Home landing live (see section 12's disclosed blocker) |
| B | Every major decision identifies league + snapshot | **PARTIAL** | `leagueSnapshotId` wired into 5/5 in-season tools + the standalone context endpoint (unit-tested); Draft's DecisionBundle uses its own separate, older provenance system, not this one -- see `DECISION_CONTRACTS.md` |
| C | Every recommendation can expose a trace ID | **PASS for in-season tools** | `_record_decision_trace_safe` now returns the real id; live-mocked proof via `test_kdst_streamer_response_carries_trace_ids_and_league_snapshot_id`; Draft has no trace id (unchanged, out of scope) |
| D | Every recommendation communicates stale/unavailable required data | **PASS (pre-existing + extended)** | `providerHealth`/`issues` already existed (`weekly_projection_provider_service` tests, 15 pre-existing); `decisionEnvelope.issues` now carries the same signal for Start/Sit and Waivers |
| E | Player status is consistent across Draft/Lineup/Waivers/Trades | **NOT YET SATISFIED, disclosed** | The one authority (`PlayerAvailabilityStatus`) now exists and is real, but NO product surface was migrated to consume it this pass -- each still renders its own local heuristic. See `DATA_AUTHORITY.md`. |
| F | Weekly Home uses one LeagueSnapshot | **NOT ARCHITECTURALLY GUARANTEED, disclosed** | `WeeklyHomePage` composes 3 independent facade calls (`redraftWeeklyHomeActions`, `redraftWeeklyLineup`, `redraftFreeAgents`), each computing its own `leagueSnapshotId` from its own live roster read within the same request -- in practice near-identical (same request, sub-second apart) but no single snapshot value is threaded through and asserted equal. A real follow-up, not silently claimed done. |
| G | Switching leagues cannot leak prior league state | **PASS** | Real bug found + fixed: 6 `useAsync` call sites missing `data.activeProfileId` in their dependency arrays (`in-season.tsx`, `pages.tsx`); `LeagueScopedPage` also keys its rendered subtree by `leagueKey`; the header "Switch league" control confirmed live in the rendered Chrome pass (section 12), including a second real bug (stuck loading state) found and fixed there |
| H | A deep link always resolves the same league | **PASS** | Unit tests + confirmed live in the rendered Chrome pass (section 12): a direct deep link to a non-active league activates and renders it correctly, including surviving a hard browser refresh -- this exact flow also surfaced and led to fixing the two real bugs documented in section 12 |
| I | Old routes redirect correctly during migration | **PASS** | `legacyRedirectTarget` pure function, unit-tested (`league-context.test.ts`); every legacy flat route now uses it via `LegacyRedirect`; 9 legacy paths confirmed live in the rendered Chrome pass (section 12), each redirecting to the correct scoped route with identical content |

Two invariants (E, F) are honestly NOT fully satisfied by this pass and
are called out as PRE-UI BLOCKERS REMAINING in the final handoff rather
than rounded up to PASS.

## Where to look next

- `LEAGUE_CONTEXT.md` -- LeagueWorkspaceContext, lifecycle resolver rules,
  LeagueSnapshot identity/hashing.
- `DATA_AUTHORITY.md` -- every data/trust authority, what's live vs.
  static vs. manual, real disclosed gaps.
- `DECISION_CONTRACTS.md` -- DecisionResultEnvelope, migration status per
  tool, trace-id plumbing.
- `RUN_POLICY.md` -- current live-network policy (supersedes its own
  legacy section for the desktop Redraft product).
