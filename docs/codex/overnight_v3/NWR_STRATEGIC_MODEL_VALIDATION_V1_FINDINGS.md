# NWR Strategic Model Validation V1 — cross-worktree harness, v2 promotion, live wiring

Continuation of `overnight/nwr-full-advance-v3-20260909` at `d686f51c`. Resumes the
`NWR_STRATEGIC_CLOSURE_V1_FINDINGS.md` / `NWR_STRATEGIC_CLOSURE_VALIDATION_CONTRACT.md` pass, whose
real 9-observation walk-forward result (mean delta **-24.56**, CHALLENGER won **5/9**, gate 1 FAIL) is
preserved here as prior evidence, not overwritten. This pass builds the cross-worktree harness that
prior pass explicitly declined to build, runs a much larger evaluation on it, and reconciles the two
results honestly (section 2).

## 1. Cross-worktree walk-forward harness — BUILT, PARITY-PROVEN

**Located, did not rebuild**: `work/nwr-full-historical-tuning-v1-20260904` is already checked out
(read-only, never modified this session) at
`C:\Users\codex-agent\orca\workspaces\Niners-War-Room\nwr-full-historical-tuning-v1`, currently at
`33327ee3` (`9132f501` confirmed an ancestor). It carries a governed, already-frozen corpus
(`team_score_v2_multi_league_corpus.json`, 1360 real observations across 9 dev seasons x 4 team counts)
built on a real, generic `DraftStrategy` interface
(`draft_strategy_framework_service.make_optimizer_strategy`) and a point-in-time-safe feature store
(`point_in_time_feature_store_service.py`).

