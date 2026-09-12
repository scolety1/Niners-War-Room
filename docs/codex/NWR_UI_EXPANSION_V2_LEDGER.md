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

## Work Unit 3 -- Trades (2026-09-12)

**Start HEAD:** `ce5c0d6e`. **Result:** COMPLETE (both tabs).

### Foundation verification (Work Unit 0)
Confirmed, not rebuilt: the shared drawer Escape-to-close fix (Work Unit 1)
applies here too -- live-verified from both the Analyze tab's impact-table
"View" action and Find Trades' candidate-card "View" actions, zero extra
wiring needed (same `usePlayerDetailOpener`/`PlayerDetailDrawer`
primitive). `LegacyRedirect`'s query-string preservation (Work Unit 2) is
what makes `ACTION_CATEGORY_LINK.TRADE`'s own `?tab=find` deep link work
through the `/trade-analysis` -> `/league/:key/trade-analysis` redirect --
confirmed live, not assumed. `npx tsc -b` and `npx vitest run` both clean
at the start head (231/231, the exact count Work Unit 2's entry reported).

### What changed (Trades surface)
- **`trades-explain.ts`** (new): pure derivation, same family as
  `lineup-explain.ts`/`improve-team-explain.ts`. `tradeVerdictFor` mirrors
  the pre-existing `verdictFor` (`in-season.tsx`) byte-for-byte for the
  same two real signals (`netMarginalUtility`, `rosValueDelta`) --
  deliberately duplicated rather than imported so this stays a pure,
  dependency-free module like its siblings (the same choice
  `explainStreamerPlay` already made for its own why-text). `IMPROVES MY
  ROSTER` / `CLOSE` / `HURTS MY ROSTER` are the only three verdicts, never
  a raw number. `explainTradeAnalysis` maps a real `TradeAnalysisResult` +
  the backend's own confirmed give/receive player names to the directive's
  exact grammar: eyebrow ("You give X / you receive Y"), headline (the
  verdict), WHY (a verdict-specific rationale sentence), WEEKLY IMPACT
  (starting lineup value before/after/delta), ROS IMPACT (net marginal
  utility + ROS value delta + a real championship-equity note only when
  supplied), DEPTH (bench contingency value before/after), POSITION EFFECT
  (starter holes + position redundancy before/after), and an honest
  `risk` (real backend `riskFlags`, `null` -- never a fabricated "no risk"
  -- when the backend records none). `explainTradeFinderCandidate` maps a
  real `TradeFinderCandidate` to "Send X for Y" / why-this-fits / a real
  NWR-roster-impact string built ONLY from `myNetMarginalUtility`/
  `myRosValueDelta`/`opponentNetMarginalUtility` -- no acceptance
  probability is computed or shown anywhere, because the backend supplies
  none (directive requirement, unit-tested explicitly). 17 new unit tests.
- **`decision-explain.tsx`**: three new optional props (`depth`,
  `positionEffect`, `risk`) and a new tone value, `"negative"` --
  additive/backward-compatible, existing Home/Lineup/Improve Team call
  sites pass none of these and render byte-for-byte as before. `negative`
  is a genuine fourth outcome no prior surface needed (Home/Lineup/Improve
  Team's cards are always NWR's own top pick; a trade the owner is
  evaluating can genuinely score as bad), mapped onto the design system's
  existing `--nwr-unavailable` token (crimson family) -- no new color
  invented, one new 3-line CSS rule (`redraft.css`).
- **`trades.tsx`** (new): `TradesPage`, the single workspace replacing the
  old separately-built Trade Analysis/Trade Finder pages in the nav. Tab
  state lives in a `?tab=` query param (`analyze` default, `find` for
  Find Trades), same pattern as Improve Team. Both tabs implemented:
  - **ANALYZE**: the same I-GIVE/I-RECEIVE `TradeSidePicker` workflow as
    the pre-existing page (now exported from `in-season.tsx` and reused
    here, not rebuilt), plus a single `DecisionExplain` verdict card
    rendering the directive's exact before/after grammar (eyebrow/
    headline/why/THIS WEEK/REST OF SEASON/DEPTH/POSITION EFFECT/RISK),
    followed by the existing metric-card row, the real per-player You
    Give/You Receive impact tables (Status/Availability badges + "View"
    into the global Player Drawer, unchanged from the pre-existing page),
    and the Position Redundancy panel. An honest "No trade analyzed yet"
    `EmptyState` covers the empty-builder state without a special case.
  - **FIND TRADES**: every real `TradeFinderCandidate` as a
    `DecisionExplain` card (mutual-improvement -> `tone="recommended"`,
    one-sided -> `tone="neutral"`, matching `explainTradeFinderCandidate`)
    with opponent/you-send/you-receive (status badge + "View" into the
    drawer for each side)/why-this-fits/NWR-roster-impact all present, and
    a real "Open in Analyze" cross-tab action that pre-selects both sides
    in Analyze's own picker state (no URL round trip, no auto-fetch --
    the owner still takes the deliberate "Analyze trade" action, mirroring
    Improve Team's own Targets -> Add/Drop jump).
  - Query-param prefill (`giveSleeperId`/`giveName`/`receiveSleeperId`/
    `receiveName`) is preserved unchanged from the pre-existing page, so
    My Roster's "Add to Trade Analysis" and Opponent Rosters' "Add to
    trade" links keep working against this new workspace without any
    change to those call sites.
- **`RedraftApp.tsx`**: `NAV_TRADES` collapsed from 2 nav items (Trade
  Analysis/Trade Finder) to 1 ("Trades", reusing the existing
  `/trade-analysis` path unchanged). All three scoped routes
  (`/league/:key/trade-analysis`, `/trades`, `/trade-finder`) now render
  `TradesPage` instead of the old standalone `TradeAnalysisPage`/
  `TradeFinderPage` (`trade-finder`'s own route passes `defaultTab="find"`
  so that specific URL still opens straight to Find Trades).
  `TradeAnalysisPage`/`TradeFinderPage`/`verdictFor`/`TradeSidePicker`
  themselves are untouched in `in-season.tsx` and still reachable at their
  own flat/scoped routes as harmless legacy fallbacks (`TradeSide`/
  `TradeSidePicker` gained `export` only, same precedent as
  `AddDropDetail` after Work Unit 2) -- deliberately not deleted.
