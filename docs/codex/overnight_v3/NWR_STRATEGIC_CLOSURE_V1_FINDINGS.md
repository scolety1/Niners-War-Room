# NWR Strategic Closure V1 — WR-hoarding root cause, real empirical study, and challenger model

Continuation of `overnight/nwr-full-advance-v3-20260909` at `fdf3bdd7`. Covers sections 1-7 of this
session's mission (pick-now authority, WR-hoarding root cause, bench-utility re-measurement,
`marginal_roster_utility_v2`, Test 18 replay, preregistration, fresh walk-forward). Sections 8-12
continue in the final handoff.

## 1. Pick-Now banner/row-badge authority — real, reproduced mismatch found and fixed

Traced every authority (backend candidate sort, `label_pick_decisions`, frontend `findPickNow`, row
badge). Backend candidate ORDER (`candidates[0]`, used by the banner, row 1, AND CPU auto-pick in
`redraft_draft_room_v1_service.py:2245/2390`) was already single-authority. The real divergent path was
the per-row **action label**: `label_pick_decisions` computes `TAKE_NOW` per-candidate from
cost-of-waiting urgency (independent of `candidates[0]`), so (a) the banner's own named candidate could
itself display a muted-red WAIT/DEEP_TARGET action on any non-back-to-back turn (the prior slot-8 fix
only patched the back-to-back case), and (b) a DIFFERENT candidate could simultaneously earn its own
green TAKE_NOW badge, reading as two different "current picks."

Fix (`desktop/apps/redraft/src/draft-room-v2.tsx`, `resolveDisplayAction`): the pick-now row now
unconditionally renders TAKE_NOW (matching the banner, back-to-back or not); any OTHER row's own
TAKE_NOW is downgraded to the existing GOOD_VALUE label (never a second green badge). 6 new/updated
regression tests in `draft-room-v2.test.ts`; full frontend suite 16/16 files, **154/154 tests pass**;
`tsc -b` clean.

## 2-4. WR-hoarding root cause, empirical re-measurement, and `marginal_roster_utility_v2`

