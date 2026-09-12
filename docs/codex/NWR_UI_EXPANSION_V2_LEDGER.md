# NWR UI Expansion V2 -- Ledger

Multi-worker UI propagation effort, branch `ui/nwr-visual-redesign-v1-20260910`,
worktree `C:\NWR\ui-visual-redesign-v1`. Each worker owns exactly one surface,
reuses the frozen design system (`NWR_UI_DESIGN_SYSTEM_V1.md`,
`NWR_UI_FOUNDATION_FREEZE_V1.md`), and appends one entry here for the next
worker. Presentation-layer only on every entry -- no worker touches
`marginal_roster_utility_v2`, scoring, roster legality, `LeagueSnapshot`/
`LeagueWorkspaceContext`, the lifecycle resolver, `DecisionResultEnvelope`
semantics, `PlayerAvailabilityStatus` authority, or provider architecture.

## Work Unit 1 -- Lineup (2026-09-12)

**Start HEAD:** `aae72a75`. **Result:** PASS.

### Foundation verification (Work Unit 0)
Confirmed, not rebuilt: the nav active-route resolver fix (`03ce9cbb`) --
live-rendered, "LINEUP > Start / Sit" highlighted correctly while on the
`/league/:key/lineup` route. Shell (`ShellIdentity`/`FreshnessIndicator`),
Home's THIS WEEK strip + `DecisionExplain` action cards, and the universal
Player Drawer all still render and behave as documented. `npx tsc -b` and
`npx vitest run` both clean at the start head (216/216 after this pass's own
+8 new tests, 0 regressions -- 208 baseline per the prior session's own
ledger entry).

### What changed (Lineup surface)
- **`lineup-explain.ts`** (new): pure derivation for a Start/Sit swap card,
  mirroring `home-action-explain.ts`'s own START_SIT/START_SIT_CLOSE_CALL
  grammar exactly (WHY templates match verbatim in the shared, non-close-call
  case) so Lineup and Home read as one vocabulary. `explainLineupSwap` maps
  a real `WeeklyLineupSwap` + its post-swap `WeeklyLineupSlot` to headline /
  why / alternative / impact / confidence / tone / status -- no new scoring,
  every field traces to an already-computed backend value.
