# NWR UI Foundation Freeze V1

Written by the `ui/nwr-visual-redesign-v1-20260910` visual/UX redesign
pass. Scope: presentation layer only, over the frozen contracts in
`NWR_PRE_UI_PRODUCT_STRUCTURE_FREEZE_V1.md` -- no decision-engine
math, `LeagueSnapshot` semantics, `LeagueWorkspaceContext`, lifecycle
resolver, `PlayerAvailabilityStatus` authority, `DecisionResultEnvelope`
contracts, provider architecture, or scoring logic was touched. Nothing
was merged/pushed/deployed; the owner's real leagues and AppData
install were never touched.

**START HEAD:** `9fa3197545044e92f4587f5a1b090006e4230064`
**FINAL HEAD:** `698bf5476f70cbfbc67855e02a5659bd0468b4a8`
(branch `ui/nwr-visual-redesign-v1-20260910`, worktree
`C:\NWR\ui-visual-redesign-v1`)

## Phase 1 -- current UI audit (concrete findings)

Rendered live (Chrome, local QA profiles only) before any redesign
work: League chooser, Home, Draft Room, Rankings, Lineup, and the
pre-existing player drawer/status bar. Findings, each classified per
Phase 9:

1. **Sidebar nav did not reflect the canonical owner task map**
   (`PRODUCT_ARCHITECTURE.md` already documented HOME/DRAFT/LINEUP/
   IMPROVE TEAM/TRADES/PLAYERS/LEAGUE as the architectural truth, but
   the actual nav was still 6 old ad hoc groups -- "League workspace",
   "Draft command", "Player board", "League", "Weekly tools",
   "System"). **INFORMATION-ARCHITECTURE PROBLEM.** Fixed this pass
   (Phase 3).
2. **League identity lived in a full-width content-area bar**
   (`ActiveLeagueSelector`) that repeated the league name/format and
   pushed every page's real content down, rather than the shell's
   actual top-left. **UX PROBLEM / IA PROBLEM.** Fixed this pass.
3. **Four freshness pills (Identity/ADP/Projections/Ready) were
   always visible** in that same bar -- real, useful data, but
   competing with page content for attention on every single page.
   **VISUAL-POLISH ISSUE / IA PROBLEM** (directive Phase 3 explicitly
   asks for exactly one quiet indicator, click for detail). Fixed
   this pass.
4. **Weekly Home's "NWR Actions" was a bare `<ol>`** -- index, one
   summary line, a category tag, an "Open" link. No WHY, no
   ALTERNATIVE, no CONFIDENCE, no per-action FRESHNESS -- the real
   underlying data existed (`WeeklyHomeAction.detail`) but was not
   surfaced. **INFORMATION-ARCHITECTURE PROBLEM** (this is precisely
   Phase 4/6's gap). Fixed this pass.
5. **The global Player Detail drawer** rendered "Availability status"
   and "Opened from <raw source code>" as two plain `<h3>` sections --
   functionally correct, visually a stub. `active.source` (e.g.
   `"TRADE_ANALYSIS"`) leaked as literal internal text into the
   primary view. **VISUAL-POLISH ISSUE + a small INTERNAL-LANGUAGE
   LEAK.** Fixed this pass.
6. **A real BUG, found live during this pass's own dogfood**: the
   player drawer's `top: 0` positioned it flush with the true
   viewport top, so a player name that wraps to two lines rendered
   its first line partially behind the native window title bar's
   minimize/maximize/close controls. Reproduced with a synthetic long
   name ("Christian McCaffrey-Jefferson Worthington III"), confirmed
   via zoomed screenshot, root-caused (`--chrome-height` not
   accounted for), and fixed. Affects BOTH the new global drawer and
   Draft Room's own separate `PlayerDrawer` (same shared CSS class).
   **BUG.** Fixed this pass.
7. **Draft Room's visual language** (many small 9-11px-font panels,
   a dozen colored chip styles, a three-pane dense workspace) reads
   as a trading-terminal aesthetic, not "calm, confident, premium."
   Functionally strong (a real, tested, owner-validated power tool)
   but visually inconsistent with the new design system.
   **VISUAL-POLISH ISSUE, correctly OUT OF SCOPE this pass** (Phase 7
   explicitly scopes this pass to Shell + Home + Player Drawer only;
   Draft Room is deliberately untouched, not overlooked).