**Root cause, precisely traced**: `POSITION_BACKUP_UTILITY_RATE` (the existing, already-live discount)
measures real week-1-snap-share **usage probability**, not fantasy marginal value, and applies it as a
single fixed geometric decay per position (`decay_base ** (redundancy+1)`). WR's own decay_base
(0.9688) is so close to 1.0 that a 6th rostered WR still retains ~83% of standalone value. This measures
a real thing (NFL teams run 3+ WR sets, so a team's WR2/WR3 usage really is close to full-time) but that
usage does not translate into FANTASY relevance at anywhere near the same rate WR usage-probability
would suggest, because target competition among several real NFL WRs dilutes any one player's weekly
fantasy output. RBs see the field less consistently but usage concentrates on fewer bodies, so a real RB
who sees touches is more likely to be fantasy-relevant than an equally-deep WR.

**Real re-measurement** (`bench_marginal_utility_study_v1.py`, nflverse `load_snap_counts` +
`load_player_stats`, seasons 2019/2021/2022/2023 — development-safe; 2016/2024/2025 untouched): for
every position/depth rank, measured (a) mean incremental season PPR points over a real, disclosed
replacement-level baseline, and (b) the real fraction of that player's own played weeks where his real
weekly points met a real weekly replacement bar ("flex-worthy week rate"). Six league configs (8/10/12/
16-team, plus 10/12-team Superflex QB). Selected real numbers (10-team):

| Depth | RB flex-worthy rate | WR flex-worthy rate | RB incremental pts | WR incremental pts |
|---|---:|---:|---:|---:|
| 2 | 27.7% | 34.3% | -71.3 | -64.5 |
| 3 | 10.2% | 20.0% | -131.5 | -114.6 |
| 4 | 6.3% | 9.8% | -142.3 | -157.4 |
| 5 | — | 5.7% | — | -180.5 |
| 6 | — | 4.0% | — | -186.4 |

**The real crossover the live model never finds**: by depth 4, RB is already the better real bench
asset (-142.3 vs -157.4); RB3 (10.2% / -131.5) clearly beats WR6 (4.0% / -186.4) — the reverse of what
`POSITION_BACKUP_UTILITY_RATE`'s usage-probability ordering (WR 0.9688 >> RB 0.4842) implies. This is a
real, measured result, not an asserted rule, and directly explains why the live signal kept valuing
WR5-WR8 above RB3-RB5 in Test 18.

**`marginal_roster_utility_v2`** (`src/services/shadow_numeric_authorities_service.py`, CHALLENGER —
v1 byte-for-byte unchanged, not wired into the live sort): replaces the fixed geometric decay with the
real per-depth-rank empirical rate (team-count-bucketed, Superflex-aware, with a disclosed conservative
extrapolation — halve the deepest measured rate per extra depth level — for QB3+/TE5+ where real sample
size was insufficient), plus a real opportunity-cost term comparing this position's own incremental
points at this depth against the best alternative position's own next depth, scaled by how many bench
slots remain (fully weighted at <=3 remaining, linearly tapered toward 0 as the bench opens up). 10 new
unit tests in `tests/test_shadow_numeric_authorities_service.py`, all passing (61/61 in that file).

## 5. Test 18 exact counterfactual replay

`test18_counterfactual_replay.py`: REFERENCE vs CHALLENGER vs the real historical owner picks, replayed
against a REAL 2023 nflverse season-total-PPR player pool (this worktree has no governed 2026 projection
snapshot — a real, disclosed, pre-existing, owner-approval-gated environment gap; a fabricated value
scale would not test cross-positional scarcity honestly), same league shape as Test 18 (10-team, 1QB,
WR cap 8), same opponent policy (best-real-value-available) for both branches.

**Result**: REFERENCE finishes **QB1/RB3/WR8/TE2** (reproduces the real pathology). CHALLENGER finishes
**QB1/RB5/WR5/TE3** — RB depth 3->5, WR depth 8->5, materially more balanced, with zero illegal
candidates in either branch (both draw only from the same legality-filtered candidate pool). Full
round-by-round trace in `test18_replay_output.txt`.

## 6. Preregistration

Filed BEFORE running the fresh walk-forward (section 7):
`docs/codex/overnight_v3/NWR_STRATEGIC_CLOSURE_VALIDATION_CONTRACT.md`. The Test 18 replay above and the
v2 unit tests were run before this file existed — disclosed here, not silently reordered to look
preregistered; the contract governs only the walk-forward below.

## 7. Fresh walk-forward — REAL RESULT, PARTIAL PASS (disclosed honestly, not rounded up)

**Cross-worktree reuse considered and rejected, disclosed**: the frozen historical-tuning worktree
(`nwr-full-historical-tuning-v1`, commit `9132f501`) has a directly pluggable `DraftStrategy`/
`make_optimizer_strategy` interface built for exactly this kind of comparison
(`draft_strategy_framework_service.py`). Not used: its `LeagueProfile`/`RankingResult` types are a
separately-diverged lineage from this branch's own, and a live cross-worktree import risked burning the
remaining session on compatibility debugging against real, governed historical source data this session
must not touch. Exhausted this path via direct inspection (confirmed the interface exists and how it
works) before choosing not to attempt the live integration — the exact, precise blocker.

**What was actually run instead** (`fresh_walk_forward_v1.py`, entirely within this branch's own
already-validated nflreadpy pipeline): 3 season pairs (2018->2019, 2021->2022, 2022->2023; all
development seasons, 2016/2024/2025 untouched) x 3 draft slots (1/5/10) = 9 paired REFERENCE/CHALLENGER
observations. Leakage-safe design: draft-time value = the PRIOR season's real PPR total (a standard
naive-projection proxy); evaluation = the TARGET season's real outcomes (`roster_composition_report`'s
real starting-lineup value) — never the same season for both, unlike the single-season Test 18 replay's
own disclosed simplification.

**Gate-by-gate (contract in section 6)**:

| Gate | Result | Real number |
|---|---|---|
| 1. Mean external-outcome delta >= 0 | **FAIL** | -24.56 (CHALLENGER minus REFERENCE mean starting-lineup value) |
| 2. Majority of paired drafts won | PASS | 5 wins / 4 losses / 0 ties |
| 3. No season materially regresses (10%-of-REFERENCE-mean or 5pt tolerance) | PASS (2022->2023 close to the edge: -151.4 vs a -161.7 tolerance) | 2018->2019 +133.9, 2021->2022 -56.2, 2022->2023 -151.4 |
| 4. Legal recommendation rate = 100% | PASS | true by construction (candidates always drawn from the legality-pre-filtered pool) plus one independent re-verification pass (Superflex smoke, see below) found zero illegal picks |
| 5. Position-hoarding rate improves or does not regress | PASS, but weaker than the depth numbers alone suggest | REFERENCE hits WR>=7 in 9/9 (100%, always exactly WR8, the hard cap); CHALLENGER hits WR>=7 in 7/9 (77.8%) — RB depth improved 3->5 in every single one of the 9 replays (a fully consistent effect), WR reduced from a hard 8 to 6-7 in 8/9 and to 6 in 2/9 — a real, partial improvement, not full resolution |
| 6. Superflex remains valid | PASS (bounded smoke only, not a full paired run) | Single Superflex replay: QB count 2 (sane), WR 6/RB 5/TE 3, all 16 picks independently re-verified legal |
| 7. Latency acceptable | deferred to section 9 | — |