- **`in-season.tsx` (`LineupPage`)**: "Recommended changes" now renders each
  swap as a `DecisionExplain` card (STARTs are Lineup's own real "actual
  decision" -- the backend only emits a swap when its optimal starter
  differs from Sleeper's current one) instead of a bare `<ol>`. A confident
  swap gets `tone="recommended"` (green accent); a swap whose resulting
  slot is a genuine close call (`slot.closeCall`, the same signal Home's
  START_SIT_CLOSE_CALL card already reads) gets `tone="warning"` + a
  visible "LOW CONFIDENCE -- CLOSE CALL" badge -- so close calls are
  visually distinct from strong recommendations, not just a different
  badge string. Each card carries WHY / ALTERNATIVE (only when a real one
  exists) / EXPECTED IMPACT / STATUS / DATA (freshness) / a "View <player>"
  action into the existing global Player Drawer. The Starting Lineup grid's
  own close-call slot gets a matching left-border accent
  (`.tier-player-grid__article--close-call`, reusing the `--nwr-close-call`
  token) so a close call reads consistently whether it produced a swap or
  not. Uncontested starters/bench are untouched -- still plain, quiet cards.
- **`decision-explain.tsx`**: added one optional `status` prop (a
  StatusBadge fact row, additive -- Home's existing calls pass nothing and
  render byte-for-byte as before). Lets a card show a player's real
  health/availability status as a fact distinct from NWR's own
  recommendation confidence.
- **`redraft.css`**: `.tier-player-grid__article--close-call` (8 lines),
  reusing the existing `--nwr-close-call` token -- no new color invented.

### Real bugs found and fixed
1. **Ambiguous same-slotType matching (found before any live render, via
   backend code read)**: `WeeklyLineupSwap.slotType` is NOT a unique key --
   a roster can carry two starting slots of the same type (two WR slots,
   both `slotType: "WR"`). An initial `find(slot => slot.slotType ===
   swap.slotType)` would silently attach the WRONG slot's status/close-call
   data whenever a swap applied to the second slot of that type. Fixed by
   matching on `slotType` AND `player.playerName === swap.startPlayer` --
   confirmed exact and safe by reading `weekly_lineup_optimizer_service.
   _swap_reasons`, which builds `startPlayer` literally from that specific
   slot's player name. Covered by a dedicated regression test
   (`lineup-explain.test.ts`).
2. **Global Player Drawer had no Escape-to-close wiring at all** (found
   live, during this pass's own required interaction trial). Every other
   dismissible overlay in this app (Switch League menu, freshness popover)
   already closes on Escape; the drawer did not. Fixed in the shared
   primitive (`player-detail-drawer.tsx`) so every surface that opens this
   same drawer inherits the fix, not just Lineup.

### Trial matrix executed
**Viewport method (safety constraint):** `mcp__claude-in-chrome__resize_window`
was tested first and verified NOT to work in this sandbox -- requesting
1440x900 and 900x800 both left `window.innerWidth` fixed at 958 (confirmed
via a real `window.innerWidth`/`matchMedia` JS check, not assumed). This
matches a prior session's own recorded finding. Per the directive's
explicit fallback, real rendering was done at the one width the sandbox
actually renders (958px, real Chrome, real DOM) instead of fabricating
screenshots at widths that were never actually shown:
- **958px (real, rendered)**: sits between the app's `930px` (mobile
  off-canvas sidebar) and `1180px` (sidebar narrows to 218px) breakpoints,
  so it exercises the SAME CSS regime as a true `1180px` render (narrow
  inline sidebar) -- states A/B/C/D and the error state, plus all
  interaction trials, were run here with zero console errors and
  `scrollWidth === clientWidth` (no horizontal overflow) confirmed by JS,
  not eyeballed.
- **1440px**: code-level review only (real render not possible here). Above
  `1180px` so the sidebar returns to full width; Lineup's own layout
  (`.nwr-action-grid` is single-column by design, `.tier-player-grid` is
  `auto-fit, minmax(220px,1fr)`) only gains whitespace/columns, no new risk
  identified from reading the CSS.
- **900px**: NOT independently re-rendered -- true 900px additionally
  crosses the `930px` off-canvas-sidebar threshold that 958px does not, so
  it is a genuinely different regime from what was rendered. This pass's
  changes touch none of `.sidebar`/`.mobile-nav-trigger`, so the risk is
  assessed as low, but this is a real, disclosed gap, not a verified pass.

States A (populated, one confident + one close-call swap) / B (empty --
"Already optimal") / C (stale/degraded -- STALE badge, UNPROJECTED/EMPTY
slots, no undefined/NaN leaks) / D (long player/team/status/alternative
names -- headline and every fact wrapped cleanly, zero overflow) / ERROR
(weekly-lineup endpoint returns a typed error -- honest ErrorState banner,
prior good data stays visible) were all rendered and JS-verified (no
`undefined`/`NaN`/null-word leaks, no horizontal overflow, zero console
errors each state).

**Interaction trials**: 5 real Player Drawer open events across different
entry points (a Recommended-changes card, the Starting Lineup grid, the
Bench table) -- closed via the header X, via Escape (both before AND after
the fix above, to prove the regression and the repair), via mouse click,
via keyboard Enter, and via keyboard Space. Verified Tab-reachability
(`document.activeElement` checks, not assumed). Navigated Lineup ->
Weekly Home -> back to Lineup via the sidebar nav with zero console errors
each way.

### Data used
100% mocked, zero real network calls. No backend process was started at
all -- `window.fetch` was patched at the browser-console level (the same
mechanism the Foundation V1 pass used and disclosed) to serve
`/api/v1/bootstrap`, `/api/v1/redraft/weekly-lineup`,
`/api/v1/redraft/status-overrides`, and
`/api/v1/redraft/player-availability-status` from hand-written fixtures for
a synthetic `qa-lineup-1` profile; every other path returns a typed 404 so
nothing can hang. The owner's real Fantasy Gamers/403/Tester leagues and
AppData install were never touched or read.

### Tests
`lineup-explain.test.ts` (8 tests, new): confident swap, negative-delta sign
formatting, close-call tone/confidence/alternative, honest null-degradation
when no resulting slot is found, the never-fabricate-an-alternative-for-a-
confident-swap guard, and the same-slotType ambiguity regression.
`npx tsc -b apps/dynasty/tsconfig.json apps/redraft/tsconfig.json`: clean.
`npx vitest run --no-file-parallelism`: 216/216 passing (208 baseline + 8
new, 0 regressions).

### Backend/model files changed
NONE. `git diff --stat` from `aae72a75`: 4 files modified + 2 new, all under
`desktop/apps/redraft/src` -- `decision-explain.tsx`, `in-season.tsx`,
`player-detail-drawer.tsx`, `redraft.css`, `lineup-explain.ts` (new),
`lineup-explain.test.ts` (new).

### Open issues for the next worker
- **900px genuinely untested** (see above) -- if a future pass gets a
  working browser-native resize method in this sandbox, re-verify Lineup
  (and ideally every surface) at true 900px, specifically the off-canvas
  sidebar handoff.
- **1440px is code-review-only**, not rendered.
- Minor, pre-existing, NOT fixed this pass: a bench player's Player Drawer
  identity line reads "WR ·" with a trailing separator and no team, because
  `WeeklyLineupBenchPlayer`/the bench "View" action never had a team field
  to pass. Cosmetic, not overflow/undefined, and not introduced by this
  pass -- flagged rather than silently left, but out of this surface's
  narrow scope to plumb a new field through.
- The Escape-to-close fix lives in the shared `PlayerDetailDrawer`
  primitive, so it should already be visible on every other surface that
  opens this drawer (Waivers, Trade Analysis/Finder, Free Agents, Opponent
  Rosters, Players/Rankings/Tiers/Compare) -- worth a quick spot-check by
  whichever worker next touches one of those, since none of them were
  independently re-rendered this pass to confirm.
- Draft Room's own separate `PlayerDrawer` (draft-room-v2.tsx) is untouched,
  as before -- still a distinct, deliberately out-of-scope component.

## Work Unit 2 -- Improve Team (2026-09-12)

**Start HEAD:** `854d637b`. **Result:** COMPLETE (all 5 tabs).

### Foundation verification (Work Unit 0)
Confirmed, not rebuilt: the shared drawer Escape-to-close fix (Work Unit 1)
DOES apply here -- spot-checked live from three different Improve Team
entry points (Targets card, Streamers card, All Free Agents table) with
zero extra wiring needed, since every one of them calls the same
`usePlayerDetailOpener`/`PlayerDetailDrawer` primitive. `npx tsc -b` and
`npx vitest run` both clean at the start head (216/216, the exact count the
Work Unit 1 entry reported).

### What changed (Improve Team surface)
- **`improve-team-explain.ts`** (new): pure derivation, same family as
  `home-action-explain.ts`/`lineup-explain.ts`. `explainWaiverTarget` maps a
  real `WaiverAddCandidate` (+ its `WaiverAddDropPairing` if one exists, +
  mode, + a real next-best alternative candidate the caller supplies) to the
  directive's exact grammar: headline ("ADD X" or "ADD X / DROP Y"), WHY
  (the backend's own `marginalUtilityExplanation`), BID (`faabBidLowDollars`-
  `faabBidHighDollars` + urgency, honestly `null` when the backend supplied
  no estimate), THIS WEEK impact (only populated in THIS_WEEK mode -- never
  fabricated in REST_OF_SEASON), ROS impact (replacement value + marginal
  utility + net-vs-drop when a pairing exists), ALTERNATIVE (a real
  next-ranked candidate, never invented). `explainStreamerPlay` does the
  same for a `KdstStreamerRow`, reusing `home-action-explain.ts`'s own
  STREAMER why-text verbatim and mapping the real `recommendation` enum
  onto `DecisionExplain`'s existing tone vocabulary (`ALTERNATIVE` ->
  `tone="alternative"`, not a new one). 15 new unit tests.
