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

## Where to look next

- `LEAGUE_CONTEXT.md` -- LeagueWorkspaceContext, lifecycle resolver rules,
  LeagueSnapshot identity/hashing.
- `DATA_AUTHORITY.md` -- every data/trust authority, what's live vs.
  static vs. manual, real disclosed gaps.
- `DECISION_CONTRACTS.md` -- DecisionResultEnvelope, migration status per
  tool, trace-id plumbing.
- `RUN_POLICY.md` -- current live-network policy (supersedes its own
  legacy section for the desktop Redraft product).