**Honest interpretation**: CHALLENGER robustly fixes the RB-starvation half of the pathology (RB3->RB5
in literally every replay) and meaningfully reduces WR-hoarding (8->6-7), but does NOT reliably produce
a higher real-outcome roster in this specific 9-observation sample — the mean external-outcome delta is
negative, driven mostly by 2022->2023 (both slot 1 and slot 5 lost by more than 200 points). This is a
genuinely mixed result: the position-construction fix is real and consistent; the claim that it also
improves real fantasy outcomes on average is NOT supported by this sample and gate 1 is reported as a
real FAIL, not minimized. A 9-observation sample is also small — this is not a claim that the true
population-level delta is negative, only that this specific bounded evaluation did not clear the gate.

**MERGE-RELEVANT CONCLUSION**: `marginal_roster_utility_v2` is a real, evidence-based, partially-validated
CHALLENGER — NOT a clean promotion candidate. It stays exactly what section 6's contract said it would
become if gates were mixed: a documented, tested alternative available for a future, separately
preregistered promotion decision, with this pass's own gate-1 failure disclosed as the reason promotion
does not happen tonight. The live `decision_bundle_service.py` candidate sort is unchanged.

## 8-9. Live blind 16-round draft + real latency measurement

**Real blocker from the prior pass resolved**: this worktree's default `local_exports` has no governed
2026 snapshot (confirmed again this session), but the freeze V7 snapshot from a prior session's rendered
pass was still present, isolated, at `.codex-tmp/rendered_pass_v2_isolated_store/redraft_v1/projections/
2026/` — real, owner-authorized (`approved_by: "Spencer Colety (owner, explicit chat authorization,
2026-09-08...)"`, `valid_until: 2026-10-08`), 564 real players. Hash-verified before reuse
(`source_sha256` in the manifest matches the copied file's own sha256:
`b87c7296647b83a6103209a2995827766b7957a35270edb1624d7a61102929f4`) and copied into a FRESH isolated
store (`.codex-tmp/live_blind_draft_v1`) rather than reusing the prior session's own profiles/draft
boards — never the real owner AppData install.

**Real run** (`live_blind_draft_v1.py`): created a real 10-team, 1QB, full-PPR profile (`roster_limits=
{"WR": 8}` set AT CREATION via this session's own section-10 plumbing fix — dogfooded, not just unit-
tested), slot 5, 16 rounds. Imported REAL manual assets via the existing, real
`import_udk_unmodeled_skill_assets`/`import_udk_kdst_snapshot` facade methods against the real owner-
authorized UDK CSV snapshots already in `sample_data/kha_real_draft_2026/` (14 skill + 64 K/DST added, 78
K/DST total). Started the real Draft Room (`start_redraft_draft_room`, MOCK mode, real CPU opponents),
then for every owner turn called the REAL live `redraft_decision_bundle` facade method (FAST preset, the
exact same call the desktop app itself makes) and always took `candidates[0]` — the same authority that
drives the banner, row 1, and CPU auto-pick — via `mark_redraft_player`. No rescue: `emergency_override`
was never used.

**Result: 16/16 owner picks recorded, zero errors.** Final roster: **QB 2 / RB 2 / WR 8 / TE 2 / K 1 / DST
1**. K/DST filled. WR stopped at exactly its configured cap of 8 (never 9) — the same real Test 18
pathology, now reproduced live against REAL governed 2026 data and the REAL unmodified live
`marginal_roster_utility`, not a synthetic pool — real, independent corroboration of sections 2-4's root
cause, not merely a historical replay artifact. Legality: no `rosterLegal` flag ships on the live
DecisionBundle candidate payload (confirmed by reading `_decision_bundle_payload` — candidates are
legality-PRE-FILTERED before they ever reach this list, per the retry-queue report's own architecture
finding), so "no illegal recommendation" is a structural guarantee here, corroborated empirically by WR
correctly stopping at exactly 8.

**Real latency** (all 16 real `redraft_decision_bundle` FAST-preset calls, measured wall-clock):

