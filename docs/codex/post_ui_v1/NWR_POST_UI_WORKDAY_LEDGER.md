# NWR Post-UI Workday Ledger

Multi-worker unattended implementation shift on the NWR desktop frontend,
branch `upgrade/nwr-post-ui-product-v1-20260912`, worktree
`C:\NWR\post-ui-product-v1`. Each worker appends its own entry below. Durable
tracking doc for the next workers -- keep entries concise, not narrative.

No merge/push/deploy by any worker. No push to origin without explicit
owner authorization (none exists for this shift).

---

## CURRENT HEAD

Two commits on top of start head `003d0dd4183f7bfc7a2ad2f03960c967dd0bb02e`
(Work Unit 0 + P0-1, then P0-2 below) -- run `git log -1` for the exact
hash.

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