8. **Honest empty/degraded states were already a real strength**
   (Rankings' "0 ranked players" + "LEAGUE SPECIFIC" badge, the
   "Sleeper league required" empty state, `ProviderStatusLine`'s
   disclosed-heuristic freshness detail). **GOOD AS-IS**, preserved
   and reused as the foundation for the new components rather than
   replaced.
9. **Design tokens existed but were not documented as a system** --
   real, consistent colors (`--gold`/`--violet`/`--crimson`/`--cyan`/
   `--green`) and a real `safe`/`review`/`blocked`/`offline` status
   vocabulary, but no semantic
   recommended/alternative/warning/unavailable/stale/close-call
   mapping and no written type/spacing scale. **VISUAL-POLISH /
   DOCUMENTATION GAP.** Addressed this pass (`NWR_UI_DESIGN_SYSTEM_V1.md`).

## Design direction

A serious decision system, dark-first (inherited, already highly
legible), restrained gold/crimson accents (inherited, not expanded).
Color communicates status/urgency/recommendation, never decorative
variety. See `NWR_UI_DESIGN_SYSTEM_V1.md` for the full token/component
reference.

## What was implemented (Phase 7 scope: Shell + Home + Player Drawer)

- **League shell**: canonical HOME/DRAFT/LINEUP/IMPROVE TEAM/TRADES/
  PLAYERS/LEAGUE nav, reordered by the active league's real lifecycle
  (`resolveLeagueLifecycle` -- the one existing shared authority, no
  new heuristic); sidebar top-left league identity (name, click ->
  chooser, lifecycle stage badge, Switch League); one compact header
  freshness chip with a click-for-detail popover replacing the four
  permanent pills. `AppShell` (shared with Dynasty) gained two
  optional, additive props; Dynasty passes neither and is unaffected
  (confirmed: single call site, unchanged typecheck/vitest).
- **Home**: a THIS WEEK strip (league/week/lifecycle stage/freshness)
  + up to 5 NWR Actions rendered via the new `DecisionExplain`
  grammar (RECOMMENDATION -> WHY -> ALTERNATIVE/UNCERTAINTY/DATA ->
  ADVANCED), a "showing top N of M" note when more exist, and a calm
  "You're set for now" state when none apply. `home-action-explain.ts`
  derives every field from data the backend already computed
  (`WeeklyLineupSwap`/`Slot`, `WaiverAddCandidate`,
  `TradeFinderCandidate`, `KdstStreamerRow`) -- unit-tested, 5/5
  passing.
- **Universal Player Drawer**: header -> STATUS/NEWS (primary) ->
  "Opened from <plain-language surface name>" -> ADVANCED/PROVENANCE
  (collapsed `<details>`, raw ids/status-category/override-kind).
- **Decision explanation pattern**: `decision-explain.tsx`
  (`DecisionExplain`) is the one reusable grammar component, wired
  into Home, left available (not yet adopted) for Lineup/Waivers/
  Trades.

## Live render (Phase 8)

Real, isolated backend + frontend (local QA profiles only, isolated
`NWR_REDRAFT_HOME`, confirmed never the owner's real AppData install;
both processes and the store were torn down cleanly afterward).
Rendered: League chooser (multiple profiles, one with a deliberately
long QA name), Home (both populated and zero-action states), Lineup
(with a real "View" -> drawer round trip and a deliberately long
synthetic player name), Draft Room, Trade Analysis, Rankings, Profile/
league-creation flow, the Switch League control, the freshness
popover. Widths tested: 1524px, 1024px, 900px (the existing app-wide
mobile-nav breakpoint took over correctly below 930px -- not
specifically redesigned this pass, just confirmed non-broken).
`read_console_messages(onlyErrors)` showed **zero errors** on a clean
hard-reload baseline and after a full navigation sweep across every
surface listed above.

**Disclosed limitation, same class as every prior pass's**: this
worktree's bundled 2026 projection seed is expired
(`DIFFERENT_ARTIFACT_TEST_SEED_EXPIRED`, pre-existing, documented in
`DATA_AUTHORITY.md`), so every local QA profile shows
`PROJECTIONS BLOCKED`/0 ranked players, and no safe non-owner Sleeper
league exists in this environment. Home's populated NWR-Actions state
and the Player Drawer's populated status state were therefore verified
using **disclosed, client-side synthetic `fetch` response data**
(installed via the browser's own JS console, never touching the real
backend, never touching a real league) rather than a genuine live
Sleeper round trip -- the exact same `BLOCKED_EXTERNAL_TEST_FIXTURE`
constraint the architecture-freeze pass already recorded. The
rendering code itself does not distinguish a real vs. synthetic fetch
response (both go through the same typed client/React paths), so this
is real evidence the components render correctly given the documented
shape of data -- but it is not a substitute for a genuine live Sleeper
round trip, and is not claimed as one.

