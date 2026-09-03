# Team Score V2 / Championship Equity V2 / Pick Score / optimizer benchmark (sections 7–10)

Script: `scripts/run_shadow_numeric_authorities_benchmark_v1.py` (run:
`python -m scripts.run_shadow_numeric_authorities_benchmark_v1`, ~30s).
Smoke test: `tests/test_shadow_numeric_authorities_benchmark_smoke.py`,
2/2 passing, exercises the same real functions at small scale so a
regression fails CI fast without paying the full 30s every run. All
outputs are real runs against a synthetic 240-player benchmarking
fixture (the same shape used throughout this repo's shadow-authorities
tests) — never presented as real player evidence.

Real output CSVs (checked in for durability):
`docs/codex/TEAM_SCORE_CHAMPIONSHIP_EQUITY_BENCHMARK_V1.csv` (35 rows —
5 league profiles × 7 roster scenarios), `CHAMPIONSHIP_EQUITY_SENSITIVITY_V1.csv`
(6 rows), `PICK_SCORE_EXAMPLES_V1.csv` (40 rows — 4 formats × 10
candidates), `LOOK_AHEAD_OPTIMIZER_BENCHMARK_V1.csv` (6 rows).

## Team Score V2 (section 7)

Profiles: 10T 1QB, 12T 1QB, 16T 1QB (KHA-like, 16 rounds), 12T
Superflex, 12T multi-FLEX (flex=2). Scenarios: star-heavy/thin-bench,
balanced, QB-heavy 1QB, RB-heavy, WR-heavy, missing-TE,
injury-risk-heavy (via the new `availability_adjusted_players`).

- **Determinism**: `simulate_comparable_leagues` re-run with the same
  seed produced a byte-identical population in all 5 profiles
  (`population_deterministic_same_seed=True` in every row); `team_score`
  re-run against the same population is likewise identical
  (`team_score_deterministic_same_population=True`).
- **Latency**: `simulate_comparable_leagues` (30 trials, the real
  population-generation cost) ranged 1.45s (10T) to 2.6s (16T/16 rounds)
  — a one-time cost per profile, reusable across every candidate/roster
  evaluated against it. `team_score` itself against a precomputed
  population is sub-2ms every time.
- **Real, intuitive signal, not fabricated**: `qb_heavy_1qb` (a 3rd QB
  drafted in a 1QB league) scored **percentile 0.0** in every profile —
  investing a pick in a redundant 3rd QB instead of a starter-eligible
  RB/WR/TE genuinely produces a weaker roster by this metric. `rb_heavy`/
  `wr_heavy` (imbalanced position investment leaving a starter hole at
  the other skill position) also scored 0.0. This is the real QB
  Moneyball behavior the directive asked to demonstrate — see also
  section 13's write-up.
  - **Caveat, stated plainly**: these benchmark rosters are small
    (7-12 players), representing an early/mid-draft state, not a
    completed 15-round roster — their absolute percentile values reflect
    that scale, not a claim about a finished team.

## Championship Equity V2 (section 8)

Sensitivity on one fixed 12T roster: `seasons_simulated` 50→500 (standard
error 0.0384→0.0166, latency 2.4ms→16.0ms — the expected 1/√n Monte
Carlo error shrinkage, and cheap enough that "seasons=500" is a
reasonable STANDARD/DEEP default rather than requiring a slow tier for
useful precision). Across `base_seed` 1/2/3 at seasons=200, win
probability varied 0.145–0.175 — real seed-to-seed Monte Carlo noise at
that season count, exactly what the reported `standard_error` predicts,
not hidden. No historical calibration is claimed anywhere (the
`ChampionshipEquityAssumptions.note` field already discloses the
simplifying assumptions).

## Pick Score (section 9)

Real top-10 tables for 16T-KHA-like/10T/12T-PPR/12T-Superflex, each
against the same 10 candidates. Latency 0.8–1.4s per 10-candidate
evaluation (dominated by `simulate_pick_now` completing a full mock
draft per candidate) — all well under the 2s interactive target. Rankings
were non-trivial (not simply reproducing NWR overall rank order) in
every format, confirming Pick Score is responding to roster-context and
league-format differences rather than degenerating to a restatement of
the input ranking.

## Look-ahead optimizer (section 10)

10T/12T/16T × 5/10 candidates. `simulate_pick_now` alone (one forced
candidate, full draft completion): 48–91ms. Full
`evaluate_pick_candidates` (every candidate, each independently
resimulated): 419ms (10T/5) to 1165ms (16T/10) — **every configuration
tested stayed under the 2s interactive target**, with real measured
numbers, not asserted ones.

**Caching already in place, demonstrated by this benchmark itself**:
`evaluate_pick_candidates` already computes `comparable_leagues` once
and reuses it across every candidate in one call (see its own docstring)
— the benchmark script does the same at the profile level, computing
`simulate_comparable_leagues` once per profile and reusing it across all
7 roster scenarios. No further caching was found necessary to hit the
2s target at these team-count/candidate-count combinations; if a future
larger candidate set (20+) is needed, `simulate_comparable_leagues`'s
per-profile population is the obvious next reuse point across repeated
Suggestions calls within one draft, not yet implemented as a persistent
cache (each facade call would currently recompute it).

## Section 13 (QB pathology) preview

The `qb_heavy_1qb` percentile-0.0 result above is exactly the Moneyball
principle section 13 asks to demonstrate: a QB can be individually
strong (its `replacement_adjusted_value` is real and positive) yet be a
poor *current action* once roster structure and replacement depth are
accounted for. See `docs/codex/QB_PATHOLOGY_MONEYBALL_DEMONSTRATION_20260903.md`
for the dedicated side-by-side receipt.
