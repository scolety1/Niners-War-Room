# Live Sleeper IN_SEASON Acceptance Procedure

**Status:** `BLOCKED_EXTERNAL_TEST_FIXTURE`. Written by the NWR pre-UI
product-architecture CLOSURE pass, part 3 (2026-09-10, directive section
4). Not executed this pass -- there is no safe, non-owner Sleeper league
available in this environment, and no explicit owner authorization to use
a real league exists for this pass. This document is the precise,
ready-to-run procedure for whenever one of those two things becomes true.
It intentionally reuses the same checklist shape the prior two passes'
rendered-acceptance sections already used (`PRODUCT_ARCHITECTURE.md`
section 12 / the "CLOSURE pass" section), so running it later is a
continuation, not a new methodology.

## Why this exists

Every architecture claim in `PRODUCT_ARCHITECTURE.md`, `LEAGUE_CONTEXT.md`,
`DATA_AUTHORITY.md`, and `DECISION_CONTRACTS.md` has been verified one of
three ways: (1) a pure-function/logic unit test (this repo's only test
infrastructure -- `desktop/vitest.config.ts` only collects `*.test.ts`,
never `*.test.tsx`, so there is no component-render test layer at all),
(2) a facade-level test with Sleeper mocked, or (3) a live, rendered Chrome
session against two **local QA profiles** (never a real Sleeper import).
Local QA profiles can reach PRE_DRAFT and (via `resolveLeagueLifecycle`'s
`drafted_count >= total_draft_picks` branch) a *simulated* IN_SEASON
classification, but they can never exercise:

- A real Sleeper roster/opponent-roster/free-agent READ (every in-season
  tool's actual live network call).
- The real `currentWeek`/week-control interplay with a live NFL calendar
  (there is no live calendar signal in this repo at all -- see
  `LEAGUE_CONTEXT.md`'s "Known, disclosed gap" -- so this procedure
  cannot and does not test that; it is a separate, already-disclosed,
  out-of-scope gap).
- The new-this-session Lineup/Waivers/Trade-Analysis/Trade-Finder/Free-
  Agents/Opponent-Rosters/Players "View" triggers opening the global
  Player Detail drawer against REAL player rows with REAL
  `PlayerAvailabilityStatus` entries (they render honestly-empty against
  a local QA profile, which has no real roster/opponent data at all).
- A real IN_SEASON landing (`leagues.tsx` -> `resolveLeagueHomeSubpath` ->
  Weekly Home) driven by a genuinely-completed live Sleeper draft rather
  than a locally-faked `drafted_count`.

## Preconditions before running this procedure

Exactly one of:

1. **A safe test league**: a Sleeper league created specifically for NWR
   testing (not any of the owner's real leagues -- see
   `docs/codex/nwr-real-local-install-location-and-schedule-finding.md`
   equivalent guidance in the operator's own memory), owned by an
   account the operator controls, with a completed or in-progress
   real draft so an IN_SEASON state is genuinely reachable.
2. **Explicit, recorded owner authorization** to use one of the owner's
   real leagues for a bounded, read-only verification pass -- the same
   authorization bar this repo's own history already requires for
   comparable actions (e.g. the governance-receipt renewal precedent in
   `DATA_AUTHORITY.md`).

Do NOT run this procedure against a real league without (2). Do NOT
fabricate either precondition.

## Environment setup (mirrors the prior passes' rendered-acceptance setup)

1. Confirm the target worktree's HEAD and that it is NOT the owner's real
   AppData install (`AppData\Local\com.ninerswarroom.redraft`) or the
   `main`/`draft-upgrade-hq` branches -- an isolated worktree only.
2. Start the backend against an isolated store:
   `python scripts/run_nwr_desktop_api.py --port 18742 --mode redraft
   --repo-root <worktree>`, with `NWR_REDRAFT_HOME` pointed at that
   worktree's own `local_exports/` (never the real AppData path). Verify
   live via `curl http://127.0.0.1:18742/healthz` before touching the
   browser.
3. Start the frontend: `npm run dev:redraft` (Vite, port 1422).
4. Load `mcp__claude-in-chrome` tools via `ToolSearch` if deferred.
5. Import (or select, if already present) the ONE safe test league /
   owner-authorized league. Do not import any other real league during
   this pass.

## Checklist (run in this order; record PASS/FAIL + evidence for each)

### A. Lifecycle + landing (real signals this time, not simulated)

- [ ] Opening the league from the chooser lands on the CORRECT workspace
  per `resolveLeagueLifecycle`'s real signals (Weekly Home for a
  genuinely-completed draft, Draft Room for a genuinely-incomplete one)
  -- confirms invariant A's real IN_SEASON case, the one thing the prior
  passes could NOT confirm live.
- [ ] `currentWeek` is confirmed still `null` on `LeagueWorkspaceContext`
  (the disclosed gap) -- every page's own week control is the real
  source of the displayed week, not a fabricated calendar value.

### B. Live data authorities (no console errors after each)

- [ ] Weekly Home (`redraftWeeklyHomeActions`) renders real actions
  from ONE `leagueSnapshotId` -- confirm the same id appears on the
  embedded `lineup` and is consistent if you separately open Start/Sit.
- [ ] Start/Sit renders real starters/bench from a genuine live Sleeper
  roster read, with real `providerHealth`.
- [ ] Waivers renders real add/drop candidates from a genuine live
  Sleeper roster + the governed ranking (confirm the ranking is NOT
  blocked in whatever environment runs this -- if it is, note the same
  governance-receipt class of gap `DATA_AUTHORITY.md` already discloses
  and treat that as a separate, pre-existing environment blocker, not a
  finding against this procedure).
- [ ] My Roster / Opponent Rosters render real live rosters.
- [ ] Free Agents renders real live free agents.

### C. Global Player Detail primitive against REAL rows (the actual new
### capability this procedure exists to verify)

For EACH of: Lineup, Waivers, Trade Analysis, Trade Finder, Free Agents,
Opponent Rosters, Players/Rankings, Players/Tiers, Players/Compare:

- [ ] Click "View" on a real player row. Confirm the SAME global drawer
  opens (not a second/competing drawer), showing real identity + a real
  `PlayerAvailabilityStatus` read (or an honest "no status issue"
  absence -- never a fabricated OK).
- [ ] Click "View" on a DIFFERENT player from the same or a different
  surface. Confirm the drawer's content replaces (never stacks).
- [ ] Click "View" on the SAME player again. Confirm the drawer closes
  (toggle-off).
- [ ] If any real player in this league carries a real
  `PlayerStatusOverride` (SEASON_OUT / NOT_WITH_TEAM /
  ADMINISTRATIVE_EXEMPT / TEAM_CORRECTION), confirm it renders
  IDENTICALLY (same tone, same label, same reason text) regardless of
  which surface's "View" opened it -- the actual cross-surface
  consistency claim (invariant E) this whole primitive exists to prove.

### D. PlayerAvailabilityStatus UI coverage in Draft/Trade Analysis/Trade
### Finder specifically (directive section 2, closed this pass on local
### QA profiles only -- this is the live confirmation)

- [ ] Draft Room's Suggestions table shows a "Status" badge for any
  candidate with a real status issue, and shows nothing for a candidate
  without one.
- [ ] Draft Room's own PlayerDrawer (NOT the global one -- Draft's is
  deliberately separate, see `DECISION_CONTRACTS.md`) shows the new
  "Availability" stat.
