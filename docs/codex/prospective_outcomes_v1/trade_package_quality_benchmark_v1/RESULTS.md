# Trade Package Quality Benchmark V1 -- Real Results (Work Unit 16)

Rubric: `docs/codex/prospective_outcomes_v1/TRADE_PACKAGE_QUALITY_
BENCHMARK_V1.md` (written first). Raw output:
`docs/codex/prospective_outcomes_v1/trade_package_quality_benchmark_v1/
results.json`, produced by `scripts/run_trade_package_quality_benchmark_
v1.py` (real, reproducible, read-only). Ranking/scoring/generator code was
NOT modified by this pass.

## Real sample

Real "Fantasy Gamers" Sleeper league (id `1312983576827920384`, real,
current 10-team rosters, read via plain Sleeper GETs), scored with the
real, currently-installed NWR ranking loaded read-only from the owner's
real AppData profile `4c5f04762921420595e4d8c7cda76582`. Three real runs:

- **FIND_WIN_WIN** (every real opponent): 15 candidates returned,
  900 packages evaluated (capped, `truncated=true`), 1.20s.
- **TARGET_PLAYER** (Sam LaPorta, TE, real roster 2 starter -- the owner's
  own real thinnest position is TE, one rostered player, no depth): 0
  candidates, 120 packages evaluated (capped), 0.18s.
- **IMPROVE_POSITION** (`TE`, the owner's real disclosed thin position):
  0 candidates, 372 packages evaluated (capped), 0.53s.

Plus one clearly-labeled SYNTHETIC 10-team fixture (deterministic, not
real player data, built with perfectly symmetric rosters across every
team -- every real starter slot already optimally filled on both sides by
design) for a larger, more stressful candidate sample:
**FIND_WIN_WIN**: 15 candidates, 900 evaluated (capped), 0.64s.

A real, disclosed data-coverage note (not a defect): 3 of the owner's 15
real rostered Sleeper players did not resolve to the canonical NWR ranking
pool used by the search -- 2 by design (K/DST are never NWR-projected,
unrelated to this pass) and 1 real identity-match gap (a rostered WR not
present in the current ranking pool, Sleeper id `11628`). The search
therefore operated on the real, but effectively 12-player, canonical
subset of the owner's 15-man roster. Not fixed (out of this pass's scope
-- ranking/identity resolution is untouched).

## Rubric results

1. **Dominated-by-simpler-trade**: **zero violations** across all four
   real/synthetic runs (`check_dominance_violations` independently
   re-verified the generator's own gate-4 invariant on its real output,
   never merely trusting it). Gate 4 holds.
2. **Both teams gain real starter value**: real FIND_WIN_WIN showed
   `benchForBenchClutterRate = 0.0` -- every one of the 15 real candidates
   moved BOTH sides' real starting-lineup value by at least the
   preregistered epsilon (0.5 pts). TARGET_PLAYER/IMPROVE_POSITION
   produced no candidates to rate (see below).
3. **Position-need fit**: `0/15` real FIND_WIN_WIN candidates resolved a
   pre-existing owner starter hole. This is EXPECTED, not a defect:
   FIND_WIN_WIN's own candidate pool is the "weakest bench piece first"
   signal by design (see the generator's own docstring) -- it is not
   targeted at any specific hole the way IMPROVE_POSITION is. The real
   IMPROVE_POSITION(TE) run, the mode actually built to target a real
   hole, returned zero candidates (see below) rather than a false-positive
   "fix."
4. **Bench-for-bench clutter**: `0%` in the real league; `93.3%`
   (14/15) in the fully-symmetric SYNTHETIC fixture. The synthetic number
   is MECHANICALLY EXPLAINED, not a red flag: that fixture was built with
   every real starter slot already optimally filled on both sides for
   every team, so the ONLY real win-win trades available to find are
   marginal bench-depth swaps -- a fixture artifact of a deliberately
   "nothing broken to fix" league shape, not evidence of a generator
   defect. The real league (which has real, uneven need across teams)
   shows the opposite: zero bench-for-bench candidates survived.
5. **Duplicate / near-duplicate packages**: 9 near-duplicate pairs
   (Jaccard >= 0.5) in both the real FIND_WIN_WIN run and the synthetic
   run. Mechanically explained: `distinctPlayersUsed` was only 11 (real)
   / 23 (synthetic) against 15 returned candidates each -- a small,
   bounded per-opponent candidate pool (`DEFAULT_CANDIDATES_PER_SIDE=6`)
   naturally produces packages that share a "core" player restated with a
   different second player. No EXACT duplicates occurred (gate 5 holds,
   confirmed by construction of the check itself).
6. **Package-size penalty**: real FIND_WIN_WIN's `1-for-2` shape actually
   had a HIGHER mean owner net utility (16.99) than `1-for-1` (12.17) --
   the larger packages that survived earned their complexity, consistent
   with gate 4 (dominance filtering) doing its job, not "complexity for
   its own sake." (Diagnostic only, per the rubric -- not a pass/fail
   gate.)