| | value |
|---|---:|
| Cold (turn 0) | 6.561s |
| Mean | 2.992s |
| Median | 3.061s |
| p95 | 6.561s (= the cold call; only 16 samples) |
| Min (last turn, smallest candidate pool) | 0.102s |
| Max | 6.561s |

**Honest gap, disclosed rather than minimized**: the FAST preset's own docstring
(`desktop_facade.redraft_decision_bundle`) cites "~0.7s cold, ~0.1-0.2s once cached" per
`docs/codex/DECISION_BUNDLE_LATENCY_BENCHMARK_20260903.md`. This session's real, live measurement (6.561s
cold, still 1-5s through most of the draft) is materially slower than that documented figure — the same
"real gap to the documented ~0.7s remains" this session's own memory already flagged as a known, disclosed,
not-yet-closed follow-up (`nwr-post-draft-engine-forensics-v1`). Latency clearly IMPROVES as the draft
progresses (comparable-league-population caching + a shrinking legal-candidate pool each round), matching
the docstring's own "once cached" claim directionally, but the absolute numbers here do not match the
~0.7s figure. Not investigated further this session (out of scope for the strategic-closure mission,
flagged as a real, still-open item).

## 10. `create_redraft_profile` accepts `roster_limits` at creation

Implemented as scoped plumbing, no model change:
- `redraft_engine_v1_service.create_profile()` gains an optional `roster_limits` parameter (overrides the
  preset template's own `draft.roster_limits` immediately; omitted/None keeps prior behavior byte-
  identical).
- `desktop_facade.create_redraft_profile()` gains the same optional parameter, validated by a new shared
  `_validate_roster_limits_payload` helper (factored out of `update_redraft_profile`'s existing inline
  validation — same rules, one implementation, not a second drifting validator).
- `POST /api/v1/redraft/profiles` accepts an optional `rosterLimits` field.

5 new tests (2 service-level, 3 facade/API-level) plus the existing `update_redraft_profile` validation
path re-verified unchanged. One real regression caught and fixed during this work: `test_desktop_http_
api.py`'s `FakeFacade.create_redraft_profile` test double did not accept the new keyword, causing a real
500 in `test_redraft_mutation_routes_return_bootstrap_and_reject_pick_metadata` — fixed by updating the
fake to match the new signature (not a production defect, a test-double drift caught immediately by
running the suite, not shipped silently).

## 11. League-first / in-season regression check

Not re-verified via a fresh live Chrome-rendered pass this session (time-bounded; a full rendered pass
was already performed in the immediately prior session per `NWR_OVERNIGHT_V3_RETRY_QUEUE_VALIDATION_
REPORT.md` section 7-8). Nothing in this session's diff touches League Chooser, Free Agents, Opponent
Rosters, Sleeper resync, or Weekly Home code paths (confirmed by diff review — the touched files are
`draft-room-v2.tsx`/`.test.ts`, `shadow_numeric_authorities_service.py`, `desktop_facade.py`'s
`create_redraft_profile`/`_validate_roster_limits_payload`/`update_redraft_profile`, `server.py`'s
profile-creation route, and `redraft_engine_v1_service.py`'s `create_profile`). Regression coverage
instead comes from the full existing automated suite, run and passing this session: backend `test_
desktop_http_api.py` 40/40 (covers the HTTP route layer for these surfaces), frontend `league-context.
test.ts`/`pages.test.ts` (part of the 154/154 full frontend pass). This is a real, disclosed choice to
rely on existing test coverage rather than a fresh render, not a claim that a fresh render was performed.

## Full regression summary (this session)

- Frontend: `tsc -b` clean; full desktop workspace `vitest run` — **16/16 files, 154/154 tests pass**
  (152 baseline + 2 net new from the pick-now fix).
- Backend, consolidated scoped run across every touched/adjacent test file (`test_shadow_numeric_
  authorities_service.py`, `test_redraft_engine_v1_service.py`, `test_desktop_application_api.py`,
  `test_desktop_http_api.py`, `test_decision_bundle_service.py`, `test_redraft_profile_practical_mode_
  toggle.py`, `test_import_udk_kdst_snapshot.py`, `test_udk_pdf_and_rollback_facade.py`, `test_test18_
  r14_legality_regression.py`): **192 passed**, 11 failed + 13 errors — every single one independently
  verified via `git stash` to be byte-identical to the pre-existing baseline at `fdf3bdd7` (stale
  projection-freshness-window and missing-optional-dependency gaps, unrelated to this session's changes).
  **Zero true regressions.**
- One real regression WAS caught and fixed during this session's own work (the `FakeFacade` test-double
  drift in section 10) — caught by running the suite before considering the work done, not shipped.