- [ ] Trade Analysis's impact table shows the "Availability" column for
  real give/receive players.
- [ ] Trade Finder's candidate cards show availability badges on both
  sides for real candidates.

### E. Context isolation with a SECOND real Sleeper league (if a second
### safe test league is available; skip with a note if only one exists)

- [ ] Switch from the test league to a second real Sleeper league via
  the header control. Confirm no stale roster/waiver/trade data from the
  first league is visible (the real bug this pass's predecessor found
  and fixed -- `PRODUCT_ARCHITECTURE.md`'s "Context isolation" section).
- [ ] Confirm a deep link to the non-active league activates and renders
  it correctly, including surviving a hard refresh (invariant H).

### F. Regression

- [ ] Zero new console errors across the whole session
  (`read_console_messages` after every navigation batch).
- [ ] `read_network_requests` shows every Sleeper/FantasyPros call
  carrying `writeBehavior: "NO_SLEEPER_WRITES"` (or the K/DST-specific
  variant) in its response -- confirms this procedure performed no
  writes back to Sleeper.

## Teardown

- Delete the isolated `local_exports/`/`NWR_REDRAFT_HOME` store created
  for this session.
- Stop the backend and frontend dev processes cleanly.
- Record the real PASS/FAIL result of every checklist item above (this
  document is the procedure; a SEPARATE dated report file records an
  actual run's results -- do not overwrite this procedure with results).
- Update `PRODUCT_ARCHITECTURE.md`'s invariant table and the structure
  freeze doc's "external caveat" line once this procedure has actually
  been run, replacing `BLOCKED_EXTERNAL_TEST_FIXTURE` with the real
  outcome.
