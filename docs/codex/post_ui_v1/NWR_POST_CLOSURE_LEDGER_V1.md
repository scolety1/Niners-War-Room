# NWR Post-Closure Ledger V1

New, smaller ledger for the post-closure implementation work that follows
`docs/codex/post_ui_v1/NWR_POST_CLOSURE_RESEARCH_V1.md`. The prior
`NWR_POST_UI_WORKDAY_LEDGER.md` (2,800+ lines, covering the entire
post-UI-product-v1 shift through Closure Worker C) is kept as-is for
historical reference; start here going forward so entries stay readable.

No merge/push/deploy by any worker. No push to origin without explicit
owner authorization.

---

## Worker D — FAAB urgency enum fix + small tech-debt batch — 2026-09-13

**Scope: research doc items #1 and #5.** Branch
`upgrade/nwr-post-closure-fixes-v1-20260913`, worktree
`C:\NWR\post-closure-fixes-v1`, start HEAD `4c8ab1b0`.

### Item 1 — FAAB urgency enum mismatch (FIXED)

**Root cause**: `src/services/waiver_engine_service.py`'s `suggest_faab_bids`
set `FaabBidSuggestion.urgency` to one of its own internal, more
descriptive reason codes -- `STARTER_UPGRADE` / `BENCH_DEPTH` / `LOW_VALUE`
-- and `src/application/desktop_facade.py` (`redraft_waivers`, the
`faabUrgency` field, ~line 3435) passed that value straight through to the
JSON response with no translation. The shared contract
(`desktop/packages/contracts/src/index.ts:1109`,
`faabUrgency: "HIGH" | "MEDIUM" | "LOW" | null`) and both frontend lookup
tables that key off it (`weekly-shared.tsx`'s `FAAB_URGENCY_TONE`,
`improve-team.tsx`'s local `FAAB_URGENCY_RANK`) only ever recognized
`HIGH`/`MEDIUM`/`LOW`. Every real FAAB urgency badge fell through to the
generic "review" fallback tone (regardless of actual urgency) and the FAAB
tab's urgency-based sort silently no-opped (every row tied at the same
fallback rank 3).

**Fix direction chosen: (a) -- map the backend's existing reason codes onto
the contract's `HIGH`/`MEDIUM`/`LOW` scale, at the source.** Added a single
module-level `FAAB_URGENCY_TIER` dict in `waiver_engine_service.py`
(`STARTER_UPGRADE -> HIGH`, `BENCH_DEPTH -> MEDIUM`, `LOW_VALUE -> LOW`) and
renamed the local variable that drives the rationale text/multiplier to
`urgency_reason` (unchanged internal logic), assigning
`FAAB_URGENCY_TIER[urgency_reason]` to the field the contract actually
promises. Chosen over updating the contract/UI to the descriptive
vocabulary because:
- **Fewer real call sites**: this direction touches exactly one backend
  file (plus its test). The alternative would have required changing
  `contracts/src/index.ts`, `weekly-shared.tsx`'s `FAAB_URGENCY_TONE`,
  `improve-team.tsx`'s `FAAB_URGENCY_RANK`, and every test fixture that
  hardcodes `"HIGH"`/`"MEDIUM"`/`"LOW"` (at least 4-5 files vs. 1).
- **No information is actually lost**: the descriptive detail
  (starter-upgrade vs. bench-depth vs. low-value) is already fully
  preserved in the separate `rationale` string every call site renders
  (`improve-team.tsx`'s title tooltip and `why` prop, `in-season.tsx`'s
  inline `<small>` text) -- the tier field only ever drove badge tone/sort,
  not the visible explanation.
- `desktop_facade.py` needed zero changes (it already just passes
  `bid.urgency` through).

**Fixture correction**: no Python test previously asserted a specific FAAB
urgency string at all (`tests/test_waiver_engine_service.py` only checked
bid dollar amounts), so there was no backend fixture to "fix" per se -- the
real masking gap was the *absence* of a test connecting the backend's real
output to the contract's promised values. The frontend unit fixture
(`improve-team-explain.test.ts:22`, `faabUrgency: "HIGH"`) already used a
contract-shaped literal and needed no change under fix direction (a); it
simply never exercised the real (buggy) backend value, which is exactly
why it never caught this.