Draft Room's own separate `PlayerDrawer` shares the exact CSS class
(`--player-drawer`) the drawer-positioning bug fix touched, confirmed
by source search; a live click-through re-verification of THAT
specific drawer was not possible in this environment (Draft Room's
Suggestions/Cheat Sheet tables are both empty under the same
`PROJECTIONS BLOCKED` constraint, so there is no clickable row to open
it from) -- the fix is a pure vertical-position CSS change with no
data dependency, so this is architectural confidence, not a second
live-rendered proof.

## Architecture changes

**NONE.** Zero `src/**/*.py` files touched. Zero changes to
`@nwr/contracts`. The only non-Redraft-frontend file touched is
`desktop/packages/ui/src/components.tsx` (`AppShell`), and only via
two new optional, additive props -- confirmed zero effect on Dynasty
(its one call site passes neither prop; typecheck and vitest for both
apps are unchanged/green).

## Backend/model changes

**NONE.**

## Regression evidence

- `npx tsc -b apps/dynasty/tsconfig.json apps/redraft/tsconfig.json`:
  clean, zero errors.
- `npx vitest run --no-file-parallelism`: 201/201 passing (up from
  196 at the start of this pass, +5 new tests in
  `home-action-explain.test.ts`, 0 regressions).
- `git diff --stat` from `9fa31975` to `698bf547`: 9 files changed (5
  modified, 4 new), all under `desktop/apps/redraft/src` or
  `desktop/packages/ui/src` -- zero backend files, zero contract
  files.
- Live Chrome session: zero console errors on a clean reload and
  across a full navigation sweep (see "Live render" above).

## UX classification summary (Phase 9)

| Finding | Classification | Status |
|---|---|---|
| Nav not organized by canonical task map | Information-architecture problem | Fixed |
| Full-width identity bar competing with content | UX / IA problem | Fixed |
| Four permanent freshness pills | Visual-polish / IA problem | Fixed |
| Home actions had no WHY/ALTERNATIVE/CONFIDENCE | IA problem | Fixed |
| Drawer sections were plain stub headers | Visual-polish + internal-language leak | Fixed |
| Drawer text collides with window title bar (long names) | **Bug** | Fixed |
| Draft Room's dense trading-terminal visual language | Visual-polish issue | Out of scope, disclosed (next surface) |
| Rankings/empty-state honesty pattern | Good as-is | Preserved, reused |
| Undocumented design tokens | Documentation gap | Addressed (`NWR_UI_DESIGN_SYSTEM_V1.md`) |
| Player Drawer's THIS WEEK/ROS/ROSTER FIT/MARKET sections | Genuine, disclosed scope gap (needs new data plumbing) | Not done -- out of a presentation-only pass |

## First Visual Freeze verdict

**CUT.** Shell + Home + Player Drawer are genuinely coherent: one
consistent design language (tokens, typography, spacing, card
grammar, decision-explanation pattern, status/freshness treatment)
implemented across all three, live-rendered with zero console errors,
a real bug found and fixed during dogfooding, zero regressions in
typecheck/tests, and zero architecture/backend changes. The freeze
below is scoped exactly to what this pass verified -- it does NOT
claim Draft Room, Lineup, Waivers, Trades, Players, or League are
redesigned (they are not, deliberately), and it does NOT claim a
genuine live Sleeper round trip was rendered (the same disclosed,
pre-existing environment constraint every prior pass on this repo
has recorded).

### What is frozen

- **Design tokens**: semantic state tokens (`--nwr-recommended/
  -alternative/-warning/-unavailable/-stale/-healthy/-close-call/
  -rostered/-available`), typography utility classes, spacing tokens
  -- `NWR_UI_DESIGN_SYSTEM_V1.md`, `desktop/apps/redraft/src/redraft.css`.
- **Navigation**: canonical HOME/DRAFT/LINEUP/IMPROVE TEAM/TRADES/
  PLAYERS/LEAGUE grouping, lifecycle-ordered (`buildNavigation` in
  `RedraftApp.tsx`).
- **League shell**: sidebar identity block (`ShellIdentity`), header
  freshness indicator (`FreshnessIndicator`) --
  `desktop/apps/redraft/src/shell-identity.tsx`.
- **Action-card grammar**: `home-action-explain.ts` (pure, tested
  derivation) + `DecisionExplain` rendering it on Home.
