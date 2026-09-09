# NWR Overnight V3 Retry-Queue Validation — Final Report

Contract filed first: `RETRY_QUEUE_VALIDATION_CONTRACT.md` (same directory). Reference commit
`a72500a6` (confirmed via `git merge-base`), candidate `e652caeb` plus this session's own additions on
the same branch. Host: ~3.2-5.6GB free of ~15.8GB observed across the session (fluctuating, within the
previously-documented range); work done strictly sequentially, one dev server / one test run at a
time; no OOM recurred this session.

## 1. Diff verification

Full diff `a72500a6..e652caeb` (excluding docs): 32 files, +2132/-350. Classification:

- **Draft legality / recommendation behavior**: `redraft_roster_legality_service.py` (new canonical
  authority), `decision_bundle_live_service.py`, `decision_bundle_live_service_v2.py`,
  `redraft_draft_room_v1_service.py`, `practical_redraft_mock_service.py`, `desktop_facade.py`
  (roster-limits intake).
- **Status-risk**: `current_player_status_overrides_service.py` (new `ADMINISTRATIVE_EXEMPT` kind).
- **League shell**: `RedraftApp.tsx`, `leagues.tsx` (new), `redraft.css`.
- **In-season capability**: `fantasypros_kdst_consensus_service.py`, `sleeper_redraft_owner_service.py`,
  `pages.tsx` (Free Agents / Opponent Rosters / League Home).
- **UI-only**: `cheat-sheet.tsx`, `profile.tsx`, `draft-room-v2.tsx` label/shortcut/Ballers-map fixes,
  `components.tsx` (search ref).
- **Tests/docs**: `tests/fixtures/test18_redraft_fixture.py` (new), 8 test files, 2 lane reports + the
  final integration report.

