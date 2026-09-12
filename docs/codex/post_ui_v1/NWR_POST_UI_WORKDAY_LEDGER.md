# NWR Post-UI Workday Ledger

Multi-worker unattended implementation shift on the NWR desktop frontend,
branch `upgrade/nwr-post-ui-product-v1-20260912`, worktree
`C:\NWR\post-ui-product-v1`. Each worker appends its own entry below. Durable
tracking doc for the next workers -- keep entries concise, not narrative.

No merge/push/deploy by any worker. No push to origin without explicit
owner authorization (none exists for this shift).

---

## CURRENT HEAD

Four commits on top of start head `003d0dd4183f7bfc7a2ad2f03960c967dd0bb02e`
(Work Unit 0 + P0-1, then P0-2, then P0-3, then P1-1 below) -- run
`git log -1` for the exact hash.

## P1-1 (automatic NFL week + matchup/standings/playoff context) -- 2026-09-12

**Gap confirmed exactly as Worker 3 flagged, then closed.** Verified fresh
(not assumed): `redraft_league_workspace_context`
(`src/application/desktop_facade.py`) hardcoded `current_week=None` on
every call, and `league_lifecycle_service.py`'s own module docstring
already disclosed "no wrapper around Sleeper's `GET /v1/state/nfl` or
equivalent exists anywhere in `src/services`". Weekly Home's `NFL WEEK`
field was a bare `useState(1)`, never wired to anything real. Both are
now fixed: `src/services/sleeper_league_context_service.py` (new) wraps
Sleeper's real `state/nfl`, per-week `matchups`, `rosters` (`settings`
wins/losses/points), `league` (status/playoff settings), and
`winners_bracket` endpoints as pure functions over already-fetched JSON;
`desktop_facade.py`'s `redraft_league_workspace_context` performs the
actual (try/except-guarded, never-crashing) reads and threads the results
through three new additive fields on `LeagueWorkspaceContext`:
`matchup`, `standings`, `playoff` (frozen-dataclass fields with real
defaults, `to_dict()`/`build_league_workspace_context()` extended --
every OTHER existing field/semantic on `LeagueWorkspaceContext` and the
lifecycle resolver were read-only, untouched, per the hard boundary).

**Raw facts only, honestly disclosed as such:** every field is `None`/
empty when Sleeper doesn't directly report it (non-Sleeper provider, a
failed HTTP read, a bye week, an unresolvable opponent, no bracket
generated yet) -- nothing is inferred, estimated, or simulated. The one
derived boolean (`playoff.inPlayoffs`) is a plain
`currentWeek >= playoffWeekStart` comparison over two raw provider
integers, not a prediction; no Championship Equity, no simulated playoff
odds were built (explicitly out of scope per the directive).

**Frontend:** `LeagueWorkspaceContext` contract gains `matchup`/
`standings`/`playoff` (additive-only; `packages/contracts/src/index.ts`).
Weekly Home (`in-season.tsx`) now fetches the context via a new shared
`useLeagueWorkspaceContext` hook (`weekly-shared.tsx`) and:
- Defaults its week to `context.currentWeek` (provider) with the existing
  `WeekControl` demoted to an explicit, clearly-labeled FALLBACK
  ("NFL week (auto)" vs "NFL week (manual)", with a "Use current week
  (N)" reset action) -- manual entry no longer wins by default.
- Resets that manual override on every league switch (`useEffect` keyed
  on `data.activeProfileId`) so no override leaks between leagues.
- Shows opponent/score (explicitly labeled "(Wk N)" -- the PROVIDER's
  real current week, independent of a manually browsed projections
  week, so the two numbers are never conflated), the owner's record/
  rank, a real Sleeper standings table, and (only once the league has
  actually reached its playoff weeks -- Sleeper pre-seeds an empty
  bracket skeleton months early, which would otherwise be a confusing,
  premature "Playoff round 2: opponent not yet determined" during Week
  1) the owner's real bracket matchup or a plain "Playoffs start Week N"
  otherwise.
- All new pure derivation (`ownerStandingsRow`, `formatRecord`,
  `formatStandingsRank`, `matchupStatusText`, `describeOwnerBracketEntry`,
  `playoffStatusText`) lives in `league-summary.ts`, unit-tested in
  `league-summary.test.ts` (same file/pattern the prior League-surface
  pass already established for `formatCurrentWeek`).
- Added one small, disclosed routing fix found along the way: the new
  Standings panel's "Open League" link needed a `/league` legacy-redirect
  route (`RedraftApp.tsx`) -- every other bare-path link in this file
  already had one, `/league` simply hadn't been added yet (no prior
  surface linked there).