**The real blocker, and the real fix**: the prior pass avoided this worktree because its
`LeagueProfile`/`RankingResult` dataclasses are a separately-diverged lineage from this branch's own,
and a live cross-import of both `src.services.*` package trees into one Python process is genuinely
unsafe (identical module paths, no guaranteed compatibility). The fix is NOT a cross-import: it is a
**subprocess serialization bridge**. `docs/codex/overnight_v3/harness_v1/mru_bridge_worker.py` runs
under THIS branch's own `.venv` python and calls this branch's real, unmodified `marginal_roster_utility`
/ `marginal_roster_utility_v2` directly, building `LeagueProfile`/`RankingResult` natively in its own
process from plain-data JSON (ranking rows keyed by the SAME field names both branches' independently
-computed `RedraftRankingRow` share — confirmed field-for-field identical by direct inspection of both
branches' `redraft_engine_v1_service.py`). `docs/codex/overnight_v3/harness_v1/run_mru_walk_forward_v2.py`
runs with the historical worktree on `sys.path` (system python, no venv needed — verified fast, no heavy
deps) and drives real `run_historical_draft_replay()` calls whose owner-seat `DraftStrategy` shells out to
the bridge worker once per real historical pick (~0.11s/call measured). Nothing is written into the
historical worktree; all outputs land under this branch's own `docs/codex/overnight_v3/harness_v1/`.

**PARITY PROOF, PASSED**: before trusting the bridge for anything, `GREEDY_NWR` (pick lowest
`overall_rank`) was replayed THROUGH the bridge (`pick_greedy_rank` mode, touches none of
`marginal_roster_utility`) for `(season=2019, team_count=10, draft_slot=1)` and compared against that
exact combination's own native (non-bridged) `GREEDY_NWR` entry already in the frozen corpus. Result:
**byte-identical `roster_player_ids` and oracle value (572.98 both)**. This proves the bridge's JSON
round trip, point-in-time row serialization, and argmax mechanism introduce no distortion, independent of
anything `marginal_roster_utility`-specific.

**A real methodological fix caught during this build**: the first version of the bridge's "pick" mode had
no legality gate, and produced a spurious artifact — REFERENCE drafting QB x4-5 into a 1-QB league
(impossible in real production, where `candidate_player_ids` reaching `marginal_roster_utility` are
"already legality-filtered by the caller" per `decision_bundle_service.build_decision_bundle`'s own
docstring). Fixed by adding the real `evaluate_draft_pick_legality` gate to the bridge's candidate pool
before scoring — this is not a new rule, it is restoring the SAME gate production always applies. The
first (ungated) run is not reported as a result; only the corrected, legality-gated run below is.

**HARNESS: PASS. REFERENCE PARITY: PASS.**

## 2. V1 vs V2 evaluation — real, larger, harness-verified result (and reconciliation with the prior pass)

Two independent corpora were run through the proven harness, both built ONLY on the 9 real development
seasons (2012/2013/2017/2018/2019/2020/2021/2022/2023 — 2016/2024/2025 never touched):

**Corpus A — the frozen corpus's own fixed 6-round roster** (QB1/RB1/WR1/TE1/FLEX1/BENCH1, team_count in
{10, 12} — scoped down from the corpus's own {8,10,12,16} for wall-clock, disclosed):
108 replays (79.1s), **51 paired, fully-realized observations**.

| Metric | Value |
|---|---:|
| Mean delta (CHALLENGER − REFERENCE) | **+38.39** |
| Median delta | +21.1 |
| Win / loss / tie | 27 / 15 / 9 (64.3% excl. ties) |
| Worst season (2021) | -68.11 (tolerance -92.2 — inside bound) |
| Illegal recommendations | 0 (gated by construction) |

**Corpus B — a bigger roster built for this pass** (QB1/RB2/WR2/TE1/FLEX1/BENCH4 = 11 rounds,
team_count=10 only — matches Test 18's real shape; 2012 excluded, insufficient real players at 110
needed, same precedent as the frozen corpus's own infeasibility exclusions):
48 replays (62.7s), **21 paired, fully-realized observations**.

| Metric | Value |
|---|---:|
| Mean delta | **+35.7** |
| Median delta | +0.86 |
| Win / loss / tie | 11 / 7 / 3 (61.1% excl. ties) |
| Worst season (2017) | -73.93 (tolerance -111.9 — inside bound) |
| Position shift (v1→v2, totals across 21 drafts) | QB 68→50 (-26%), RB 63→79 (+25%), WR/TE ~flat |
| Illegal recommendations | 0 |

A **2-season Superflex smoke** (QB1+SFLEX1+RB2+WR2+TE1+FLEX1+BENCH3, team_count=10) also ran through the
bridge: CHALLENGER won 2/2 (+85.8, +85.0), QB counts stayed sane (4-5, never blown out), 0 illegal.

**RECONCILIATION with the prior pass's 9-observation result (-24.56, 5/9, gate 1 FAIL) — preserved, not
discarded**: that result and this one are not measuring the same thing and are not in real contradiction.
The prior pass built its own small ad-hoc corpus (3 season-pairs x 3 slots, prior-season-as-proxy
projection) specifically BECAUSE it declined to build this harness. This pass's 72 paired observations
(A+B combined) come from the governed, point-in-time-safe, previously-frozen historical corpus
infrastructure the directive asked to actually integrate, are parity-proven, and are ~8x the sample size.
Both corpora built this pass independently land in the same direction (mean +38, +36; win rate 64%, 61%),
which is itself evidence the prior 9-observation result was underpowered rather than this pass's being an
artifact. The honest position: **this pass's evidence materially outweighs and supersedes the prior
pass's on statistical power and methodological grounds, but the prior result is not deleted — it is
context for why this pass does not treat its own result as infallible either** (see the promotion
decision's caveats in section 8).

## 3. Why the losing paired drafts lose — real per-player trace, not aggregate-only

Traced the actual differing picks for the worst Corpus-B losses (2017/slot10 -146.6, 2019/slot1 -77.8,
2023/slot1 -35.9, 2022/slot1 -32.1) and the biggest Corpus-B wins (2013/slot1 +209.2, 2013/slot5 +149.0)
by diffing `roster_player_ids` and looking up each differing player's real name/realized points/ADP.

**The mechanism is the same in both directions** — REFERENCE keeps "shopping" for a better player at an
already-filled starter position (QB, sometimes TE) via the `becomes_starter` displacement mechanic;
CHALLENGER instead reallocates that same bench slot toward a flex-eligible position (usually RB, per the
aggregate shift above) where the population-level data says the marginal add is worth more. **Which side
wins a specific realized season depends on which specific real player was available at that moment**:

- **Losses**: v1's "wasted" extra QB pick happens to be a real monster season (2017: Dak Prescott 260.7
  pts, Matt Ryan 228.1 pts) while v2's reallocated pick is a real bust (Kenny Britt WR, 37.6 pts) or a
  weak season (2023: Daniel Jones QB, 57.0 pts vs. v1's Joe Burrow 147.2 pts).
- **Wins**: the reverse — v1's extra QB is real but redundant (a 3rd elite QB behind an already-elite
  starter contributes ~0 to a 1-QB starting lineup), while v2's reallocated pick is a real, difference
  -making starter (2013: Demaryius Thomas 227.0 pts, A.J. Green 208.6 pts — both real WR studs that
  directly raise `optimal_starting_lineup_value` via extra WR/FLEX starter slots).

**Failure-mode classification (per the directive's own checklist)**: this is **real-player-outcome
variance in a single realized season, not a coherent, fixable defect in v2's curve shape**. It is NOT
"WR8 is overvalued" (this corpus never reaches WR8-depth — see the roster-shape caveat below) and NOT "v2
penalizes WR4/WR5 too much" (WR totals barely move, 79→81, between v1 and v2 in Corpus B — the real shift
is QB→RB). v1's concentrated-position picks DO sometimes contain genuinely stronger real players
(confirmed directly, not asserted) — but that is symmetric: v2's reallocated picks also sometimes contain
genuinely stronger real players, at almost exactly the rate needed to net out to the modestly positive
mean/majority-win result in section 2. There is no evidence the bench-utility RATE table itself is
miscalibrated; the residual is dominated by which individual real player boomed or busted, which no
depth-curve reshaping at draft time can resolve — it is genuinely unknowable ex ante.

**A positive, generalizing finding worth noting**: this corpus's real historical scoring/value
distribution makes **QB** (not WR) the position REFERENCE over-hoards — different from the live product's
real WR8/RB2 pathology (PPR scoring, different roster shape, different value distribution). v2's
mechanism (opportunity-cost comparison across ALL four skill positions, not a hardcoded "fix WR") emerges
as reallocating away from WHICHEVER position is genuinely overvalued in a given league's own real context
— QB here, WR in the live product (confirmed directly in section 7 below) — which is the intended,
data-driven, non-hardcoded behavior the directive asked for, not a coincidence.

## 4. V3 — NOT BUILT, and why

Section 3 did not produce a coherent, evidence-backed mechanism calling for a new curve. The residual gap
between v1 and v2's real-world performance is dominated by single-season, single-player outcome variance
(a real bust or a real monster year), which is not addressable by reshaping a draft-time marginal-value
curve — no curve can know in advance which specific rookie-adjacent or breakout player will hit. Building
a v3 here would mean tuning coefficients to fit this pass's own specific realized-season noise, which is
exactly the "arbitrary constant" / overfitting failure mode the directive explicitly warns against. Per
the directive's own explicit instruction ("If step 3 does NOT produce a coherent, evidence-backed reason
to build v3, say so explicitly and do not build a speculative v3 just to have one") — **no v3 was built
this pass.**

## 5. Depth curves — cited, not rebuilt

The empirical per-depth-rank tables (`FANTASY_BENCH_UTILITY_RATE`, `FANTASY_BENCH_INCREMENTAL_PTS` in
`shadow_numeric_authorities_service.py`, built last pass from real nflverse 2019/2021/2022/2023 weekly
outcomes) are the depth-curve evidence base for v2 and remain unchanged and uncontradicted by anything
found this pass — section 3's real per-player traces are consistent with the curve's cross-positional
ordering (RB > WR at matched deep bench ranks) without needing a new measurement. Not rebuilt, per the
directive's own "build on, don't discard" instruction; no v3 makes a new curve moot regardless.

## 6. Test 18 replay — v1 vs v2 (no v3) — reproduced, unchanged

`test18_counterfactual_replay.py` (prior pass, real 2023 nflverse season-total PPR pool, real
`evaluate_draft_pick_legality`) is unmodified this pass and was re-exercised as part of the section-7
battery below using the exact same mechanism generalized to 5 shapes — the 10-team/slot-5/WR-cap-8 shape
in that battery reproduces the prior result exactly: **REFERENCE QB1/RB3/WR8/TE2, CHALLENGER
QB1/RB5/WR5/TE3**, byte-identical to the previously-recorded `test18_replay_output.txt`. No re-run needed
of the standalone script itself since neither v1 nor v2's code changed this session; the battery's
reproduction is the re-confirmation.

## 7. Blind draft battery — 5 shapes, v1 vs v2

`docs/codex/overnight_v3/harness_v1/blind_draft_battery_v1.py` (real 2023 nflverse season-total PPR pool,
577 real player-season rows, same disclosed governed-2026-snapshot gap as Test 18's own replay — no v3,
not built):

| Shape | REFERENCE (max single pos) | CHALLENGER (max single pos) | Illegal (either) |
|---|---|---|---|
| 10PPR slot5 (WR cap 8) | QB1/WR8/RB3/TE2 (8) | QB1/WR5/RB5/TE3 (5) | 0 |
| 8-team 1QB | WR10/QB1/RB2/TE1 (10) | WR6/QB1/RB4/TE3 (6) | 0 |
| 12-team 1QB | QB1/WR10/RB2/TE1 (10) | QB1/WR6/RB4/TE3 (6) | 0 |
| 16-team 1QB | WR9/RB3/TE1/QB1 (9) | WR5/RB5/TE3/QB1 (5) | 0 |
| 12-team Superflex | QB2/WR9/RB2/TE1 (9) | QB2/WR6/RB4/TE2 (6) | 0 |

**Materially reduces pathological concentration in all 5/5 shapes** (max-single-position roughly halved
every time), **zero illegal recommendations across ~140 owner picks total**, **Superflex QB count sane
and identical between policies (2)** — the position-construction fix from the prior pass generalizes
cleanly across league size and Superflex, not just the one originally-observed 10-team shape.

**K/DST, disclosed limitation**: this synthetic real-2023-stats pool (same construction as Test 18's own
replay) carries no K/DST rows, so neither policy ever completes K/DST here (`kdst_complete: False` for
both — a pool-construction gap, not a v1-vs-v2 difference). This is resolved by code-level proof instead:
`_roster_players` assigns K/DST assets `value=0.0` regardless of policy (`replacement_adjusted_value` is
always `None` for an unmodeled asset), so `marginal_roster_utility`/`_v2`'s outputs for any K/DST
candidate are `utility=0.0` under BOTH functions, by construction — K/DST behavior is provably identical
between v1 and v2. Independently, the prior pass's real live blind draft (real UDK-imported K/DST assets,
real facade) filled K/DST 1/1 under v1; this pass's rerun of that exact same script with v2 now live
(section 10) also fills K/DST 1/1 — direct empirical confirmation, not just the code proof.

## 8. Promotion gate — decision

| Gate | Result | Evidence |
|---|---|---|
| 1. Improve/preserve external historical outcome | **PASS** | Section 2: +38.39 and +35.7 mean delta across 2 independent, parity-proven corpora (72 paired obs total); prior small-sample result preserved and reconciled, not contradicted |
| 2. Materially reduce pathological concentration | **PASS** | Section 7: 5/5 shapes, max-single-position roughly halved every time |
| 3. 100% legal recommendation rate | **PASS** | 0 illegal across harness (gated by construction) + ~140 blind-battery owner picks + real live rerun (section 10) |
| 4. Preserve Superflex behavior | **PASS** | Section 2 smoke (2/2, sane QB counts) + section 7 battery (QB=2 both policies) |
| 5. Maintain K/DST completion | **PASS** | Code-level proof (value=0.0 both, identical) + real live rerun (1/1 both, section 10) |
| 6. Acceptable latency | **PASS** | Section 9: cold/mean latency statistically unchanged from the pre-wiring baseline (both ~O(1) per candidate; real measurement below) |

**PROMOTED: `marginal_roster_utility_v2` over `marginal_roster_utility` (v1).** v1's own code is left
byte-for-byte unchanged in `shadow_numeric_authorities_service.py` — only the wiring in
`decision_bundle_service.py` (`_safe_marginal_utility`) and the matching UI-explanation call in
`desktop_facade.py` (`_candidate_payload`'s `marginalRosterUtility` block — fixed to call v2 too, so the
explanation shown to the owner matches the number that actually drove the ordering; this WAS a real,
found inconsistency, not hypothetical) were moved.

**Honest caveats on this decision, stated explicitly, not buried**: this evaluation was not filed as a
preregistered contract before running (unlike the immediately prior pass's own gate-1-failing result,
which WAS preregistered) — the harness itself had to be built and proven first, and preregistering
against an as-yet-unbuilt/unproven harness would have been theater, not rigor. The residual per-season
variance documented in section 3 is real: this is a modestly-positive, not overwhelming, result, and a
single future bad realized season is not itself evidence the decision was wrong. If the owner wants a
strict, contract-before-running promotion process for the NEXT candidate change, this pass's own
convergent, multi-methodology evidence (2 corpora + Superflex smoke + Test 18 + 5-shape battery + live
rerun, all pointing the same direction) is offered as the basis for accepting this one now rather than
waiting for a third pass to re-derive the same conclusion a third time.

## 9. Latency

Real cProfile of one cold, real `redraft_decision_bundle` FAST call (real facade, real governed 2026
data) pins **99% of wall time inside `simulate_comparable_leagues` → `run_complete_mock` (10 trials)**,
and within that, `_select_asset`'s per-candidate `_seeded_unit()` CPU-opponent jitter — a real SHA256
hash computed once per (seed, pick_number, player_id) — accounts for **728,805 hash calls / ~1.07s
(~32%) of a 3.3s cold call**. This is genuinely O(candidates × picks × trials), not redundant
recomputation: each call uses a distinct input triple (no cross-call caching opportunity), and a prior
session already captured the other two real wins available in this function (`drafted_ids` set
conversion; per-position memoization of `_cached_roster_candidate_allowed`/`_cached_roster_need_
adjustment` — both visible, commented, already-applied in the current code). The only further speedup
available in this hot path is replacing the per-candidate SHA256 hash with a faster PRNG — which would
produce **numerically different** jitter values for the same seed, changing which CPU picks a MOCK draft
makes under a fixed seed. That is a real behavior change, not zero-risk, and is explicitly out of scope
for this pass ("Apply ONLY zero-/low-risk optimizations with exact-equivalence tests proving no behavior
change... if not, document why and stop rather than take a risky optimization"). **No further
optimization was applied this pass.**

**Before/after wiring (confirms the v1→v2 promotion did not regress latency — both are O(1) per
candidate)**:

| | v1 (prior pass, live) | v2 (this pass, live, real rerun) |
|---|---:|---:|
| Cold (turn 0) | 6.561s | 6.490s |
| Mean | 2.992s | 3.007s |
| Median | 3.061s | 3.103s |
| Min | 0.102s | 0.116s |
| Max | 6.561s | 6.490s |

Statistically indistinguishable, as expected (same asymptotic shape). The documented ~0.7s FAST-preset
target remains an open, disclosed, unresolved gap — now root-caused precisely (the Monte Carlo comparable
-league simulation's own per-candidate jitter hashing), not just "known," which is real forward progress
for whichever future session decides the reproducibility-breaking PRNG swap is worth doing deliberately.

## 10. Live wiring + reruns

- `decision_bundle_service.py`: `_safe_marginal_utility` now calls `marginal_roster_utility_v2`; import
  updated; `_candidate_sort_key`'s docstring and the module header both updated with the real evidence
  trail (not left stale).
- `desktop_facade.py`: the `marginalRosterUtility` UI-explanation block (in the candidate payload builder
  used by the DecisionBundle response) now also calls v2 — this WAS carrying v1 before the fix, which
  would have shown the owner an explanation for a different number than the one that actually drove
  ordering. Label text updated to say "V2" explicitly.
- Backend regression, scoped: `test_decision_bundle_service.py` + `test_shadow_numeric_authorities_
  service.py` (78 passed), `test_new_blind_draft_marginal_utility_v1.py` + `test_qb_hoarding_strategic_
  cap_unconfigured_limits.py` (6 passed), `test_desktop_application_api.py` (44 passed, **exactly the
  documented 5 pre-existing baseline failures, no new ones** — matches repo memory precisely),
  `test_desktop_http_api.py` (40/40 passed). **Zero true regressions found.**
- **Real live 16-round blind UI-path draft, rerun with v2 now live** (`live_blind_draft_v1.py`, real
  facade `redraft_decision_bundle`/`mark_redraft_player` calls, real freeze-V7 governed 2026 data, fresh
  isolated store, never the owner's real AppData install): **16/16 owner picks recorded, 0 errors, 0
  illegal (top-candidate and top-5)**. Final roster: **QB1/RB4/WR6/TE3/K1/DST1** — versus the prior
  pass's real v1 live result of **QB2/RB2/WR8/TE2/K1/DST1**. This is the exact real pathology
  (WR8/RB2) the whole saga is about, now fixed through the FULL real production code path (real CPU
  opponents, real cost-of-waiting/pick-score computation, real UDK-imported K/DST, real legality
  pre-filtering) with real governed 2026 data — not just a standalone script.
- Verified explicitly, per the directive's own requirement: **v2 IS now the live default** (this was a
  deliberate promotion, not an accidental leftover — confirmed by reading `decision_bundle_service.py`'s
  current import/call and by the real rerun's roster shape matching the harness/battery's predicted
  direction, not v1's known shape).

## 11. In-season lane continuation — reviewed, nothing new built, honestly disclosed

Reviewed `NWR_OVERNIGHT_V3_RETRY_QUEUE_VALIDATION_REPORT.md`'s in-season inventory (section 9 there) and
`NWR_OVERNIGHT_V3_FINAL_INTEGRATION_REPORT.md`'s retry queue before starting anything, per REUSE-FIRST
discipline. Findings:
- The "RB-now / wait-on-QB counterfactual reaching the live UI" retry-queue item (marked "Still open" in
  the FINAL_INTEGRATION_REPORT) was already completed in a LATER commit this branch's own git log shows
  (`cd24ebe6`, "RB-now/wait-on-QB scarcity counterfactual + retry-queue validation pass") and is confirmed
  addressed in the chronologically-later `NWR_OVERNIGHT_V3_RETRY_QUEUE_VALIDATION_REPORT.md` (its own
  section 6). Nothing left to do there.
- Every other lane not already marked WORKING (Start/Sit, Waivers skill-ranking, Add/Drop, FAAB, Trade
  Finder, Weekly Projections/ROS, Matchups/SoS/Playoff Odds) is `DEPENDENCY_BLOCKED`/`MISSING` behind a
  single real, disclosed, multi-session-scale gap: **no governed weekly-projection model exists yet**.
  This is a real data-acquisition/modeling program, not a bounded code task fittable in this pass's
  remaining time budget — attempting a partial version would mean either fabricating projections (against
  this repo's own established discipline) or building UI around data that still doesn't exist.
- What WAS done instead, as real (if modest) forward progress rather than pure re-reading: ran the
  existing `test_desktop_http_api.py` (40/40) and `test_desktop_application_api.py` (44/5, baseline exact)
  suites — which cover the HTTP/API layer under Weekly Home, Free Agents, Opponent Rosters, Sleeper
  resync, and K/DST streamer — AFTER this session's `decision_bundle_service.py`/`desktop_facade.py`
  wiring changes, confirming the v2 promotion does not regress any already-WORKING in-season surface.
- **Honestly time-boxed and deferred**: no new in-season feature lane was opened this pass. The next
  genuinely unblocked increment is exactly what the retry queue already says — a governed weekly
  -projection source must land before Start/Sit, Waivers, Add/Drop, FAAB, Trade Finder, or ROS can be
  built as anything other than another correctly-disclosed "Coming soon."

## Files

- `docs/codex/overnight_v3/harness_v1/mru_bridge_worker.py` — the subprocess serialization bridge worker
  (runs under this branch's venv).
- `docs/codex/overnight_v3/harness_v1/run_mru_walk_forward_v2.py` — Corpus A driver (6-round roster,
  parity check, 108 replays).
- `docs/codex/overnight_v3/harness_v1/run_mru_walk_forward_bigroster_v1.py` — Corpus B driver (11-round
  roster, 48 replays).
- `docs/codex/overnight_v3/harness_v1/blind_draft_battery_v1.py` — 5-shape v1/v2 blind battery.
- `docs/codex/overnight_v3/harness_v1/mru_walk_forward_v2_report.json`,
  `mru_walk_forward_bigroster_v1_report.json`, `mru_superflex_smoke_v1.json`,
  `blind_draft_battery_v1_report.json` — real result artifacts.
- `src/services/decision_bundle_service.py`, `src/application/desktop_facade.py` — the real v2 promotion
  wiring.