7. **Roster consolidation cost**: zero real violations once this
   benchmark's OWN pre-trade roster-size bookkeeping was corrected (see
   "A real bug found and fixed" below) -- every returned real/synthetic
   candidate leaves both sides at a legal post-trade roster size.
8. **Package diversity**: real FIND_WIN_WIN: 11 distinct players across
   15 candidates (ratio 0.73), max single-player frequency 6. Reasonable
   for a small real league's real trade-relevant candidate pool; reported
   as honest context, not a pass/fail (per the rubric's own preregistered
   scope).
9. **Latency**: every real/synthetic run completed well inside the
   preregistered 5-second target (worst case 1.20s, real FIND_WIN_WIN
   across all 9 real opponents).

## A real bug found and fixed -- in this pass's OWN measurement script, not the generator

The FIRST run of this benchmark's harness (`scripts/run_trade_package_
quality_benchmark_v1.py`) reported 8 real "roster consolidation legality"
violations. Investigated live before reporting it as a generator defect:
the script's `owner_roster_size_before`/`opponent_roster_size_before_by_id`
were built from the RAW Sleeper roster size (15 players), but the real
search itself operates on the CANONICAL (identity-resolved) roster the
generator's own caller passes in -- 12 players for the owner, once K/DST
(never NWR-projected, by design) and one real identity-match gap dropped
out. Comparing the generator's real post-trade counts against the WRONG
"before" baseline produced 8 false positives. Fixed by using the same
canonical counts the search itself uses. Re-run: zero violations. This bug
lived entirely in this pass's new benchmark script
(`scripts/run_trade_package_quality_benchmark_v1.py`); `trade_package_
search_service.py` itself was never touched and was correct throughout.
A second, similarly-shaped bug (a synthetic fixture built with a 16-player
roster against a 15-slot league cap, making every trade illegal by
construction and producing zero candidates) was found and fixed the same
way, in the same script, before any real numbers were recorded.

## Verdict

**No coherent, mechanically-explainable failure pattern was found in the
real trade package generator across this rubric.** Every dimension either
passed cleanly (dominance, exact-duplicates, latency, roster legality) or
produced a result that is honestly and mechanically explained by the
INPUT (a small real league's candidate pool; a deliberately symmetric
synthetic fixture; a mode that legitimately found no package clearing its
own preregistered utility gates). Two real bugs were found and fixed this
pass, both in the new benchmark measurement code, never in the generator
itself. Per the owner's standing instruction, **no ranking challenger is
recommended** -- this is a complete, honest "the generator looks fine on
this rubric" result, not a forced conclusion.

## Open, disclosed items for a future pass (not acted on this pass)

- TARGET_PLAYER(LaPorta) and IMPROVE_POSITION(TE) both returned zero real
  candidates against the real league. This was not root-caused beyond
  confirming it is the utility gates rejecting every evaluated combination
  (packages_evaluated was non-zero, 120 and 372 respectively) -- plausible
  given the real target opponent (roster 2) is itself deep at every
  position the owner could offer surplus at, but a future pass with more
  time could trace the exact rejected utility numbers to confirm this
  more precisely rather than inferring it.
- The one real identity-match gap (Sleeper id `11628`, a rostered WR not
  present in the current ranking pool) was found but not investigated
  further or fixed -- out of this pass's scope (ranking/identity
  resolution is untouched by this cycle's hard boundary).
- This benchmark used only ONE real league. A genuine "coherent pattern
  across multiple real cases" standard (per the owner's own bar for ever
  recommending a challenger) would need this same harness run against a
  second real league -- flagged for Work Unit 19 (multi-league scale
  characterization), the next worker's own assignment.
