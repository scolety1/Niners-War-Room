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