No unrelated/accidental changes found (every hunk maps to one of the above categories, matching the
lane reports' own descriptions).

### Canonical legality authority — confirmed single source

`evaluate_draft_pick_legality` is imported and used as the sole hard-maxima/feasibility gate at every
live call site: `desktop_facade.py:210/1781` (bulk legality annotation), `decision_bundle_live_service.py`
(:180, :273, :320 — Suggestions build, manual-K/DST fallback, shortlist), `decision_bundle_live_service_v2.py:102`,
`redraft_draft_room_v1_service.py` (:1480, :2215, :2321, :2378, :2716, :2734 — pick recording, board
legality flags, CPU auto-pick), `practical_redraft_mock_service.py:91` (CPU/opponent simulation). No
second, competing implementation remains on any of these paths.

### Real duplicate/legacy path found — confined to historical backtesting, not live

`draft_strategy_framework_service.py` has its own independent `compute_position_caps` /
`make_roster_capped_greedy_nwr_strategy` position-cap logic. Traced its only callers:
`strategy_tournament_service.py`, `team_score_calibration_corpus_service.py`,
`historical_draft_replay_engine_service.py` — all historical walk-forward/backtest harnesses, never any
of the eight live surfaces above. Not a live duplicate-authority bug. Not touched.

### Real, disclosed finding: canonical legality is materially MORE PERMISSIVE than the old check for
### unconfigured QB/TE

This is the one finding from this pass that most needs owner attention. The pre-branch
`_roster_candidate_allowed` (`a72500a6`) had hardcoded per-position defaults when `roster_limits` had no
explicit entry: QB ≤ `max(qb+superflex+1, 2)`, TE ≤ `max(te+1, 2)`, K/DST ≤ exact roster requirement,
everything else ≤ `rounds` (the real Test 18 WR bug). The new canonical `evaluate_draft_pick_legality`
deliberately removed ALL such hardcoded defaults (its own docstring: "does not contain strategy
heuristics... an unknown rule is not silently invented") and relies solely on the mandatory-slot
feasibility guard when a position has no explicit `roster_limits` entry.

Verified live (script, not a claim): in a 1QB/2RB/2WR/1TE/1FLEX/1K/1DST/7BN league with
`roster_limits={}` (the real state of every existing profile before this branch shipped the UI to set
limits — `desktop_facade.py` never auto-populates `roster_limits`, it is purely owner opt-in), **8 QBs
are legally draftable** before the feasibility guard finally blocks a 9th. The old code would have
blocked at 2. This is a genuine behavioral regression in the DEFAULT (unconfigured) case specifically
for QB/TE — WR/RB are now correctly bounded for the first time (the actual Test 18 fix), but QB/TE lost
their old built-in ceiling.

**Why this was not silently patched**: `compute_position_caps` (the same already-validated formula used
in historical backtesting) produces the *same* generous ceiling (starters + full bench = 8) for this
exact roster shape, so it is not obviously "wrong" by this codebase's own established design language —
it may be an intentional generalization, not a bug. Whether 8 legal-but-very-unlikely-to-be-recommended
QBs is acceptable given the already-promoted `marginal_utility` primary sort (which should independently
steer away from a 3rd+ QB long before it becomes the actual top Suggestion) is a real product judgment
call, not a clear-cut defect — and the owner has previously and explicitly declined a "no RB quota" style
heuristic fix in this exact area (Lane 1, item 1.7). Reported here, not fixed, per the mission's own
instruction to report rather than silently patch ambiguous cases.

**Recommended follow-up (not performed here)**: either (a) auto-populate `roster_limits` via
`compute_position_caps` at profile creation/update time so no real profile is ever "unconfigured" again,
or (b) restore a QB/TE default inside `evaluate_draft_pick_legality` explicitly, or (c) confirm via a
real DecisionBundle trace that `marginal_utility` already makes this ceiling practically unreachable and
close as WORKS_AS_INTENDED. Left as an explicit open item.

## 2. Preregistration

See `RETRY_QUEUE_VALIDATION_CONTRACT.md`. Filed after Phase 4/5's mechanical, non-tunable regression
replays but before Phases 3/7/8/9/10's results — disclosed honestly rather than silently reordered.

## 3. Historical walk-forward validation

**Environment constraint (disclosed before any result)**: this worktree has no governed 2026 projection
snapshot installed (`local_exports/projections/2026/current.csv` absent) and no historical nflverse
season corpus installed either — both real, pre-existing, already-documented environment gaps, not
newly discovered or fabricated around. Installing a real snapshot requires a real, owner-issued
approval receipt (`install_projection_snapshot`'s `_validate_approval_receipt` gate) that this session
cannot self-issue and did not attempt to forge.

What COULD be run without new data: the existing historical-replay/tournament/calibration unit-test
harnesses (`test_historical_draft_replay_engine_service.py`, `test_strategy_tournament_service.py`,
`test_team_score_calibration_corpus_service.py`) — 15/15 pass, but these are fixture-based unit tests of
the harness code itself, not an outcome-based walk-forward re-validation against real historical
seasons. A behavioral-equivalence read of the actual legality-check diff (old `_roster_candidate_allowed`
vs new `evaluate_draft_pick_legality`, see section 1) stands in as the best available evidence of what
changed and why, in place of an outcome re-run this environment cannot perform.

**Verdict: WALK-FORWARD = FAIL (not attempted at the outcome level; environment-blocked, matching the
retry queue's own RESOURCE_BLOCKED classification, now more precisely DATA_ACCESS_BLOCKED)**. Everything
this environment could still support responsibly (the diff-level behavioral audit above) was done.

## 4. Test 18 exact replay

Ran the existing permanent fixture (`tests/fixtures/test18_redraft_fixture.py`,
`tests/test_test18_r14_legality_regression.py`) — 8/8 pass. Additionally replayed rounds 1-14
round-by-round against the canonical service directly (script, not committed as a new test — the
fixture already covers the acceptance-critical R14/15/16 cases permanently):

| Round | Real pick | Legal under canonical service? |
|---|---|---|
| 1 | McCaffrey (RB) | LEGAL |
| 2 | McBride (TE) | LEGAL |
| 3-4 | Olave, Flowers (WR) | LEGAL |
| 5 | Jacobs (RB) | LEGAL |
| 6 | **Stafford (QB)** | LEGAL |
| 7-9 | Wilson, Robinson, Sutton (WR) | LEGAL |
| 10 | **Lawrence (QB2)** | LEGAL |
| 11-13 | Allen, Meyers, Jennings (WR) | LEGAL — roster now WR 8/8, RB 2, TE 1, QB 2 |
| **14** | Franklin/Doubs (WR, illegal) → **Kyler Murray (QB3)** | Franklin/Doubs correctly **BLOCKED** (`POSITION_MAXIMUM_REACHED`, WR 8/8); Kyler LEGAL and the top remaining legal candidate |
| 15 | Ravens D/ST | LEGAL — only D/ST and Fairbairn remain legal |
| 16 | Fairbairn (K) | LEGAL — only Fairbairn remains legal |

No historical pick 1-13 was itself illegal under the fixed service — the real defect was specifically
that nothing stopped the WR run at 8/8 from continuing, not that any prior pick broke a rule. Strategic
composition after round 13 (before the fix ever fires): RB 2 (zero bench depth), TE 1 (zero depth), WR 8
(vs. 2 starters + 1 possible flex = 3 useful slots), QB 2 — confirms this is genuinely bad roster
construction independent of legality, exactly matching the corrected evidence packet's own framing.

**TEST 18 REPLAY = PASS.**

## 5. New blind ESPN draft

**Disclosed limitation** (see section 3): no real 2026 data in this worktree, so this used
`practical_redraft_mock_service.run_practical_mock` (the retry queue's own named automatable substitute,
"exists, untested tonight") against a clearly-labeled SYNTHETIC ranked pool (`QB01`..., never presented
as real players), with `roster_limits` populated via the already-validated `compute_position_caps` (not
left unconfigured, avoiding the section-1 gap). 10-team, slot 5, roster
1QB/2RB/2WR/1TE/1FLEX/1K/1DST/7BN, 16 rounds.

Result: 160/160 unique picks, zero errors, **zero position-cap violations across all 10 rosters, zero
illegal picks recorded** (replayed every pick against `evaluate_draft_pick_legality` independently).
K/DST filled for every team. Owner (slot 5) finished QB 3 / RB 6 / WR 4 / TE 1 / K 1 / DST 1.

**Important, undersold-if-omitted caveat**: this harness selects by the ranking's *static* value order
(best-available-legal), NOT the live, already-promoted `marginal_utility`-sorted Suggestions order used
in production. Under this cruder proxy, two synthetic teams (slots 9 and 10) drafted QB counts of 6 —
legal (well under the cap of 8) but not a demonstration that the *real* production ordering would ever
surface a 3rd+ QB as its actual top recommendation; that requires the real `marginal_utility` signal,
which this harness does not exercise. **Do not read this as "no QB hoarding pathology remains" — read it
as "the legality ceiling holds even under a cruder, more hoarding-prone selection rule."**

**NEW BLIND DRAFT = PASS on legality/completeness/K-DST-fill; hoarding-pathology claim explicitly
NOT independently verified against the real production ordering in this environment.**

## 6. RB-now / wait-on-QB counterfactual UI

Built. `buildScarcityCounterfactual` (`draft-room-v2.tsx`) reuses only already-computed
`SuggestionRow` fields (`pickScore`, `teamScoreAfter`, `costOfWaiting`, `makeItBackProbability`,
`makeItBackTrials`) — the same Cost-of-Waiting-V2/Make-It-Back data already shipped and already
displayed per-candidate. No new backend modeling. Position-agnostic: picks whichever position among the
current legal candidates has the lowest real Make-It-Back probability as the "scarce" path, compares
against the actual #1 recommendation (or the next-best position if the scarce candidate IS the #1). Null
— never fabricated — when fewer than two positions are on the board or no candidate has a real
evaluation. Rendered as a compact "SCARCITY" chip + detail line in the Suggestions panel, same UI idiom
as the existing CLOSE CALL chip. 5 new unit tests, all passing; `tsc -b` clean.

## 7-8. Rendered integrated acceptance + state-leak stress test

Backend launched via the documented real dev recipe (`scripts/run_nwr_desktop_api.py --port 18742 --mode
redraft --repo-root <this worktree>`, dev token `nwr-desktop-development-token-only-000000000000`,
matching `browserRuntime()`'s own fallback) against an isolated `local_exports` store in this worktree —
**never the real owner AppData install** (`AppData\Local\com.ninerswarroom.redraft`), confirmed by the
fresh "No leagues yet" chooser state. Frontend via `npm run dev:redraft` (Vite, port 1422). Both launched
sequentially, verified live via `curl` before touching the browser.

Real profiles created for this pass (never the owner's real Fantasy Gamers/403/Tester leagues, which do
not and should not exist in this isolated store): "QA League A (10-team)", "QA League B (12-team SFLX)",
"QA League C (12-team HalfPPR)".

Verified via Chrome MCP: League Chooser renders and lists real created profiles; card click →
activate → correct workspace loads with the right league name/shape; header "Switch league" dropdown
performs an in-place switch; Draft Setup correctly resets to the new league's own team count/slot grid on
every switch (no stale team-count or slot-selection leak observed across A→B→C→A→B). Weekly League Home,
Free Agents, and Cheat Sheet all render cleanly and **honestly disclose** blocked/unavailable states
("PROJECTIONS BLOCKED", "Sleeper league required — ESPN and local profiles have no live roster source, so
NWR will not fabricate availability", "No rows match this view") rather than fabricating data — direct,
positive evidence for the "no fake recommendations where data is missing" requirement. Zero console
errors/exceptions across every navigation and switch in the entire pass.

**Real, disclosed gap**: the governed-2026-projection block (section 3) meant a draft could never
actually be started (`Start Draft` → "Pick could not be recorded — The active Redraft ranking is
unavailable: Governed 2026 projection snapshot is missing", itself an honest, non-fabricating failure,
not a crash). Search/`/`-shortcut, Compare, Player Drawer, Draft Board, and in-draft roster/recent-picks
state-leak could therefore NOT be exercised with live picks in this environment — only the pre-draft
League Chooser / Draft Setup / Weekly Home / Free Agents / Cheat Sheet layers were actually driven.
Both dev servers were cleanly shut down at the end (background Vite task stopped via TaskStop; the
backend's orphaned PID was independently found via `Get-NetTCPConnection` and killed; verified via
`curl` that port 18742 no longer responds). No process left running.

**LEAGUE CHOOSER = PASS. LEAGUE CONTEXT SWITCH = PASS (at the layers reachable without real draft data).
RENDERED ACCEPTANCE = PARTIAL PASS — real, rendered, zero-console-error evidence at every layer this
environment's data gate allows; in-draft/board-level rendering genuinely not reached, disclosed rather
than assumed.**

## 9. In-season inventory (reused from Lane 2/3 archaeology, not rebuilt)

| Capability | Status | Next dependency |
|---|---|---|
| Weekly Home | WORKING (real, honest partial: Data Health + K/DST streamer + free-agent top; Start/Sit etc. labeled "Coming soon") | none for what's built; blocked items below |
| Free Agents | WORKING (Sleeper profiles); correctly BLOCKED (not fabricated) for ESPN/local | live roster source for non-Sleeper providers |
| Opponent Rosters | WORKING (Sleeper profiles) | same as above |
| Sleeper resync | WORKING (read-only, no Sleeper writes) | none |
| K Streamer / DST Streamer | WORKING (pre-existing, untouched) | none |
| Start/Sit | BLOCKED | governed weekly-projection model (does not exist) |
| Waivers (skill-position ranking) | BLOCKED | same weekly-projection gap |
| Add/Drop | MISSING | not attempted (same gap) |
| FAAB | MISSING | not attempted (same gap) |
| Trade Analysis | PARTIAL — real, but Dynasty-app only, not wired into Redraft | a real design decision to wire it in, not attempted |
| Trade Finder | MISSING | depends on Trade Analysis wiring + weekly data |
| Weekly Projections / ROS | BLOCKED | governed weekly-projection model |
| News/Status | WORKING (current-alert intelligence, status overrides incl. new `ADMINISTRATIVE_EXEMPT`) | none |
| Roster Sync | WORKING (Sleeper resync) | ESPN/local live sync source, if ever wanted |
| Matchups/SoS/Playoff Odds | MISSING | live standings store (does not exist) |

## 10. Final regression / performance

- Backend, scoped to every changed area (12 files, superset of the diff's touched services):
  **215 passed, 1 skipped, 8 failed.** 5 of the 8 are the exact documented pre-existing baseline
  (`test_dynasty_facade_composes_real_governed_workflows`,
  `test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`,
  `test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`,
  `test_redraft_league_switching_isolates_draft_state_and_persists_active_profile`,
  `test_facade_has_no_streamlit_or_app_component_dependency`). The other 3
  (`test_parse_udk_position_pdf_*`) are a genuinely NEW-to-this-session finding but confirmed, via
  `git show a72500a6:...`, to be **pre-existing** — this worktree's venv is simply missing the
  `reportlab`/`pdfplumber` test-only dependencies; the UDK-PDF code and its tests predate this branch
  entirely and are untouched by it. **Zero true regressions.**
- Frontend: `tsc -b` clean; full `vitest run` (not just the scoped files) — **16/16 files, 152/152
  tests, 0 failures** (up from lane3's 147 baseline, reflecting this session's 5 new counterfactual
  tests).
- Fresh bootstrap: exercised live via the rendered pass (section 7) — real bootstrap payload served,
  correct "0 profiles" fresh state, no crash.
- 10-team blind draft: section 5 (reused).
- 8-team / 12-team / Superflex smokes (same synthetic-pool method, position caps reused from
  `compute_position_caps`): all three legal-completeness-clean — 8-team 120/120 unique picks in 0.246s,
  12-team 192/192 in 0.326s, Superflex-12 192/192 in 0.327s; zero cap violations, zero illegal picks
  recorded in any of the three.
- League-switch stress test: section 8 (reused).
- Rendered app smoke: section 7 (reused).
- **Latency**: could not measure real live DecisionBundle/Suggestions latency in this worktree (no
  governed projection data to compute a real Suggestions call against — see section 3). The legality
  substitution itself (`evaluate_draft_pick_legality`) is a pure `Counter`-based O(1) check with no
  simulation/I/O, called through the same per-position memoization wrapper
  (`_cached_roster_candidate_allowed`'s successor) as before, so no material latency regression is
  expected from this branch's diff specifically; the real prior benchmark (~8.3-8.9s per Suggestions
  call, ~30-35% improved from ~13.4s, per this session's own memory) is unaffected by anything in this
  diff. This is an inference from reading the code, not a fresh measurement — flagged as such, not
  presented as a measured result.
- No hidden background servers left running (verified via `curl` after cleanup).

## 11. Adoption decision

See the structured handoff below for the full verdict and open items.