**Regression tests added**:
- `tests/test_waiver_engine_service.py`: three new tests --
  `test_faab_urgency_uses_the_shared_contracts_high_medium_low_scale`
  (asserts exact `HIGH`/`MEDIUM`/`LOW` per becomes-starter/bench/low-value
  candidate, using real `WaiverCandidate` fixtures, not just "some
  string"), `test_faab_urgency_tier_maps_every_internal_reason_onto_the_
  contract_scale` (locks the mapping dict itself), and
  `test_faab_urgency_for_unmatched_identity_is_the_contracts_low_value`.
- `desktop/apps/redraft/src/weekly-shared.test.ts`: one new test asserting
  `FAAB_URGENCY_TONE` covers exactly the real contract type's 3 literal
  values (typed as `WaiverAddCandidate["faabUrgency"]`, not a hand-rolled
  string, so it fails to compile if the union and the table drift apart
  again), with the exact expected tone per value.

**Live verification against the real Fantasy Gamers Sleeper league**
(ID `1312983576827920384`, read-only): ran
`desktop/scripts/nwr_release_gate_smoke.ps1 -KeepRunning -SleeperLeagueId
1312983576827920384 -SleeperUsername scolety`, which starts the real
Python desktop API backend (port 18742) and a real production `vite
preview` build (port 1422) against the already-imported real profile.
- Direct `POST /api/v1/redraft/waivers {"mode":"REST_OF_SEASON"}` against
  the running backend returned 25 real candidates with `faabUrgency`
  values of exactly `MEDIUM` (bench-depth adds, marginal utility > 0) and
  `LOW` (marginal utility <= 0) -- never the old
  `STARTER_UPGRADE`/`BENCH_DEPTH`/`LOW_VALUE` strings. (No `HIGH` in this
  particular real pool, since no free agent currently becomes a starter on
  this roster -- consistent with the roster's real state, not a gap in the
  fix.)
- Drove the real app in Chrome (`http://127.0.0.1:1422/#/league/<id>/
  waivers?tab=faab`, real Fantasy Gamers league already active): the FAAB
  tab correctly renders `MEDIUM URGENCY` badges (amber/gold, "review"
  tone) and `LOW URGENCY` badges (green, "safe" tone), sorted MEDIUM before
  LOW as `FAAB_URGENCY_RANK` intends, with bid text reading e.g. "BID
  $30-50 - MEDIUM urgency for Juwan Johnson" -- not blank, not the raw
  backend enum, not miscolored. The Targets tab's suggested-bid line
  ("SUGGESTED BID $30-50 - MEDIUM urgency") renders identically.
  **Zero console messages of any kind** on a fresh reload of the FAAB tab
  (checked via `read_console_messages` with no filter after a hard
  navigation).
- Sleeper writes: 0. `redraft_waivers` only issues `GET` calls through
  `SleeperHttpClient.get_json` (rosters/players); no POST/PUT/PATCH/DELETE
  call site targets `api.sleeper.app` anywhere in `src/` (same structural
  guarantee every prior worker has verified). Backend + vite preview
  processes stopped and cleaned up (`taskkill`) after verification.

### Item 5 — small cosmetic/tech-debt batch

- **Stale comment (FIXED)**: `src/services/waiver_engine_service.py`'s
  module docstring claimed the DST/K streamer lane "has a real
  nflreadpy-backed matchup signal." Confirmed false by direct read of
  `fantasypros_kdst_consensus_service.py` (pure FantasyPros ECR passthrough
  + live Sleeper roster-ownership matching, no schedule/matchup signal at
  all) -- corrected the comment to say so honestly.
- **`.replaceAll()` hardening on `writeBehavior` (pages.tsx / improve-team.tsx)
  -- VERIFIED UNREACHABLE, SKIPPED**: `result.writeBehavior.replaceAll("_",
  " ")` in both `WeeklyToolsPage` (pages.tsx:538) and its `improve-team.tsx`
  equivalent (line 630) reads a field that is a hardcoded literal string
  (`"NO_SLEEPER_WRITES"` / `"NO_SLEEPER_WRITES_NO_FANTASYPROS_WRITES"`) on
  every single success-path return in `desktop_facade.py` (11 emission
  sites checked, all literal, none conditional on a variable that could be
  `None`); every error path raises `FacadeError` instead of returning a
  partial payload, so the frontend's `results` array can never contain an
  object missing this field. Confirmed by direct code read of
  `redraft_kdst_streamer` end to end. Hardening a field that cannot
  actually be null/undefined under the current backend contract would add
  dead defensive code, not fix a real risk -- skipped per the directive's
  own "don't harden something that's actually unreachable" guidance.
- **`.replaceAll()` hardening on dynasty `decisions.tsx` -- VERIFIED
  UNREACHABLE, SKIPPED**: `decision.recommendation.replaceAll(...)` and
  `dimension.outcome.replaceAll(...)` both read fields that flow through
  `desktop_facade.py`'s `_trade_decision_payload` (the single call site
  that builds this response), which wraps every field in the `_text()`
  helper -- `_text` guarantees a real string is always returned (coercing
  `None`/`"nan"`/`"none"`/`"null"`/`"<na>"` to `""`), never `None`/
  `undefined`. `"".replaceAll(...)` is safe (returns `""`). Same
  conclusion: not a reachable crash or leak site, skipped rather than
  force a no-op change.
- **`String(row.action)` "undefined" leak in Compare/Suggestions
  (draft-room-v2.tsx) -- VERIFIED NOT REPRODUCIBLE, SKIPPED**: traced both
  the Suggestions candidate table's Action/Value columns (lines 2288-2301,
  no null guard before `String(row.action)`) and the Compare table's
  equivalent (lines 3673-3683, which does guard with
  `if (row.action == null) return "-"`). Empirically verified with a
  throwaway vitest test exercising `resolveDisplayAction`/
  `splitActionValue`/`actionToBadgeTone` directly with `undefined` and
  `null`: `splitActionValue`'s own ternary chain has a catch-all default
  (`"Review data"` for the action label, `"Unknown"` for the value when
  geometry is also missing) for any string it doesn't recognize, including
  the literal `"undefined"`/`"null"` that `String(...)` produces --  so the
  visible badge always reads "Review data" and never leaks the raw
  coercion text. The research doc's description of this item does not
  survive direct inspection/testing; documenting honestly and skipping
  rather than forcing an unneeded change. (Scratch test file used for this
  check was not committed.)
- **Dead button cleanup ("Open in Analyze") -- NOTHING TO DO**: grepped for
  the button; it no longer exists anywhere in the code (only historical
  comments in `trades-explain.ts`/`trades-explain.test.ts`/`trades.tsx`
  referencing its removal during an earlier closure pass, one explicitly
  reading "Deliberately NO 'Open in Analyze' cross-tab jump on these
  cards"). Already cleaned up by prior work; no action needed here.

### Tests

- `python -m pytest tests/test_waiver_engine_service.py`: 12 passed (9
  pre-existing + 3 new).
- `python -m pytest tests/test_desktop_facade_architecture_wiring.py
  tests/test_weekly_home_single_snapshot.py
  tests/test_trade_package_search_facade_wiring.py`: 23 + 6 passed (safety
  sweep of every other consumer of `waiver_engine_service`/FAAB-adjacent
  facade wiring -- no regression).
- `npx tsc -b apps/dynasty/tsconfig.json apps/redraft/tsconfig.json`: clean,
  zero errors.
- `npm run test` (full monorepo vitest, from `desktop/`): **28 test files,
  368 tests, all passed** (includes the 1 new `weekly-shared.test.ts`
  case; still >= the 367-baseline the directive named).
- Console errors during live Chrome verification: **0**.

### Files changed

- `src/services/waiver_engine_service.py` -- the FAAB urgency tier mapping
  fix + the stale streamer-schedule-signal comment correction. Justified:
  this is the exact, narrowly-scoped root cause of the shipping bug;
  `marginal_roster_utility_v2` and every other hard-boundary function are
  untouched (only called, as before).
- `tests/test_waiver_engine_service.py` -- 3 new regression tests, no
  existing test changed (none needed fixing, per the fixture analysis
  above).
- `desktop/apps/redraft/src/weekly-shared.test.ts` -- 1 new regression
  test for the frontend tone table.

No draft recommendation/scoring/roster-legality file, `LeagueSnapshot`/
`LeagueWorkspaceContext`/lifecycle-resolver/`DecisionResultEnvelope`/
`PlayerAvailabilityStatus` file was touched.

### Open issues for the next worker

- Item 5's `.replaceAll()`/`String(row.action)` sites are genuinely
  unreachable/non-reproducible today under the current backend contract --
  re-verify if `desktop_facade.py`'s `writeBehavior`/`_text()` guarantees
  or `splitActionValue`'s catch-all default ever change; they'd become
  real risks again if any of those invariants are relaxed.
- The build-machine-path leak in the shipped `.exe` Rust panic strings
  (`--remap-path-prefix`, research doc item in the "not recommended for
  now" tier) and the install-and-launch verification gap remain untouched
  -- out of this worker's scope (items #1/#5 only).
- Per the directive: next up is a real profiling pass on Waivers
  (THIS_WEEK, ~16.3s) and Weekly Home aggregation (~7.9s) latency (research
  doc item #3 / Area J) -- likely root causes already named there
  (`redraft_weekly_home_actions` re-invoking several live-Sleeper-backed
  sub-calls separately; THIS_WEEK mode's live per-candidate weekly-
  projection resolution across the whole free-agent pool). Neither
  profiled nor touched this pass.