- **Decision-explanation grammar**: `decision-explain.tsx`
  (RECOMMENDATION -> WHY -> ALTERNATIVE/UNCERTAINTY/DATA -> ADVANCED),
  available for reuse by later passes.
- **Status/freshness treatment**: one freshness chip + popover
  pattern (shell), one `.nwr-this-week` strip pattern (Home).
- **Global player drawer**: header -> Status/News -> Opened From ->
  Advanced/Provenance, plus the shared drawer-positioning fix.
- **Responsive assumptions**: existing app-wide breakpoints (1180px,
  930px mobile-nav, 760px) reused as-is; new components verified
  non-broken at 1524/1024/900px, not independently re-architected.

### Not frozen / explicitly remaining

- Draft Room's own visual language (deliberately untouched).
- Lineup/Waivers/Trades/Players/League page-level redesigns (Phase 7
  scoped this pass to Shell + Home + Player Drawer only).
- Player Drawer's context-specific sections (THIS WEEK/ROS/ROSTER
  FIT/MARKET/WHY NWR CARES) -- needs new per-surface data plumbing,
  a real architectural addition out of this presentation-only pass's
  scope. Flagged, not silently dropped.
- A genuine live Sleeper round trip through the redesigned surfaces
  -- blocked on the same pre-existing `BLOCKED_EXTERNAL_TEST_FIXTURE`
  constraint documented in `NWR_PRE_UI_PRODUCT_STRUCTURE_FREEZE_V1.md`.
  Run `docs/codex/NWR_LIVE_SLEEPER_INSEASON_ACCEPTANCE_PROCEDURE.md`
  once a safe test league or explicit bounded owner authorization
  exists, and re-verify Home/Player Drawer's populated states against
  real data at that time.

## Final handoff

```
NWR_UI_FOUNDATION_V1
START HEAD: 9fa31975
FINAL HEAD: 698bf547
CURRENT UI AUDIT: nav not organized by the already-documented canonical
  task map, identity/freshness competing with page content, Home's
  actions lacked WHY/ALTERNATIVE/CONFIDENCE, drawer sections were
  stub headers with a leaked internal source code, a real drawer/
  window-chrome collision bug found+fixed live, Draft Room's dense
  visual language flagged out-of-scope, empty-state honesty pattern
  confirmed GOOD AS-IS and reused.
DESIGN DIRECTION: serious decision system, dark-first, restrained
  accents, color = status/urgency/recommendation only.
DESIGN SYSTEM: semantic state tokens + typography/spacing scale +
  new component classes, additive over the existing @nwr/ui token set,
  documented in NWR_UI_DESIGN_SYSTEM_V1.md.
LEAGUE SHELL: DONE -- canonical lifecycle-ordered nav, sidebar
  identity, one freshness indicator; AppShell changes additive/opt-in,
  Dynasty unaffected.
HOME: DONE -- THIS WEEK strip + up to 5 DecisionExplain action cards +
  "you're set for now" state, capped/prioritized display over
  already-existing data, zero new computation.
PLAYER DRAWER: DONE (visual foundation) -- header/Status-News/Opened-
  From/Advanced grammar; context-specific per-surface sections
  (This Week/ROS/Roster Fit/Market) remain a disclosed, real gap
  requiring new data plumbing, not fabricated.
DECISION EXPLANATION PATTERN: DONE -- DecisionExplain component,
  wired into Home, available for later adoption elsewhere.
RESPONSIVE: existing breakpoints reused, verified non-broken at
  1524/1024/900px; not independently re-architected this pass.
LIVE RENDER: PASS (local QA profiles; Home/Drawer populated states
  via disclosed synthetic client-side data, not a real Sleeper round
  trip -- see "Live render" section above)
SCREENSHOTS: captured interactively during this session (Chrome MCP
  tool results); not persisted to disk as files in this worktree.
ARCHITECTURE CHANGES: NONE
BACKEND/MODEL CHANGES: NONE
UI FOUNDATION FREEZE: CUT -- this document
  (docs/codex/NWR_UI_FOUNDATION_FREEZE_V1.md)
NEXT UI SURFACES: 1. Draft Room (bring its dense visual language onto
  this design system without regressing its live-draft density
  requirements). 2. Lineup/Waivers (adopt DecisionExplain for
  Start/Sit swaps and Add/Drop recommendations). 3. Trades/Players/
  League (apply the same card/status grammar; wire the Player
  Drawer's remaining context-specific sections once the underlying
  per-surface data exists).
READY TO EXPAND REDESIGN: YES
```