- **`decision-explain.tsx`**: three new optional props (`bid`,
  `thisWeekImpact`, `rosImpact`), additive -- existing Home/Lineup call
  sites pass none of these and render byte-for-byte as before. Lets one
  card show a split week-vs-season impact plus a bid fact, per the
  directive's grammar, without inventing a second explanation component.
- **`improve-team.tsx`** (new): `ImproveTeamPage`, the single workspace
  replacing the old separately-built Waivers/Free Agents/K-DST Streamer
  pages in the nav. Tab state lives in a `?tab=` query param (shareable/
  deep-linkable), default `targets`. All 5 tabs implemented:
  - **TARGETS**: up to 10 capped `DecisionExplain` cards (mirrors Home's
    own "top N of M" capped-display pattern) over the real `WaiversResult`,
    each with a "View <player>" action into the global Player Drawer and an
    "Open in Add/Drop" action that switches tabs AND pre-selects that
    candidate in Add/Drop's own detail view -- a real cross-tab link, not
    two disconnected screens.
  - **ADD-DROP**: the full browse/pairing workflow (Available to add /
    Add-Drop pairings / Consider dropping + the existing `AddDropDetail`
    panel, now exported from `in-season.tsx` and reused here rather than
    rebuilt) -- the deep-comparison counterpart to Targets' curated top
    picks, both reading the SAME `WaiversResult`.
  - **FAAB**: budget-planning view -- 3 `MetricCard`s (remaining/weeks/
    per-week budget), the FAAB settings panel, and every real bid candidate
    as a `DecisionExplain` card sorted by the backend's own urgency signal,
    each carrying an urgency status badge via the existing
    `FAAB_URGENCY_TONE` mapping (no new tone invented).
  - **STREAMERS**: the top real K/DST recommendation per position as a
    `DecisionExplain` card (same visual language as Targets/FAAB, per the
    directive -- "not feel like a different app"), plus the full FantasyPros
    ECR comparison table below for a deep positional read. The original
    `WeeklyToolsPage` never had Player Drawer wiring at all (confirmed by
    reading it before assuming otherwise) -- this tab adds it new, via a
    synthetic `kdst-<position>-<playerName>` id (`KdstStreamerRow` carries
    no canonical id; this is an honest, disclosed synthetic identity, not a
    fabricated one -- see the code comment).
  - **ALL FREE AGENTS**: the browse/deep-search mode of the same workspace
    -- the existing `RedraftFreeAgentsResult` table plus a new client-side
    name/team search filter, one panel instead of a whole separate page.
  - `STREAMER_HORIZON_OPTIONS`/`_WEEKS`/`StreamerHorizon` exported from
    `pages.tsx` (was file-local) and reused rather than reimplemented.