- **`league-context.ts`**: added one `ROUTE_ALIAS_SUBPATH` entry
  (`"trade-finder": "trade-analysis"`) so the now-shared `/trade-finder`
  route still highlights the one "Trades" nav item instead of nothing --
  same reasoning as the pre-existing `improve` -> `waivers` alias. One new
  regression test in `league-context.test.ts`.
- **`weekly-shared.tsx`**: Home's `ACTION_CATEGORY_LINK.TRADE` now points
  at `/trade-analysis?tab=find` (the unified workspace's Find Trades tab)
  instead of the old standalone `/trade-finder` page.
- **`player-detail-drawer.tsx`**: added a `TRADES` entry to `SOURCE_LABEL`
  (found before any live render, by reading the map against the new call
  site) -- without it, opening the drawer from the new `TradesPage` would
  have shown "Opened from TRADES" verbatim, the same internal-language
  leak class Work Unit 2 fixed for `IMPROVE_TEAM`. `TRADE_ANALYSIS`/
  `TRADE_FINDER` stay mapped for the untouched legacy pages.

### Real bugs found and fixed
Both found before any live render, by reading against the new call site
(same discipline as Work Unit 2's own two pre-render catches):
1. **`player-detail-drawer.tsx`'s `SOURCE_LABEL` map had no `TRADES`
   entry** -- see above.
2. **The new `/trade-finder` scoped route would have resolved the nav
   active-state to nothing** once Trade Analysis/Trade Finder shared one
   nav item -- `resolveActiveNavPath` had no alias mapping `trade-finder`
   subpath back to the nav item's own `trade-analysis` subpath. Fixed via
   the `ROUTE_ALIAS_SUBPATH` entry above; live-confirmed (`Trades`
   highlights correctly on `/#/trade-finder`) and covered by a new
   regression test.

### Trial matrix executed
**Viewport method (safety constraint):** `mcp__claude-in-chrome__resize_window`
was tested first, requesting 1180x900 -- `window.innerWidth` stayed fixed
at **1424** (confirmed via a real JS check, not assumed) -- a THIRD
distinct value across this effort's three sessions (958px Work Unit 1,
884px Work Unit 2, 1424px here), confirming again that this tool does not
actually change the viewport in this sandbox. Per the directive's explicit
fallback, real rendering was done at the one width this sandbox's browser
actually renders (**1424px, real Chrome, real DOM**) -- notably the
OPPOSITE regime from both prior sessions: 1424px sits ABOVE the app's
`1180px` sidebar-narrowing breakpoint (full-width sidebar, the regime
neither Work Unit 1 nor 2 rendered live), so this pass is a genuinely new,
complementary real-render data point, not a repeat of the same regime.
- **1424px (real, rendered)**: states A (positive trade, green
  `IMPROVES MY ROSTER`) / B (negative trade, new crimson
  `HURTS MY ROSTER`) / C (close/ambiguous, gold `CLOSE`) / D (empty trade
  builder -- disabled Analyze button + honest "No trade analyzed yet"
  empty state) / E (Find Trades, zero candidates) / F (long
  player-name + long team-name + long risk-flag/championship-equity-note
  text stress, both tabs) were all rendered and JS-verified: zero console
  errors in every state, `document.documentElement.scrollWidth ===
  clientWidth` (no horizontal overflow) confirmed by JS across every
  state including the long-text stress state, no `undefined`/`NaN` leaks
  (checked via a body-text regex, not eyeballed).
- **1180px / 930px**: NOT independently re-rendered as distinct regimes --
  code-review only. `.nwr-explain__facts` (flex-wrap) and
  `.data-table-wrap` (its own `overflow:auto`) are the same
  already-reviewed-safe primitives Work Units 1/2 already exercised at
  narrower real widths; the two new optional `DecisionExplain` facts
  (`depth`/`positionEffect`) and the `risk` fact use the identical `<dt>/
  <dd>` markup as every existing fact, so no new narrow-width risk was
  identified from reading the CSS. This is the same disclosed class of
  gap both prior entries recorded, just inverted (this pass reached the
  wide/full-sidebar regime live; the narrow/mobile regimes are
  code-review only here).

### Interaction trials
Player Drawer opened from both required entry points (Analyze tab's
You-Give impact-table "View" action, Find Trades' candidate-card
you-send/you-receive "View" actions) -- closed via the header X, via
Escape (including a real keyboard-only open-then-close: `.focus()` +
`Enter` opened the drawer, `Escape` closed it, both verified via a real
`document.activeElement`/`.player-drawer` JS check, not assumed), reopened
a different player (correctly replaced, not stacked). Switched
Analyze/Find-Trades repeatedly with the `?tab=` URL updating correctly
each time and zero console errors. Navigated Trades -> Weekly Home -> back
to Trades via the sidebar nav (remount-driven state reset confirmed
correct, matching Work Unit 2's own documented Free-Agents-empty-state
precedent) and separately via `/trade-finder` and `/trade-analysis?tab=find`
direct hash navigation (both real regression-test targets above), all
zero console errors.

### Data used
100% mocked, zero real network calls, zero backend process started --
`window.fetch` patched at the browser-console level (the same mechanism
Work Units 1/2 used and disclosed) for a synthetic `qa-trades-1` profile,
serving `/api/v1/bootstrap`, `/api/v1/redraft/my-roster`,
`/api/v1/redraft/opponent-rosters`, `/api/v1/redraft/trade-analysis`
(echoing the real requested give/receive ids back as named players, with
a `window.__NWR_TRADES_QA__.scenario` switch driving the
positive/negative/close/long-names numeric response), `/api/v1/redraft/trade-finder`
(`findScenario` switch for normal/empty), and
`/api/v1/redraft/player-availability-status`; every other path returns a
typed 404 envelope so nothing can hang. The owner's real Fantasy Gamers/
403/Tester leagues and AppData install were never touched or read.

### Tests
`trades-explain.test.ts` (17 tests, new): all four verdict boundary
conditions (including a genuinely zero/tiny change reading as `Close`,
never a fabricated confident verdict), WEEKLY/ROS/DEPTH/POSITION EFFECT
formatting against real `TradeAnalysisResult` fixtures, the real
championship-equity-note append, the honest `risk: null` vs. real
joined-risk-flags cases, all three verdict-specific WHY strings, the
Find Trades headline/why/fits/tone mapping for both mutual and one-sided
candidates, and an explicit assertion that the impact string never
contains "probability" or "accept" (never fabricating an acceptance
signal). One new test in `league-context.test.ts` (the `trade-finder`
alias regression). `npx tsc -b apps/dynasty/tsconfig.json
apps/redraft/tsconfig.json`: clean. `npx vitest run
--no-file-parallelism`: 249/249 passing (231 baseline + 18 new, 0
regressions).

### Backend/model files changed
NONE. `git diff --stat ce5c0d6e HEAD -- src/`: empty. Full diff: 8 files
modified + 3 new, all under `desktop/apps/redraft/src` --
`RedraftApp.tsx`, `decision-explain.tsx`, `in-season.tsx`,
`league-context.test.ts`, `league-context.ts`, `player-detail-drawer.tsx`,
`redraft.css`, `weekly-shared.tsx` (modified); `trades-explain.ts`,
`trades-explain.test.ts`, `trades.tsx` (new).

### Open issues for the next worker
- **1180px/930px genuinely untested as distinct regimes** (see above) --
  if a future pass gets a working browser-native resize method, re-verify
  Trades (and ideally revisit every surface) at a real 1180px and 930px,
  since across all three Work Units so far no session has rendered the
  SAME width live as another.
- **Minor, pre-existing, NOT fixed this pass** (found live, out of narrow
  scope, inherited unchanged from the old `TradeAnalysisPage`): the You
  Give/You Receive impact tables have no client-side search/filter (not
  needed at typical 1-3-player trade sizes, but would matter for a very
  large multi-team/multi-player package) -- pure existing-code scope gap,
  not introduced by this pass.
- `TradeAnalysisPage`/`TradeFinderPage` (the pre-consolidation pages) are
  still live code in `in-season.tsx`, reachable at their own flat/scoped
  routes, just no longer linked from anywhere in the app now that nav and
  Home both point into `TradesPage`. Deliberately left in place rather
  than deleted (lowest-risk choice, same precedent as `WaiversPage`/
  `FreeAgentsPage`/`WeeklyToolsPage` after Work Unit 2).
- Per the directive's own scope boundary, Players and League were not
  attempted this pass -- Trades' full scope fit within this session, so
  no partial-completion handoff is needed here, but the next worker
  should still start from Players (not League) per the directive's stated
  order.

## Work Unit 4 -- Players (2026-09-12)

**Start HEAD:** `129a1231`. **Result:** COMPLETE (all 4 modes).

### Foundation verification (Work Unit 0)
Confirmed, not rebuilt: the shared drawer Escape-to-close fix (Work Unit 1)
applies here too -- live-verified from all three required entry points
(Rankings row action, Tiers grid card, Compare card) plus a fourth
(Market's new ADP-preview-row action, see below), zero extra wiring
needed. The nav active-route resolver fix (Work Unit 0) was ALREADY
correct for the pre-consolidation five-item Players nav (Rankings/Tiers &
Positions/Compare/Cheat Sheet/Market Data each already resolved to its own
nav item, confirmed by reading `resolveActiveNavPath`/`NAV_LEGACY_PATH_
SUBPATH` before changing anything) -- see "RANKINGS NAV BUG STATUS" below
for what this pass's OWN consolidation then required. `npx tsc -b` and
`npx vitest run` both clean at the start head (200/200 in `apps/redraft`
alone -- the exact scope this pass measures against; the prior three
entries' higher counts, up to 249, evidently included `apps/dynasty`
and/or a different test-runner scope not reproduced when running vitest
from `apps/redraft` directly).

### What changed (Players surface)
- **`players.tsx`** (new): `PlayersPage`, the single workspace replacing
  the previously separately-built Rankings / Tiers & Positions / Compare /
  Market Data pages in the nav. Tab state lives in a `?tab=` query param
  (shareable/deep-linkable), default `rankings`, same pattern as Improve
  Team/Trades. All four tabs render the exact same content the old
  standalone pages rendered (see the `pages.tsx`/`adp-providers.tsx` split
  below) under ONE shared `PageHeader`("Players") and ONE `.nwr-tabbar`
  (RANKINGS/TIERS/COMPARE/MARKET) instead of four separate page headers.
  Cheat Sheet is deliberately NOT a fifth tab here -- it stays its own
  separate nav item/page, per the directive's own SEARCH/RANKINGS/TIERS/
  COMPARE/MARKET-ADP scope list (Cheat Sheet was already unified
  separately, see the "Combined Cheat Sheet V1" memory entry) and per a
  fresh read of `cheat-sheet.tsx` confirming it is a genuinely distinct
  consumer surface (Ballers/NWR/Market blend for a draft-day sheet), not a
  fifth research mode of this one.
- **`pages.tsx`**: `RankingsPage`/`TiersPage`/`ComparePage` each split into
  an exported `*Content` function (no `PageHeader` of its own) plus a thin
  wrapper of the same original name that composes `PageHeader` +
  `*Content` -- same shape as `AddDropDetail`/`TradeSidePicker` being
  exported for reuse in prior passes. `RankingsContent`/`TiersContent`/
  `CompareContent` are what `PlayersPage` actually renders; `RankingsPage`/
  `TiersPage`/`ComparePage` themselves are kept as unrouted legacy
  fallbacks (same precedent as `WaiversPage` after Improve Team) -- no
  route in RedraftApp.tsx points to any of them any more. Zero behavior
  change to any of the three tabs' own logic (filters, Compare's 4 modes,
  Tiers' position rooms) -- this was a pure extraction, not a rewrite.
- **`adp-providers.tsx`**: same split -- `AdpProvidersPage`'s body became
  `MarketDataContent` (exported, no `PageHeader`), with `AdpProvidersPage`
  now a thin wrapper kept as an unrouted legacy fallback. Also: the ADP
  paste-preview table's "Matched NWR player" column had a real, matched
  player identity (`matchedNwrPlayerId`, a real backend field --
  `matched_nwr_player_id`, camelCased at the API boundary by
  `camel_case_key`/`public_json_value` in `src/application/contracts.py`,
  confirmed by reading the backend before assuming the casing) with NO
  Player Drawer wiring at all. Added a `View` action per matched row
  (looked up against the already-loaded governed rankings for
  position/team, same lookup shape `exportMarketAdpCsv` already used) --
  the directive's "all players clickable" requirement applies to Market's
  real player rows too, not just Rankings/Tiers/Compare.
- **`RedraftApp.tsx`**: `NAV_PLAYERS` collapsed from 5 items (Rankings/
  Tiers & Positions/Compare/Cheat Sheet/Market Data) to 2 (Players/Cheat
  Sheet) -- Cheat Sheet untouched, the other four merged into one
  "Players" nav item reusing the existing `/rankings` path unchanged (same
  precedent as Improve Team reusing `/waivers`, Trades reusing
  `/trade-analysis`). The five scoped routes (`rankings`/`players`/`tiers`/
  `compare`/`adp`) now all render `PlayersPage` (with `defaultTab` set for
  `tiers`/`compare`/`adp` so each flat URL still opens on its own mode,
  same `defaultTab` pattern Trades used for `/trade-finder`) instead of
  the four old standalone pages. `RankingsPage`/`TiersPage`/`ComparePage`/
  `AdpProvidersPage` are unrouted, not deleted.
- **`league-context.ts`**: added three `ROUTE_ALIAS_SUBPATH` entries
  (`tiers`/`compare`/`adp` -> `rankings`) so the now-shared `/tiers`,
  `/compare`, `/adp` routes still highlight the one "Players" nav item
  instead of nothing -- same reasoning as `improve` -> `waivers` and
  `trade-finder` -> `trade-analysis`.
- **`player-detail-drawer.tsx`**: added a `PLAYERS_MARKET` entry to
  `SOURCE_LABEL` (found before any live render, by reading the map against
  the new Market-tab call site) -- without it, opening the drawer from a
  matched ADP-preview row would have shown "Opened from PLAYERS_MARKET"
  verbatim, the same internal-language leak class fixed for
  `IMPROVE_TEAM`/`TRADES`. `PLAYERS_RANKINGS`/`PLAYERS_TIERS`/
  `PLAYERS_COMPARE` were already present from the earlier CLOSURE pass.

### RANKINGS NAV BUG STATUS
**Already fixed, verified, then a NEW variant introduced by this pass's
OWN consolidation was found and fixed in the same canonical resolver.**
Before touching anything, live-rendered `/rankings`, `/tiers`, `/compare`,
and `/adp` under the pre-existing five-item nav and confirmed each
correctly highlighted its OWN nav item (Rankings/Tiers & Positions/
Compare/Market Data), not Cheat Sheet or each other -- the Work Unit 0 fix
holds. Collapsing those four into one "Players" nav item then
NECESSARILY changed what "correct" means for `/tiers`/`/compare`/`/adp`
(they must now resolve to the ONE surviving "Players" item, not to
themselves) -- without the new `ROUTE_ALIAS_SUBPATH` entries above, all
three would have resolved to nothing (the exact bug class Work Unit 0
fixed, freshly reproduced by this pass's own nav change, not left over
from before it). Fixed in the ONE canonical resolver (`league-context.ts`),
not a per-page patch, and live-verified on a second synthetic league
profile: `/rankings`, `/tiers`, `/compare`, and `/adp` (with
`defaultTab="market"`) all correctly highlight "Players" and open their
intended tab. A pre-existing generic resolver test
(`resolveActiveNavPath > resolves Tiers, Compare, and Market (adp) each to
their own nav item`) asserted the PRE-consolidation behavior against a
fixture (`playersNavPaths`) that still lists four separate items -- since
`ROUTE_ALIAS_SUBPATH` aliases unconditionally (independent of which
navPaths list is passed, matching how `improve`/`trade-finder` already
worked), that specific assertion is now factually describing removed
product behavior; updated in place (title and expectations) with a
comment explaining why, rather than left to silently regress or deleted.
A second, new test exercises the REAL post-consolidation nav array
(`["/rankings", "/cheat-sheet"]`) directly.

### Trial matrix executed
**Viewport method (safety constraint):** `mcp__claude-in-chrome__resize_window`
was tested first, requesting 1440x900 -- `window.innerWidth` stayed fixed
at **1164** (confirmed via a real JS check, not assumed) -- a FOURTH
distinct value across this effort's four sessions (958px Work Unit 1,
884px Work Unit 2, 1424px Work Unit 3, 1164px here), reconfirming the tool
does not actually change the viewport in this sandbox. Per the directive's
explicit fallback, real rendering was done at the one width this
sandbox's browser actually renders (**1164px, real Chrome, real DOM**).
1164px sits between the `@nwr/ui` shell's own `930px` (off-canvas sidebar)
and `1180px` (sidebar narrows to 218px) breakpoints, so -- like Work Unit
1's 958px -- it exercises the narrow-inline-sidebar regime, NOT a new
regime relative to Work Unit 1, though it is a new real width relative to
Work Units 2 (884px, below 930px) and 3 (1424px, above 1180px).
- **1164px (real, rendered)**: states A (populated Rankings, 48 synthetic
  players across 6 positions) / B (populated Tiers) / C (populated
  Compare, all 4 modes exercised: Rest of Season, This Week, Roster Fit,
  Trade) / D (populated Market -- active ADP source, owner platform
  snapshot, Ballers panel, plus a live paste-preview round trip with a
  real matched row) / E (empty search -- "Christianeuxaviera..." typed
  into Rankings, 1 of 48 matched, verified live rather than assumed) / F
  (missing market data -- a SEPARATE synthetic league/bootstrap fixture
  with `adp.available:false` and no `ownerPlatformSnapshot`, since this is
  static bootstrap data rather than a live-togglable scenario switch; a
  full second page load, not a scenario flag) / G (long player name
  stress -- a real 76-character WR name baked into the main fixture,
  present across Rankings/Tiers/Compare/the Player Drawer) were all
  rendered and JS-verified: zero console errors across the entire session
  (checked cumulatively at the end, not just per-state), zero horizontal
  overflow (`document.documentElement.scrollWidth <= clientWidth + 1`)
  in every state including the long-name stress and the wide ADP-preview
  table (which scrolls inside its own `.draft-board-scroll` container, not
  the page), zero `undefined`/`NaN`/`[object Object]` leaks (checked via a
  body-text regex each time, not eyeballed), correct nav ("Players")
  highlighted for all four modes checked repeatedly.
- **1440px / 1180px / 900px / 720px**: code-review only (real render not
  possible here). `.nwr-tabbar` (Improve Team's pre-existing component,
  reused unchanged) already narrows its own margins at `720px`
  (redraft.css); `.tier-player-grid`/`.compare-card-grid`/`.metric-grid`/
  `.data-table-wrap` are the same already-reviewed-safe primitives prior
  Work Units exercised at other real widths. No new CSS was added by this
  pass beyond the Market tab's one new preview-table `<th>`/`<td>` pair,
  which reuses the existing `.draft-board-scroll` overflow container. This
  is the same disclosed class of gap every prior entry recorded -- no
  session in this effort has yet rendered the SAME width live as another,
  and 900px/1440px/1180px specifically remain unverified live for Players.

### Interaction trials
Player Drawer opened from FOUR entry points (Rankings row action, Tiers
grid card, Compare card, and the new Market ADP-preview-row action --
exceeding the directive's "at least 3 of 5" requirement) -- closed via the
header X (Tiers entry point) and via Escape (Rankings, Compare, and Market
entry points; a real `document.dispatchEvent(keydown Escape)` check each
time, not assumed), reopened a different player from a different tab
correctly (no stacking -- a fresh `.player-drawer` each time, verified by
reading its content, not just presence). Switched among all four tabs
repeatedly (Rankings -> Tiers -> Compare -> Market -> Rankings) with the
`?tab=` URL updating correctly and the correct tab/nav-item highlighted
every time. Used the real global command palette (Ctrl+K equivalent --
the "Search players or jump to a tool" trigger), typed a player name,
selected the real result, and confirmed it landed on `/rankings?player=
<id>` inside this unified workspace with the Rankings search box
pre-filled and the table correctly filtered to that one player -- the
directive's "global search should naturally lead into this area"
requirement, live-verified rather than assumed from the route shape
alone. Navigated Players -> Weekly Home -> back to Players via the
sidebar nav twice, each round trip resetting cleanly to the Rankings
default tab with zero console errors.

### Data used
100% mocked, zero real network calls, zero backend process started --
`window.fetch` patched at the browser-console level (the same mechanism
Work Units 1-3 used and disclosed), for TWO synthetic profiles across two
separate page loads (a full reload is required between them since this is
static bootstrap data, not a live scenario switch): `qa-players-1` (a
sleeper-provider, 48-player fixture across 6 positions plus the long-name
stress player, full ADP/owner-platform-snapshot/Ballers/marketProviderAdp
data, serving `/api/v1/bootstrap`, `/api/v1/redraft/my-roster`,
`/api/v1/redraft/waivers`, `/api/v1/redraft/weekly-projections`,
`/api/v1/redraft/player-availability-status`,
`/api/v1/redraft/status-overrides`, and (added mid-session)
`/api/v1/redraft/adp/*/paste/preview`) and `qa-players-2` (a local-
provider, 12-player fixture with `adp.available:false` and no
`ownerPlatformSnapshot`/`marketProviderAdp`/`udkRankings`, for the honest
missing-market-data state F); every other path returns a typed 404
envelope so nothing can hang. The owner's real Fantasy Gamers/403/Tester
leagues and AppData install were never touched or read. One real, disclosed
mock-authoring bug found and fixed mid-session (not a product bug): the
first fetch-patch draft assumed `input.url` would be set for a `URL`-typed
`fetch` argument (it is not -- only `Request` objects have `.url`; the
app's `request()` method passes a `URL`), which silently 404'd every
mocked call; fixed by branching on `input instanceof URL` before falling
back to `.url`.

### Tests
One test updated in place + one new test in `league-context.test.ts` (see
"RANKINGS NAV BUG STATUS" above for what changed and why): the pre-
existing "resolves Tiers, Compare, and Market (adp) each to their own nav
item" test now asserts the current, correct post-consolidation behavior
(all three resolve to `/rankings`) with a comment explaining the prior
behavior it replaces; a new test exercises the real, minimal
post-consolidation nav array directly. No new pure-logic module was
introduced for Players (unlike Lineup/Improve Team/Trades' own `*-explain.
ts` files) -- Players' tab-selection logic mirrors Improve Team's/Trades'
own `?tab=` resolution exactly and, consistent with that same precedent,
was verified via the live interaction trials above rather than a
duplicate isolated unit test. `npx tsc -b apps/dynasty/tsconfig.json
apps/redraft/tsconfig.json`: clean. `npx vitest run --no-file-parallelism`
(run from `apps/redraft`): 201/201 passing (200 baseline + 1 net new, 0
regressions -- see the Foundation-verification note above on why this
pass's own baseline count differs from prior entries' reported numbers).

### Backend/model files changed
NONE. `git diff --stat 129a1231 -- src/`: empty. Full diff: 6 files
modified + 1 new, all under `desktop/apps/redraft/src` -- `RedraftApp.tsx`,
`adp-providers.tsx`, `league-context.test.ts`, `league-context.ts`,
`pages.tsx`, `player-detail-drawer.tsx` (modified); `players.tsx` (new).

### Open issues for the next worker
- **900px/1180px/1440px/720px genuinely untested as distinct regimes for
  Players** (see Trial matrix above) -- if a future pass gets a working
  browser-native resize method, re-verify Players (and ideally revisit
  every surface) at each of those, since no session in this whole effort
  has yet rendered the SAME width live as another.
- **Market tab's ADP-preview `View` action is new, narrow-scope**: it only
  resolves for a row whose `matchedNwrPlayerId` matches an already-loaded
  ranking (the common case); an `OWNER_APPROVED`-matched row whose
  candidate came from `candidateSuggestions` (a different, not-yet-
  activated match) does not get a `View` action -- an honest, disclosed
  scope boundary (the directive's "all players clickable" reading applied
  to the table's OWN already-resolved matched identity, not every
  candidate suggestion nested inside a cell), not a bug.
- `RankingsPage`/`TiersPage`/`ComparePage`/`AdpProvidersPage` (the
  pre-consolidation pages) are still live source code but, unlike Improve
  Team's `FreeAgentsPage`/`WeeklyToolsPage`, NO route in `RedraftApp.tsx`
  points to any of these four any more (same as Trades' `TradeAnalysisPage`/
  `TradeFinderPage`) -- they are genuinely unrouted/unreachable from the
  app, kept only as source-level fallbacks per that same precedent.
- Per the directive's own scope boundary, League (and Draft Room) were not
  attempted this pass -- Players' full scope fit within this session, so
  no partial-completion handoff is needed here, but the next worker should
  proceed to League per the directive's stated order.

## Work Unit 5 -- League (2026-09-12)

**Start HEAD:** `8e314f8f`. **Result:** COMPLETE.

### Foundation verification (Work Unit 0)
Confirmed, not rebuilt: the shared drawer Escape-to-close fix (Work Unit 1)
applies here too -- live-verified from three real entry points (My Roster's
new `View` action, Teams'/Opponent Rosters' existing `View` action twice,
once per player, to prove reopen-a-different-player), zero extra wiring
needed. `npx tsc -b` and `npx vitest run` (apps/redraft alone) both clean at
the start head (215/215 -- 201 baseline the Players entry reported plus its
own +14, 0 regressions before this pass's own changes).

### What changed (League surface)
- **`league.tsx`** (new): `LeagueWorkspacePage`, the single workspace
  replacing the previously separately-built My Roster / Opponent Rosters /
  Profile & Scoring pages in the nav. Tab state lives in a `?tab=` query
  param (shareable/deep-linkable), default `overview`, same pattern as
  Players/Improve Team/Trades. Six tabs:
  - **OVERVIEW**: the directive's compact top-level summary (league name,
    my roster size, platform, team count, scoring format, current week,
    sync health) as one `.health-list` panel, with every provider/internal/
    debug detail (profile id, identity string, lifecycle basis, scoring/
    roster-state hashes, snapshot id, sync-as-of, raw issues) demoted into a
    collapsed `<details className="player-drawer__section">` disclosure --
    the exact reused progressive-disclosure pattern the design system
    already documents for the Player Drawer, not a new one-off component.
  - **MY ROSTER** / **TEAMS**: render the extracted `MyRosterContent`
    (in-season.tsx) / `OpponentRostersContent` (pages.tsx) directly -- see
    the real bug fix below for My Roster.
  - **SCORING**: a new, presentation-only read-only display
    (`scoringSummaryGroups`/`rosterCompositionRows`, league-summary.ts) of
    EVERY real scoring rule on the active profile grouped as Passing/
    Rushing/Receiving/Other/Bonuses -- including several fields
    (yards-per-point thresholds, first-down/return/fumble rules, bonuses)
    the existing roster/scoring EDIT form never exposed anywhere, read-only
    or otherwise. One "Edit in Settings" cross-tab jump button (same
    precedent as Improve Team's Targets -> Add/Drop and Trades' Find
    Trades -> Analyze).
  - **SETTINGS**: reuses `ProfileEditor` + `editableProfile` directly from
    `profile.tsx` (both gained `export` for this reuse) -- the exact same
    roster/scoring/draft-settings form and `client.updateRedraftProfile`/
    `client.duplicateRedraftProfile` contract calls `ProfilePage` already
    made, zero behavior change to the editor itself.
  - **SYNC**: combines the real `LeagueWorkspaceContext` (`currentWeek`/
    `syncStatus`/`syncAsOf`/`issues` -- see the real gap-closure below) with
    the real `LEAGUE_SYNC` category of the existing Data Health report
    (`client.redraftDataHealth()`, reused via a newly-`export`ed
    `dataHealthTone` from pages.tsx, not duplicated) and the real Sleeper
    "Refresh from Sleeper" resync action (`client.resyncSleeperRedraftProfile`,
    same call `ProfilePage` already made).
  - `ProfilePage` (multi-profile create/import/duplicate/switch/Practical
    Mock flow) is DELIBERATELY NOT folded in here -- it answers "manage MY
    LEAGUES" (plural), a genuinely different question from this workspace's
    "what is THIS league" (singular). It stays reachable at its own nav
    item, relabeled "Manage Leagues" (path `/profile` unchanged). "Data
    Health" also stays separate -- a genuinely broader whole-system
    diagnostic (weekly/ROS projections, market ADP, player status, decision
    engine, snapshot), not specific to this one league; only its real
    `LEAGUE_SYNC` category is reused (see SYNC above). Both choices are the
    same "keep a genuinely distinct surface separate" precedent Players used
    for Cheat Sheet.
- **`league-summary.ts`** (new): pure derivation, same family as
  `lineup-explain.ts`/`improve-team-explain.ts`/`trades-explain.ts` --
  `syncHealthTone`/`syncHealthLabel` (LIVE/DEGRADED/NOT_APPLICABLE ->
  safe/review/offline), `formatCurrentWeek` (honest "Not available" for
  `null`, never a fabricated week), `scoringSummaryGroups`,
  `rosterCompositionRows` (omits zero-count Superflex/K/DST slots rather
  than showing a confusing "0"). 13 new unit tests
  (`league-summary.test.ts`).
- **`in-season.tsx`**: `MyRosterPage` split into an exported
  `MyRosterContent` (no `PageHeader`) + a thin wrapper of the same name kept
  as an unrouted legacy fallback -- same shape as every prior consolidation.
  See the real bug fix below for what else changed here.
- **`pages.tsx`**: `OpponentRostersPage` split the same way into
  `OpponentRostersContent` + a thin wrapper; `dataHealthTone` gained
  `export` for SYNC-tab reuse.
- **`profile.tsx`**: `editableProfile`/`EditableProfile`/`ProfileEditor`
  gained `export` for SETTINGS-tab reuse. `ProfilePage` itself is otherwise
  completely unchanged.
- **`RedraftApp.tsx`**: `NAV_LEAGUE` collapsed from 4 items (My Roster/
  Opponent Rosters/Profile & Scoring/Data Health) to 3 (League/Manage
  Leagues/Data Health) -- My Roster and Opponent Rosters merged into the
  one new "League" item, reusing the existing `/my-roster` path unchanged
  (same precedent as Improve Team reusing `/waivers`) and inheriting the
  `shortcut: "4"` the old "Profile & Scoring" item carried. The
  `/league/:leagueKey/my-roster`, `/league/:leagueKey/league` (the
  canonical task-map alias -- previously a placeholder rendering
  `MyRosterPage`, now the real thing), and `/league/:leagueKey/opponent-rosters`
  scoped routes all now render `LeagueWorkspacePage` (with `defaultTab`
  `"roster"`/unset-`"overview"`/`"teams"` respectively) instead of the old
  standalone pages. `MyRosterPage`/`OpponentRostersPage` are unrouted, not
  deleted (same precedent as `RankingsPage`/`TiersPage`/`ComparePage`/
  `AdpProvidersPage` after Players).
- **`league-context.ts`**: added one `ROUTE_ALIAS_SUBPATH` entry
  (`"opponent-rosters": "my-roster"`) so `/league/:key/opponent-rosters`
  still highlights the one "League" nav item instead of nothing -- same
  reasoning as every prior alias (`improve`/`trade-finder`/`tiers`/
  `compare`/`adp`). One new regression test in `league-context.test.ts`
  exercising the real post-consolidation League nav array.
- **`player-detail-drawer.tsx`**: added a `MY_ROSTER` entry to
  `SOURCE_LABEL` (found before any live render, by reading the map against
  the new call site) -- see the real bug fix below.
- **`redraft.css`**: `.league-scoring-groups`/`.league-scoring-group h3`
  (2 rules, ~4 lines) for the Scoring tab's grouped layout -- the one
  genuinely new visual pattern this pass needed; every other choice reuses
  `.panel`/`.health-list`/`.player-drawer__section`/`.nwr-tabbar` unchanged.

### Real bugs found and fixed
1. **My Roster had NO Player Drawer wiring at all** (found before any live
   render, by reading `MyRosterPage` against the directive's "players
   clickable -> Player Drawer" requirement) -- unlike every other roster/
   table surface already adopted (Opponent Rosters, Free Agents, Rankings,
   ...), confirmed by reading the pre-existing component rather than
   assuming otherwise. Fixed by adding the same global
   `usePlayerDetailOpener`/`appendPlayerDetailColumn` primitive, alongside
   (not instead of) the existing "Add to Trade Analysis" link -- live-
   verified: opens, shows "OPENED FROM MY ROSTER" (not a raw source-code
   leak, since the matching `SOURCE_LABEL` entry was added in the same
   pass), closes via X/Escape, reopens a different player cleanly.
2. **`LeagueWorkspaceContext` (`currentWeek`/`syncStatus`/`syncAsOf`/
   `issues`) was fetched by NO frontend surface anywhere** (confirmed by a
   whole-repo search before writing `league-summary.ts`) despite the client
   method (`redraftLeagueWorkspaceContext`) and full contract type already
   existing -- the same class of "real backend field, never surfaced"
   finding the Players pass made for the ADP-preview `View` action. Closed
   by wiring it into OVERVIEW's "Current week"/"Sync health" facts and the
   new SYNC tab, read-only, its semantics untouched (this pass's hard
   boundary).
3. **`player-detail-drawer.tsx`'s `SOURCE_LABEL` map had no `MY_ROSTER`
   entry** -- see bug 1. Found before any live render, by reading the map
   against the new call site (same discipline as every prior pass's own
   pre-render `SOURCE_LABEL` catches).

### Trial matrix executed
**Viewport method (safety constraint):** `mcp__claude-in-chrome__resize_window`
was tested first, requesting 1180x900 -- `window.innerWidth` stayed fixed at
**1424** (confirmed via a real JS check, not assumed, both before AND after
the resize call, which reported "success" but changed nothing real) --
matching Work Unit 3's own recorded value exactly (a plausible same-display
coincidence across sessions, not a claim the tool works). Per the
directive's explicit fallback, real rendering was done at the one width
this sandbox's browser actually renders (**1424px, real Chrome, real DOM**,
via a real local Vite dev server + a real fetch-mock, no backend process
started).
- **1424px (real, rendered)**: states A (My Roster populated -- 3 players,
  one a real 55-character WR name, MATCHED/UNMATCHED identity badges both
  present) / B (Teams -- 2 real opponent rosters, one a 68-character team
  name, one genuinely empty with an honest "No rows match this view" and an
  unresolved-Sleeper-id note) / C (Scoring -- all 5 rule groups incl.
  Bonuses, honest singular "1 pt"/"None" TE-premium formatting) / D
  (Settings -- the full roster/scoring/draft editor, a real `Save & refresh
  rankings` round trip against the mock `updateRedraftProfile` endpoint,
  confirmed via the real "Scoring, roster, and draft settings saved..."
  feedback string) / E (Sync -- healthy: LIVE badge, real `Refresh from
  Sleeper` round trip confirmed via its own real feedback string) / F (Sync
  -- stale/degraded: toggled a `window.__NWR_LEAGUE_QA__.sync = "degraded"`
  QA flag and remounted the Sync tab by switching away and back -- both the
  Connection & Sync panel AND the League Sync Detail panel independently
  showed DEGRADED, with real degradation-reason/issue text, and the
  Overview tab's own Sync-health fact updated to "Degraded" on its own next
  mount) / G (long league name AND long player/team names baked into every
  fixture simultaneously, present across every tab and the sidebar identity
  block, the page title, and the Player Drawer) were all rendered and
  verified: zero console errors across the entire session (checked
  cumulatively, not just per-state -- only Vite HMR/React-DevTools debug/
  info lines appeared, no errors or warnings), `document.documentElement.
  scrollWidth === clientWidth` (no horizontal overflow) confirmed by JS in
  every state including the long-name stress state, correct "League" nav
  highlighting throughout, real Save/Duplicate/Resync round trips exercised
  against the mock (not just rendered idle).
- **1440px / 1180px / 900px**: code-review only (real render not possible
  here). `.health-list` (dt/dd flex row), `.nwr-tabbar` (flex-wrap),
  `.profile-edit-grid` (the pre-existing Settings editor, unchanged), and
  the two new `.league-scoring-groups` rules (`repeat(auto-fit,
  minmax(200px,1fr))`, no fixed widths) are the same already-reviewed-safe
  primitives every prior Work Unit exercised at other real widths; no new
  narrow-width risk identified from reading the CSS. Same disclosed class
  of gap every prior entry recorded -- no session in this whole effort has
  yet rendered the SAME width live as another (958/884/1424/1164/1424px
  across five sessions).

### Interaction trials
Player Drawer opened from My Roster (`View`, the new wiring) and from Teams/
Opponent Rosters (`View`, twice -- Opponent Star Player then Opponent Bench
Guy, from the SAME panel, to prove reopening a different player replaces
rather than stacks: `document.querySelectorAll('.player-drawer').length`
stayed 1 throughout); closed via the header X (Teams entry point) and via
Escape (My Roster entry point, and again after the keyboard-only open
below); a real keyboard-only round trip (`button.focus()` + `Enter` opened
it, confirmed via `document.activeElement`/`.player-drawer` presence, not
assumed). Switched among all six League tabs repeatedly (Overview -> My
Roster -> Teams -> Scoring -> Settings -> Sync -> Overview) with the
`?tab=` URL updating correctly and the correct tab highlighted every time,
plus a real cross-tab jump (Scoring's "Edit in Settings" button ->
`?tab=settings`). Navigated League -> Weekly Home (via the sidebar nav) ->
back to League (via a second click on the "League" nav item, landing on
`/my-roster`'s own default "My Roster" tab) with zero console errors each
way. Separately verified the legacy `/opponent-rosters` flat path resolves
to the League workspace's Teams tab AND correctly highlights the "League"
nav item (the alias fix, live-confirmed, not just unit-tested). Regression-
spot-checked "Manage Leagues" (`/profile`, unchanged `ProfilePage`, still
shows the real active profile/create-preset/import-Sleeper/Practical-Mock
panels) and "Data Health" (`/data-health`, unchanged `DataHealthPage`) --
both still render correctly and highlight their own nav items, confirming
the nav consolidation did not strand either surface.

### Data used
100% mocked, zero real network calls, zero backend process started --
`window.fetch` patched at the browser-console level (the same mechanism
Work Units 1-4 used and disclosed, including the Players pass's `input
instanceof URL` fix, reused here since this app's `request()` always calls
`fetch(new URL(...), ...)`) for one synthetic `qa-league-1` profile serving
`/api/v1/bootstrap`, `/api/v1/redraft/my-roster`,
`/api/v1/redraft/opponent-rosters`, `/api/v1/redraft/league-workspace-context`
(a `window.__NWR_LEAGUE_QA__.sync` flag switches its `syncStatus`/`syncAsOf`/
`issues` between LIVE/DEGRADED on the NEXT mount, no reload needed since tab
switching already unmounts/remounts each tab's content), `/api/v1/redraft/data-health`
(same flag drives its `LEAGUE_SYNC` category), `/api/v1/redraft/player-availability-status`,
and the three real profile-mutation endpoints (`.../edit`, `.../duplicate`,
`.../sleeper-resync`, each echoing a real merged/updated profile back
through the same `RedraftBootstrap` shape the real backend returns); every
other path returns a typed 404 envelope so nothing can hang. The owner's
real Fantasy Gamers/403/Tester leagues and AppData install were never
touched or read.

### Tests
`league-summary.test.ts` (13 tests, new): sync-status tone/label mapping
for all three real `syncStatus` values, honest `null`-week formatting,
scoring-group composition (incl. the honest "None" TE-premium case and the
real bonus-append case), and the honest zero-count Superflex/K/DST omission
in roster composition. One new test in `league-context.test.ts` (the
`opponent-rosters` alias regression, exercised against the real
post-consolidation League nav array). `npx tsc -b apps/dynasty/tsconfig.json
apps/redraft/tsconfig.json`: clean. `npx vitest run --no-file-parallelism`
run from the MONOREPO ROOT (`desktop/`, both apps, per this pass's own
directive): **264/264 passing**. Run from `apps/redraft` alone: **215/215**
(201 baseline the Players entry reported + 14 new [13 + 1], 0 regressions).
This directly reconciles the 201-vs-249 discrepancy the Players entry
flagged: the monorepo-root run includes `apps/dynasty` (264 − 215 = 49
Dynasty tests) in addition to Redraft's own suite -- confirmed empirically
by running both scopes back to back in this session, not inferred. Every
prior entry's "249" (Trades) and similar higher counts were very likely
monorepo-root runs; Players' "201"/"200" was a `apps/redraft`-scoped run.
Both scopes are internally consistent; there is no real regression hiding
in the gap.

### Backend/model files changed
NONE. `git diff --stat 8e314f8f -- src/`: empty. Full diff: 8 files
modified + 3 new, all under `desktop/apps/redraft/src` -- `RedraftApp.tsx`,
`in-season.tsx`, `league-context.test.ts`, `league-context.ts`, `pages.tsx`,
`player-detail-drawer.tsx`, `profile.tsx`, `redraft.css` (modified);
`league-summary.ts`, `league-summary.test.ts`, `league.tsx` (new).

### Open issues for the next worker
- **No real "my team name" field exists anywhere in the contracts**
  (`LeagueProfile`, `LeagueWorkspaceContext`, `RedraftMyRosterResult` all
  lack one) for a Sleeper-sourced roster -- confirmed by reading every
  candidate type before designing the Overview summary. Rather than
  fabricate one, OVERVIEW's "My roster" fact honestly shows the rostered-
  player COUNT once loaded (or "Not tracked for a Local/ESPN profile") --
  a disclosed, real contract gap, not a bug this presentation-only pass can
  close (would need a new backend field).
- **900px/1180px/1440px genuinely untested as distinct regimes for
  League** (see Trial matrix above) -- same disclosed class of gap every
  prior entry recorded; no session across all five Work Units has yet
  rendered the SAME width live as another.
- `MyRosterPage`/`OpponentRostersPage` (the pre-consolidation pages) are
  still live source code but, like Trades'/Players' own predecessors, NO
  route in `RedraftApp.tsx` points to either any more -- genuinely
  unrouted/unreachable from the app, kept only as source-level fallbacks
  per that same precedent.
- Per the directive's own hard boundary, this pass never wrote to
  `LeagueWorkspaceContext` or changed its semantics -- only read it
  (a new, additive frontend consumer of an already-existing, previously-
  unused backend contract/endpoint).
- Per the directive's explicit instruction, Draft Room was NOT attempted
  by this pass. With League now complete, every UI-expansion surface named
  in this effort (Lineup, Improve Team, Trades, Players, League) is done;
  Draft Room remains the one deliberately-separate, differently-owned
  surface for a future pass.