**Verification:**
- New backend unit tests: `tests/test_sleeper_league_context_service.py`
  (19 tests, pure functions -- parse-week, team-name resolution, matchup
  bye-week/unavailable/opponent-unresolvable, standings sort/rank,
  playoff non-playoff/playoff/malformed-input cases).
- New backend facade-wiring tests (mocked Sleeper, same pattern as
  `test_desktop_facade_architecture_wiring.py`'s existing KDST test):
  `tests/test_league_workspace_context_sleeper_p1_1.py` (6 tests --
  current-week-populated, bye-week, playoff-state-with-bracket,
  provider-unavailable/OSError fallback, local/non-Sleeper honest
  "not automatically sourced", and a real league-SWITCH test asserting
  League A's matchup/standings never appear in League B's context).
- New frontend unit tests appended to `league-summary.test.ts` (10
  tests covering the same edge cases as the backend, at the display
  layer).
- `pytest tests/test_sleeper_league_context_service.py
  tests/test_league_workspace_context_sleeper_p1_1.py
  tests/test_league_workspace_context_service.py
  tests/test_desktop_facade_architecture_wiring.py
  tests/test_desktop_application_api.py`: 86 passed, 4 failed -- the
  SAME 4 pre-existing `test_desktop_application_api.py` failures P0-2
  already documented (confirmed via an A/B `git stash` comparison
  showing identical failures before/after this pass's changes); zero
  new failures.
- `npx tsc -b apps/dynasty/tsconfig.json apps/redraft/tsconfig.json`:
  clean.
- `npx vitest run --no-file-parallelism`: **296/296 passing, 25/25
  files** (286 baseline from Worker 1 + 10 new).
- **Real, live-rendered confirmation (real Sleeper, not a fixture):**
  used `desktop/scripts/nwr_release_gate_smoke.ps1 -KeepRunning
  -SleeperLeagueId 1312983576827920384 -SleeperUsername scolety`
  (Worker 3's own release-gate script, unmodified) to stand up the real
  backend + a real production `vite build`/`vite preview`, then drove it
  live in Chrome (read-only, real "Fantasy Gamers" league). Confirmed:
  `currentWeek: 1` (real, non-hardcoded), a real live matchup ("Brown
  Town & Big Mike" vs "Puka's Bitches", 6.0-25.4), a real 10-row
  standings table (owner correctly bolded, ranked #9), "Playoffs start
  Week 15." (real settings, correctly NOT showing the pre-seeded bracket
  skeleton in Week 1), the manual-override fallback control working
  exactly as designed (auto->manual->reset-to-auto, verified by
  screenshot at each step), and the new `/league` route. Zero console
  errors (verified with console tracking armed across two separate page
  loads). Both processes (backend + vite preview) were stopped and their
  full process trees killed at the end of this pass -- confirmed via
  `Get-NetTCPConnection` showing ports 1422/18742 in `TimeWait`/no
  listener, not left running. Did NOT additionally build a fixture-based
  Chrome harness for the bye-week/playoff-state edge cases (the prior
  UI-expansion effort's `window.fetch`-patched QA-harness technique) --
  those are covered instead by the backend facade-wiring tests' mocked-
  Sleeper scenarios above (bye week, playoff-state-with-real-bracket) and
  the frontend pure-function unit tests exercising the exact same
  display logic Home renders; a real fixture-harness Chrome pass for
  those specific shapes is a disclosed, not-yet-done option for a future
  pass if a live visual (not just unit-tested) confirmation of those
  specific edge cases is wanted.

**Sleeper safety (0 writes):** every new read (`state/nfl`,
`league/{id}/matchups/{week}`, `league/{id}/users`, `league/{id}`,
`league/{id}/winners_bracket`) goes through the existing `SleeperHttpClient
.get_json()` (GET-only, no write method exists on the class, same
structural guarantee prior workers already verified). The live-rendered
check above used the release-gate script's own real-league before/after
byte-diff (already run, already verified identical) plus this pass's own
real-time observation of the rendered app -- no new write surface was
introduced.

**Files changed:** `src/services/sleeper_league_context_service.py`
(new), `src/application/desktop_facade.py`
(`redraft_league_workspace_context` only),
`src/services/league_workspace_context_service.py` (additive fields
only), `desktop/packages/contracts/src/index.ts` (additive types only),
`desktop/apps/redraft/src/weekly-shared.tsx` (new
`useLeagueWorkspaceContext` hook), `desktop/apps/redraft/src/
league-summary.ts` (+6 pure functions), `desktop/apps/redraft/src/
in-season.tsx` (`WeeklyHomePage` only), `desktop/apps/redraft/src/
RedraftApp.tsx` (+1 legacy-redirect route), plus the three new/extended
test files above. Nothing under `marginal_roster_utility_v2`, draft
recommendation logic, scoring, roster legality, `LeagueSnapshot`/
`LeagueWorkspaceContext`'s OTHER fields, the lifecycle resolver,
`DecisionResultEnvelope`, or `PlayerAvailabilityStatus` was touched.

**For Worker 5 (Multi-League Attention Center):** `LeagueWorkspaceContext`
now carries real per-league `matchup`/`standings`/`playoff` -- likely
directly reusable for an attention center that needs to summarize
multiple leagues' current state at a glance (fetch the context once per
league, same shape every time). The pre-existing
`weekly-home-actions` 500 bug (Worker 3's finding) is still open and
NOT touched by this pass -- it's a separate endpoint from
`league-workspace-context` and was never in this pass's path except as
something to watch for; it degrades honestly (frontend shows "Command
center unavailable" rather than crashing) and was reproduced again,
unchanged, during this pass's own live-rendered check.

## P0-3 (real backend + Sleeper + packaged Tauri release gate) -- 2026-09-12

**Two separate, honest verdicts -- do not blend them:**

- **PACKAGING GATE: BLOCKED (pre-existing, not a regression).**
  `npm run check:resources` fails for the `redraft` app: the bundled
  `NWR_DATA_GOVERNANCE.json` governance receipt legitimately contains the
  real owner's name in its own audit trail (`"approved_by"`/`"renewed_by"`),
  which the same script's owner-privacy guard (`ownerMarkers`) forbids in
  any bundled resource. Verified this predates the whole shift
  (`git diff --stat 003d0dd4 HEAD -- desktop/scripts
  desktop/apps/redraft/src-tauri/tauri.windows.conf.json` was empty before
  this pass's own fix below) -- not caused by Worker 2's seed migration or
  anything in this shift. Did NOT bypass or weaken the privacy guard to
  force a build through; that is a real product/governance decision for the
  owner (e.g. redact the bundled copy, or keep the receipt out of the
  distributable bundle and verify it a different way), not something a
  verification pass should decide unilaterally. Separately confirmed the
  Rust/Tauri toolchain itself is NOT the blocker: PyInstaller successfully
  built the real Python sidecar exe (147MB,
  `desktop/binaries/nwr-desktop-api-x86_64-pc-windows-msvc.exe`, gitignored)
  and `cargo check` in `desktop/apps/redraft/src-tauri` compiles cleanly
  (~55s cold, ~1s warm) -- both bundle nothing, so neither hits the privacy
  conflict.
  - **Real, disclosed fix made along the way (not the privacy conflict
    itself, a different bug found while investigating it):** the Windows
    resource-bundle map (`tauri.windows.conf.json`) and its allowlist mirror
    (`check-resource-allowlists.mjs`) still pointed at the OLD 608-row
    bundled seed after Worker 2's P0-2 migrated the runtime facade to
    Freeze V7 (564 rows) -- a native build attempted before this fix would
    have bundled stale, already-expired-approval seed data into the
    installer. Both files now correctly point at
    `docs/hq/model/nwr_redraft_2026_freeze_v7_bundled_seed_v1_20260912/`.
    This did NOT unblock `check:resources` (the owner-marker conflict is
    separate and present on either seed generation's governance receipt).

- **BRIDGE SMOKE: PASS (real backend, real production frontend build, real
  read-only Sleeper league).** Since a full native bundle is blocked (above),
  built and verified the fallback the directive names: a real production
  `vite build` served by `vite preview`, talking to the REAL Python desktop
  API backend process (`scripts/run_nwr_desktop_api.py`, not mocked
  `window.fetch`) over real loopback HTTP with the real auth handshake. Ran
  the full click-through smoke flow live in Chrome against a REAL read-only
  Sleeper league ("Fantasy Gamers", league ID `1312983576827920384`, found
  via the owner's own real AppData profile record -- read-only filesystem
  inspection only, never written to): league chooser, Sleeper import/sync,
  Home, Lineup, Improve Team, Trades, Players (real 564-row Freeze V7 board,
  Player Drawer opens with real detail), League/My Roster (real 15-player
  roster)/Data Health, Draft Room (real not-yet-started board state,
  `configured:false` -- never clicked "Start Draft"), a full page reload
  (restart-equivalent), a cold deep link straight to a sub-route, and a real
  league switch (created a second isolated local profile, switched back).
  Every surface rendered real backend data; only exception is the one real
  bug found (next bullet). **ROS-DATA STATUS:** distinct from the above --
  Sleeper Weekly projections/League sync both showed `OK`/`CURRENT`/`LIVE`
  on Data Health for this profile; Market/ADP correctly showed `UNAVAILABLE`
  (no ADP snapshot imported into this fresh isolated profile -- an expected
  gap for a brand-new import, not a bug).
  - **Real bug found and disclosed, NOT fixed (backend out of scope for this
    pass):** `POST /api/v1/redraft/weekly-home-actions` (the Weekly Home
    "NWR Actions" panel) returns HTTP 500 for a Sleeper-imported profile
    with an active roster. Reproduced directly:
    `DesktopBackendFacade.redraft_weekly_home_actions`
    (`src/application/desktop_facade.py:4181`) still assumes
    `redraft_kdst_streamer(...).data["positions"]` is a dict keyed by
    position; it is actually a list of decision-envelope rows --
    `AttributeError: 'list' object has no attribute 'items'`. The frontend
    degrades honestly ("Command center unavailable") rather than fabricating
    data. NOT reproduced against a fresh local-preset profile with no
    roster (the STREAMER section is likely only reached once a roster
    exists).

**Sleeper safety (0 writes, verified with real evidence, not just an
assertion):** structural -- `SleeperHttpClient` (`src/services/
sleeper_import_service.py`) defines only `get_json()` via
`urllib.request.urlopen()` (GET, no `data=` payload; no write method exists
on the class at all). Grep -- no POST/PUT/PATCH/DELETE call site anywhere in
`src/` targets `api.sleeper.app`. Before/after -- fetched `league`,
`rosters`, `users` directly from `api.sleeper.app` immediately before and
immediately after the real import call and diffed: byte-identical on every
field, every time (both the manual pass and the scripted pass, run
separately). All writes this session touched a fresh, isolated
`local_exports/redraft_v1/` inside this worktree only -- the owner's real
`%LOCALAPPDATA%\com.ninerswarroom.redraft` install was read from exactly
once (one profile JSON + one sleeper_imports receipt JSON, both read-only,
to discover the real league ID/username to use) and never written to.

**Latency (real, single-session measurements; a `bootstrap`/Home cold vs.
warm pair and a cold-vs-warm Player Drawer pair were the only ones with
repeat samples -- see the script's JSON report for the full set):**

| Surface | Time |
| --- | --- |
| Production `vite build` (cold launch's frontend half) | ~0.3-0.6 s |
| Backend process start -> first successful `/api/v1/bootstrap` | ~1-2 s (polled) |
| `bootstrap` (Home) cold | ~215-300 ms |
| `bootstrap` (Home) warm | ~213-320 ms |
| Real Sleeper league-open/import (`sleeper/import`) | ~1.0-2.7 s |
| Player Drawer first open (real click, Chrome) | visually instant (<1 render frame; no separate network call -- drawer reads already-fetched rankings data client-side) |
| Player Drawer second open (warm) | same -- no network round-trip either time |
| Improve Team tab switch (Targets, real 25-candidate list) | ~1-2 s to "Reading..." resolve |
| Trade Finder | ~1.6-9.3 s (widest spread observed; heaviest computed endpoint) |
| Draft refresh (bootstrap's inline `draftBoard`) | included in `bootstrap` above -- no separate endpoint |

**For Worker 4 (automatic NFL week/matchup/standings context):** Weekly Home
today shows `"Fantasy Gamers · Week 1"` and an `NFL WEEK` field defaulting to
`1` regardless of the real current calendar date (today is 2026-09-12,
several weeks into a real season by kickoff conventions) -- worth checking
whether that is this project's real, intentional manual-week-selection
design (there is a visible `NFL WEEK` input the owner sets by hand) or a gap
your work unit is meant to close. Also inherit the disclosed
`weekly-home-actions` 500 bug above if your work touches that surface.

**Files changed this pass:**
`desktop/apps/redraft/src-tauri/tauri.windows.conf.json`,
`desktop/scripts/check-resource-allowlists.mjs` (both packaging-manifest
path fixes only, described above), `desktop/scripts/
nwr_release_gate_smoke.ps1` (new, the repeatable release-gate script),
`docs/codex/post_ui_v1/NWR_RELEASE_GATE_CHECKLIST.md` (new). **Zero** files
under `src/` (backend/model) touched beyond Worker 2's already-committed
migration -- confirmed via `git diff --stat 003d0dd4 HEAD -- src/` showing
only Worker 2's prior commit's changes, none from this pass.

## P0-2 (projection governance reconciliation) -- 2026-09-12

**Classification: B.** Verified fresh (not from memory): this worktree's
default bundled Redraft seed (608 rows, `e483caae...`) has a real,
independently-confirmed EXPIRED approval (`valid_until` 2026-09-09; today
is 2026-09-12) -- reproduced live with a standalone pytest run showing
`redraft_bootstrap()` fails to install any seed at all in a fresh store.
Found the real "Freeze V7" combined admission (491 veteran + 73 rookie =
564 rows) already sitting in this branch's own history (commit `0ae4b039`
verified an ancestor via `git merge-base --is-ancestor`), with its own
already-existing, still-valid owner approval (`valid_until` 2026-10-08) at
`docs/codex/nwr_redraft_2026_rookie_projection_admission_CANDIDATE_v2_20260908/
MERGED_CURRENT_CANDIDATE.approval.json`. No new approval was created --
migrated to that exact already-approved artifact.

Found and fixed a real CRLF-vs-LF checkout hazard (this worktree's
`core.autocrlf=true` would have silently broken the receipt's hash
binding) by LF-normalizing a byte-identical copy into a new canonical
packet (`docs/hq/model/nwr_redraft_2026_freeze_v7_bundled_seed_v1_20260912/`,
full provenance/hash-chain in its `PROVENANCE.md`) with a matching
`.gitattributes eol=lf` rule. Updated `desktop_facade.py`'s
`REDRAFT_SEED_*` constants and two presentation strings that would
otherwise have gone stale under the new counts. Net pytest effect:
`test_desktop_application_api.py` 5 -> 4 known failures (one genuinely
fixed; the remaining 4 are pre-existing/unrelated, one of them now
blocked only by this session's own `NWR_FANTASYPROS_API_KEY` env var, not
this change). Zero new regressions confirmed via an A/B stash comparison
across every other projection/redraft-engine/rookie test file. Frontend
`tsc -b` clean, `vitest run`: 286/286 unchanged. Committed at commit
(see `git log -1`); no merge/push/deploy.

**For Worker 3 (packaged Tauri + real backend release gate):** a FRESH
isolated `redraft_root` in this worktree now bootstraps real, current,
non-expired governed 2026 projection data (564 players) instead of
failing closed -- you do NOT need to stay on fixture/isolation paths for
the Redraft projection layer specifically if your work needs it live.
Everything else (Sleeper-linked Waivers/Trade Analysis/Trade Finder, the
real owner AppData install) is unaffected/untouched by this change and
still requires whatever isolation approach the prior UI-expansion workers
already used.

---

Prior entry (Work Unit 0 + P0-1) below.
(Work Unit 0 + P0-1, this entry) -- run `git log -1` in the worktree to get
the exact hash; not hardcoded here to avoid this doc going stale the
instant a future worker commits on top of it.

## COMPLETED

- **Work Unit 0 (baseline + ledger).** Verified branch
  (`upgrade/nwr-post-ui-product-v1-20260912`), start HEAD
  (`003d0dd4183f7bfc7a2ad2f03960c967dd0bb02e`, matches directive exactly),
  clean worktree. Ran `npm install` in `desktop/` (node_modules were absent
  at worktree creation -- a one-time hoisted-workspace install, not a
  dependency change). `npx tsc -b apps/dynasty/tsconfig.json
  apps/redraft/tsconfig.json`: clean. `npx vitest run
  --no-file-parallelism`: **278/278 passing, 25/25 files** -- exact match
  to the prior UI-expansion effort's final freeze count
  (`NWR_UI_EXPANSION_FREEZE_V1.md`). Confirmed freeze docs present and read:
  `docs/codex/NWR_UI_EXPANSION_FREEZE_V1.md` (FREEZE HEAD `1dd068a3`, one
  named carve-out: Draft Room Board/Queue/Teams/Cheat-Sheet visual-token
  migration, not attempted) and `docs/codex/NWR_UI_EXPANSION_V2_LEDGER.md`
  (12 work units, 24 real bugs fixed, 1 latent bug flagged-not-fixed --
  the exact two bugs this pass's P0-1 closes).
- **P0-1 (fix the two remaining latent crash sites).** Both real,
  pre-existing crash sites reproduced with actual malformed payloads (not
  assumed) and fixed at the narrowest correct source. See detail below.

## IN PROGRESS

None. This worker's scope (Work Unit 0 + P0-1) is done; terminating per
directive.

## BLOCKED

Nothing blocked this pass.

## NEXT

**P0-2 (projection governance reconciliation)** -- a separate worker's
scope, not attempted here. No other work units were started or touched.

## TEST STATUS

- `npx tsc -b apps/dynasty/tsconfig.json apps/redraft/tsconfig.json`:
  **clean**, both before and after the P0-1 fix.
- `npx vitest run --no-file-parallelism` (full monorepo, `desktop/`):
  **286/286 passing, 25/25 files** (278 baseline + 8 new regression tests,
  **0 regressions**).
  - `pages.test.ts`: +5 tests (`dataHealthStatusLabel` / `dataHealthTone`
    undefined-status regression group).
  - `draft-room-v2.test.ts`: +3 tests (`actionToBadgeTone`
    undefined/null-action regression group).
- Both bugs were reproduced with a standalone Node repro script BEFORE the
  fix (real `TypeError`, not assumed) and a matching `expect(() =>
  ...).toThrow(TypeError)` assertion is preserved in each new test group
  to prove the guard is load-bearing (not a no-op).
- Console errors introduced by this pass: **0** (no live browser render was
  performed this pass -- verification was tsc + vitest only, consistent
  with the directive's presentation/defensive-coding-only scope; no new
  runtime/browser-console risk was introduced by either fix).

## DATA-GOVERNANCE STATE

Unchanged. No backend/model file touched (`git diff --stat 003d0dd4 HEAD --
src/` is empty -- verified). No seed data, projections, ADP, or governance
receipts read or written. The owner's real leagues and
`AppData\Local\com.ninerswarroom.redraft` install were never touched.

## PROCESS-RAM STATE

No backend/desktop process was started this pass (tsc/vitest only, no
`npm run dev`, no Tauri launch, no Chrome MCP render). Nothing left running
in the background.

---

## Work Unit 0 + P0-1 detail (2026-09-12)

### Bug 1 -- `LeagueSyncTab` `.replaceAll()` on possibly-undefined `status`

**Location (exact):** `desktop/apps/redraft/src/league.tsx:341`, inside
`LeagueSyncTab`'s "League sync detail" panel --
`syncCategory.status.replaceAll("_", " ")`.

**Contract:** `DataHealthCategory.status` (`packages/contracts/src/index.ts`)
is typed as a non-optional enum (`"OK" | "DEGRADED" | "UNAVAILABLE" |
"NOT_APPLICABLE" | "NO_ACTIVITY"`), but a degraded/malformed backend
response (schema drift, partial payload) can genuinely omit it at runtime,
violating the declared type. `dataHealthTone(status)` (the paired tone
function) was already runtime-safe -- it only does `===` comparisons, no
method calls -- but the `.replaceAll()` label computation was not.

**Repro (real, not assumed):** a standalone Node script constructed
`{ status: undefined }` and called `.replaceAll("_", " ")` on it directly --
`TypeError: Cannot read properties of undefined (reading 'replaceAll')`,
matching the exact failure the prior ledger entry described.

**Same pattern found nearby, fixed too:** `desktop/apps/redraft/src/
pages.tsx:448` (`DataHealthPage`) reads the *same* `DataHealthCategory.status`
field with the identical unguarded `.replaceAll()` call -- same contract,
same root cause, high-confidence fix, not speculative.

**Fix:** added one shared helper, `dataHealthStatusLabel(status: string |
null | undefined): string` (`pages.tsx`, next to `dataHealthTone`) that
returns `status.replaceAll("_", " ")` when truthy, else the honest literal
`"Unknown"` -- never a fabricated status. Both call sites
(`league.tsx:341`, `pages.tsx:448`) now use it. `league.tsx` imports it
from `pages.tsx` alongside the existing `dataHealthTone` import (same
precedent, no new module).

**Regression tests:** `pages.test.ts`, new `describe("dataHealthStatusLabel
...")` block (5 tests) -- real-status formatting, the load-bearing
pre-fix-crash proof, undefined-to-"Unknown", null-to-"Unknown", and
`dataHealthTone` never fabricating a confident tone for a missing status.

### Bug 2 -- `actionToBadgeTone` `.toUpperCase()` on possibly-undefined `action`

**Location (exact):** `desktop/apps/redraft/src/draft-room-v2.tsx`, the
`actionToBadgeTone` function (was line 2645) and its one unguarded call
site in the Player Drawer's "Action" stat (was line 3981) --
`actionToBadgeTone(candidate.action)` / `label={candidate.action}`.

**Contract:** `DecisionBundleCandidate.action`
(`packages/contracts/src/index.ts`) is typed as a non-optional `string`,
but a degraded/malformed real `DecisionBundle` response can genuinely omit
it at runtime. Three sibling functions share this exact `action:
string` + `.toUpperCase()` shape (`resolveDisplayAction`,
`actionToBadgeTone`, `splitActionValue`); a full-file audit of every call
site confirmed the OTHER two call sites (the Suggestions table's Action/
Value columns, the Compare table) already coerce via `String(row.action)`
first or guard with `row.action == null` before calling -- safe, if a bit
leaky (would render the literal string `"undefined"` rather than crash, a
separate, lower-severity cosmetic gap, not touched this pass). Only the
Player Drawer's direct `candidate.action` read was unguarded.

**Repro (real, not assumed):** a standalone Node script constructed
`{ action: undefined }` and called `.toUpperCase()` on it via the exact
pre-fix function body -- `TypeError: Cannot read properties of undefined
(reading 'toUpperCase')`, matching the exact failure the prior ledger
entry described.

**Fix:** widened `actionToBadgeTone`'s signature to `action: string | null
| undefined` (the real runtime shape, not just the declared one) and added
a guard (`if (!action) return "review";`) -- an unrecognized/missing action
already fell to the generic `"review"` tone for other unrecognized labels,
so this reuses an existing, honest fallback rather than inventing a new
one. The call site's label was also hardened
(`label={candidate.action || "Unknown"}`) so a missing action shows the
literal word "Unknown" rather than a blank badge -- an honest degraded
state, not garbage. `resolveDisplayAction`/`splitActionValue` were left
untouched (no unguarded call site reaches them with a possibly-undefined
action; touching them was assessed as unnecessary defensive hardening
beyond the genuinely reachable bug).

**Regression tests:** `draft-room-v2.test.ts`, appended to the existing
`describe("actionToBadgeTone", ...)` block (3 tests) -- undefined-input,
null-input (both assert no throw + the "review" fallback tone), and the
load-bearing pre-fix-crash proof.

### Additional unsafe patterns reviewed, NOT fixed (out of narrow scope)

Searched all of `desktop/apps` for `.replaceAll(`, `.toUpperCase(`,
`.toLowerCase(` called directly on a field. Reviewed and deliberately left
alone (disclosed, not silently skipped):

- `result.writeBehavior.replaceAll("_", " ")` (`pages.tsx:525`,
  `improve-team.tsx:630`) -- `writeBehavior: string` appears identically in
  11 places across `packages/contracts/src/index.ts`, always as fixed
  response-envelope metadata (e.g. `"NO_SLEEPER_WRITES"`) populated by a
  shared backend helper on every response, not a per-category computed
  value with a known partial-failure mode like `DataHealthCategory.status`
  was. Lower confidence that this is genuinely reachable; left alone per
  the directive's explicit "not a repo-wide sweep" boundary.
- `apps/dynasty/src/pages/decisions.tsx:991`
  (`decision.recommendation.replaceAll(...)`) and `:1032`
  (`dimension.outcome.replaceAll(...)`) -- same non-optional-`string`-in-
  contract shape (`TradeDecision.recommendation`, a dimension's `outcome`),
  but a different app (dynasty, not redraft) and a different surface from
  either designated bug -- not "nearby" by file/contract/root-cause the way
  the `DataHealthCategory.status` duplicate was. Flagged here as a
  candidate for a future dynasty-side pass, not fixed this pass.
- Every other `.toUpperCase()`/`.toLowerCase()` call site found (see the
  full grep list in this session) was already guarded (`?? ""`, `String(...)`
  coercion, or operates on a value already known non-null in context) --
  no further action needed.

### Files changed (this commit)

`desktop/apps/redraft/src/pages.tsx`, `desktop/apps/redraft/src/league.tsx`,
`desktop/apps/redraft/src/draft-room-v2.tsx`, `desktop/apps/redraft/src/
pages.test.ts`, `desktop/apps/redraft/src/draft-room-v2.test.ts`. **Zero**
files under `src/` (backend/model) touched -- confirmed via `git diff
--stat 003d0dd4 HEAD -- src/` (empty).

### Hard boundaries respected

`marginal_roster_utility_v2`, draft recommendation logic, scoring, roster
legality, `LeagueSnapshot`/`LeagueWorkspaceContext` semantics, the
lifecycle resolver, `DecisionResultEnvelope` semantics,
`PlayerAvailabilityStatus` authority, and provider architecture were read
from (for contract shapes only), never written to. No merge, push, or
deploy performed.

### Open issues for the next worker

1. **P0-2 (projection governance reconciliation)** is untouched -- next in
   the queue per the directive.
2. `writeBehavior.replaceAll(...)` (2 sites) and dynasty's
   `decisions.tsx` (2 sites) are real, structurally-identical-risk
   `.replaceAll()`/similar call sites on non-optional-`string` contract
   fields, deliberately NOT hardened this pass (see rationale above) --
   worth a quick look if a future pass has budget for it, but genuinely
   lower-confidence/lower-reachability than the two fixed here.
3. The Compare table's and Suggestions table's `String(row.action)`
   coercion (draft-room-v2.tsx) is crash-safe but not leak-safe -- a
   genuinely missing `action` would render the literal string `"undefined"`
   as a visible badge/label rather than an honest "Unknown" fallback. Not
   a crash, so out of this pass's narrow P0-1 scope, but a real, disclosed
   cosmetic gap.
4. This pass did not launch a live browser render (Chrome MCP) to confirm
   zero console errors end-to-end -- verification was tsc + vitest only,
   which is sufficient for a presentation/defensive-coding fix of this
   size and matches the directive's own test requirements, but is
   disclosed here as a real, not a hidden, scope choice.