- **`RedraftApp.tsx`**: `NAV_IMPROVE` collapsed from 3 nav items (Waivers/
  Free Agents/K-DST Streamer) to 1 ("Improve Team", reusing the existing
  `/waivers` path unchanged -- zero nav-active-route-resolver changes
  needed, see `league-context.ts`'s existing `ROUTE_ALIAS_SUBPATH.improve
  = "waivers"`/`NAV_LEGACY_PATH_SUBPATH["/waivers"] = "waivers"`, both left
  untouched and still correct). Both the `/league/:leagueKey/waivers` and
  `/league/:leagueKey/improve` scoped routes now render `ImproveTeamPage`
  instead of the old standalone `WaiversPage`. `WaiversPage`/`FreeAgentsPage`/
  `WeeklyToolsPage` themselves are untouched and still reachable at their
  own flat/scoped routes as harmless legacy fallbacks (no longer linked
  from nav) -- deliberately not deleted, in case a next pass wants to
  retire them outright.
- **`weekly-shared.tsx`**: Home's `ACTION_CATEGORY_LINK` for `WAIVER`/
  `STREAMER` now points into the unified workspace (`/waivers?tab=targets`,
  `/waivers?tab=streamers`) instead of the old separate pages.
- **`redraft.css`**: new `.nwr-tabbar`/`.nwr-tabbar__tab(--active)` (one
  small additive component, ~10 lines) -- the one genuinely new visual
  pattern this pass needed (a tab bar for one workspace's sections); every
  other visual choice inside each tab reuses existing `.nwr-explain`/
  `.panel`/`.metric-grid`/`.toolbar`/`.data-table-wrap` components
  unchanged.

### Real bugs found and fixed
1. **`player-detail-drawer.tsx`'s `SOURCE_LABEL` map had no `IMPROVE_TEAM`
   entry** (found before any live render, by reading the map against the
   new call site) -- without it, opening the drawer from ANY Improve Team
   tab would have shown "Opened from IMPROVE_TEAM" verbatim, the exact
   internal-language leak the Foundation pass's Phase 5 already fixed for
   every other surface. Added `IMPROVE_TEAM: "Improve Team"`.
2. **`LegacyRedirect` (RedraftApp.tsx) dropped the query string** on every
   flat-path compatibility redirect (found live, mid-trial, when a `?tab=`
   deep link silently landed on the default tab). `/waivers?tab=streamers`
   would resolve to `/league/<key>/waivers` with NO `tab` param at all,
   since the redirect built its target from `legacyRedirectTarget(...)`
   alone and never looked at `location.search`. This is what makes Home's
   own `ACTION_CATEGORY_LINK` `?tab=...` links (and any future flat link
   carrying a query string) actually work through the redirect. Fixed by
   appending `location.search` (already-imported `useLocation`, no new
   import needed).
3. **Streamers tab had zero Player Drawer wiring** -- not a regression (the
   original `WeeklyToolsPage` never had it either, confirmed by reading it
   first), but a real gap against this pass's own required interaction
   trial matrix ("Open Player Drawer from each tab ... Streamers"). Added
   a synthetic-id-based `View` action to both the card and the table (see
   above).

### Trial matrix executed
**Viewport method (safety constraint):** `mcp__claude-in-chrome__resize_window`
was tested first, requesting 1440x900 -- `window.innerWidth` stayed fixed
at 884 (confirmed via a real JS check, not assumed), consistent with the
Lineup pass's own recorded finding in a different sandbox session (958px
there). Per the directive's explicit fallback, real rendering was done at
the one width this sandbox's browser actually renders (**884px, real
Chrome, real DOM**) -- notably a NEW regime vs. Work Unit 1's 958px: 884px
sits BELOW the app's `930px` mobile-off-canvas-sidebar breakpoint, so this
pass's real render exercises the off-canvas sidebar (confirmed live --
sidebar opens as a scrim overlay, `.sidebar` width 244px, zero horizontal
overflow via `scrollWidth === innerWidth` JS check) that Work Unit 1
explicitly flagged as never independently verified.
- **884px (real, rendered)**: all 5 tabs, states A (populated)/B (empty)/C
  (stale weekly projections, THIS_WEEK mode only)/D (long league/player/
  team-name stress) plus the streamer-specific empty state and the
  no-free-agent state -- 8 distinct data scenarios in total, each
  JS-verified for `scrollWidth === innerWidth` (no horizontal overflow) and
  no `undefined`/`NaN` leaks, zero console errors on a clean baseline (see
  below for one transient, self-explained exception).
- **1440px / 1180px**: code-review only (real render not possible here).
  Every tab reuses existing, already-reviewed-safe responsive primitives
  unchanged (`.metric-grid` -- explicit `repeat(4,...)` -> `repeat(2,...)`
  at <=1180px; `.toolbar` -- `flex-wrap`; `.data-table-wrap` -- its own
  `overflow:auto` + `max-width:100%`, confirmed empirically at 884px that
  wide tables never breach the page; `.nwr-action-grid` -- single-column).
  The one new class this pass added, `.nwr-tabbar`, is a plain
  `flex-wrap` row with no fixed widths, and was confirmed live to fit on
  ONE line at 884px -- strictly more room exists at 1180/1440px, so no new
  risk identified from reading the CSS.
- **900px**: NOT independently re-rendered as a THIRD distinct width from
  884px -- both sit on the same side of the `930px` off-canvas threshold
  (below it), so 884px's real render already exercises the same CSS regime
  900px would. Disclosed as the same class of gap Work Unit 1 recorded for
  a width it could not reach, just inverted (this pass reached the
  narrow/mobile regime live; the two mid/wide regimes are code-review
  only).

States A/B/C/D were driven via a `window.__NWR_QA__` scenario switch
(`waiversScenario`/`streamerScenario`/`freeAgentsScenario` in
`{normal|empty|stale}`) read at mock-fetch time, so each state could be
exercised without re-injecting the whole fixture -- Targets/Add-Drop/FAAB
were each verified in both their populated and empty forms, Targets
additionally in THIS_WEEK mode (real "becomes starter" impact text) and in
the stale/degraded mode (STALE badge + ranking-unavailable alert strip,
both rendered correctly together).

### Interaction trials
Player Drawer opened from all 4 required entry points (Targets card,
Streamers card, Streamers table row, All Free Agents table row) plus
Add-Drop's own detail panel; closed via the header X, via Escape (a real,
live spot-check that Work Unit 1's shared-primitive fix benefits this
surface too, not assumed), and via keyboard (Tab to a "View" button, Enter
to open; Tab again moved focus correctly onto the next card's own action).
Reopening a different player while one was already open correctly replaced
it (toggle-to-different-player, not stacked). All 5 tabs were switched
between repeatedly (Targets -> Add/Drop -> FAAB -> Streamers -> All Free
Agents -> Targets) with the `?tab=` URL updating correctly each time and
zero console errors. Navigated Improve Team -> Weekly Home -> back to
Improve Team via real URL navigation with zero console errors and correct
remount-driven refetch (used deliberately to re-exercise the Free Agents
empty state, which has no manual refresh control of its own).

**One transient console error, explained and excluded from the final
count**: mid-session, while iterating on the Streamers tab's drawer-wiring
fix, Vite's Hot Module Replacement briefly threw
`ReferenceError: STREAMER_TABLE_COLUMNS is not defined` twice while
hot-swapping the edited module against a still-mounted component instance
-- a dev-server-only HMR artifact (confirmed by a subsequent hard
navigation + full reload immediately after, which produced a clean,
error-free boot and every trial below was re-run from that clean
baseline). This can only happen while editing source with the page open in
a dev server; it cannot occur in the shipped Tauri build (no HMR there)
and did not occur on any fresh load. Reported here for honesty rather than
silently omitted.

### Data used
100% mocked, zero real network calls, zero backend process started --
`window.fetch` patched at the browser-console level (the same mechanism
Work Unit 1 used and disclosed) for a synthetic `qa-improve-1` profile,
serving `/api/v1/bootstrap`, `/api/v1/redraft/waivers`,
`/api/v1/redraft/free-agents`, `/api/v1/redraft/kdst/streamer`,
`/api/v1/redraft/player-availability-status`,
`/api/v1/redraft/status-overrides`, `/api/v1/redraft/weekly-home-actions`
(a minimal stub, only for the Home round-trip nav check),
`/api/v1/redraft/opponent-rosters`, and `/api/v1/redraft/my-roster`; every
other path returns a typed 404 envelope so nothing can hang. The owner's
real Fantasy Gamers/403/Tester leagues and AppData install were never
touched or read.

### Tests
`improve-team-explain.test.ts` (15 tests, new): ADD/DROP headline
composition with and without a pairing, bid formatting and its honest
`null` case, THIS_WEEK vs REST_OF_SEASON impact (never fabricated in the
wrong mode), a real next-best alternative vs. the honest no-alternative
case, the generic-why fallback, and the full streamer-recommendation ->
tone/verb mapping including the ALTERNATIVE-to-`tone="alternative"` reuse.
`npx tsc -b apps/dynasty/tsconfig.json apps/redraft/tsconfig.json`: clean.
`npx vitest run --no-file-parallelism`: 231/231 passing (216 baseline + 15
new, 0 regressions).

### Backend/model files changed
NONE. `git diff --stat 854d637b HEAD -- src/`: empty. Full diff: 7 files
modified + 3 new, all under `desktop/apps/redraft/src` --
`RedraftApp.tsx`, `decision-explain.tsx`, `in-season.tsx`, `pages.tsx`,
`player-detail-drawer.tsx`, `redraft.css`, `weekly-shared.tsx` (modified);
`improve-team-explain.ts`, `improve-team-explain.test.ts`, `improve-team.tsx`
(new).

### Open issues for the next worker
- **900px genuinely untested as a distinct regime from 884px** (both sit
  below the same `930px` threshold) -- if a future pass gets a working
  browser-native resize method, re-verify Improve Team (and every other
  surface) at true 900px AND at a real 1180/1440px, since neither this
  pass nor Work Unit 1 has rendered the SAME width live.
  1440px/1180px here are code-review-only, same disclosed class of gap.
- **Minor, pre-existing, NOT fixed this pass** (found live, out of narrow
  scope): `AddDropDetail`'s FAAB recommendation paragraph
  (`{add.faabRationale}. Not a mathematically exact bid...`) double-periods
  whenever the backend's own `faabRationale` string already ends in a
  period (e.g. "Multiple teams likely bidding this week.." rendered
  live). Pure existing-code cosmetic formatting, not introduced by this
  pass, not overflow/undefined -- flagged rather than silently left, but
  out of this surface's scope to fix a shared string-formatting
  convention.
- `WaiversPage`/`FreeAgentsPage`/`WeeklyToolsPage` (the pre-consolidation
  pages) are still live code, reachable at their own flat/scoped routes,
  just no longer linked from anywhere in the app now that nav and Home
  both point into `ImproveTeamPage`. Deliberately left in place rather
  than deleted (lowest-risk choice for this pass); a future pass could
  retire them outright once confident nothing external depends on the old
  URLs.
- Streamers' synthetic `kdst-<position>-<playerName>` player-drawer id
  (see above) will never resolve a match against the real
  `PlayerAvailabilityStatus` authority even when a real status exists for
  that K/DST -- an honest, disclosed limitation of `KdstStreamerRow`
  carrying no canonical id, not something this presentation-only pass can
  fix (would need a real backend id added to that contract).
