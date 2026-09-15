# Trade Package Quality Benchmark V1 -- Preregistered Rubric (Work Unit 16)

Written BEFORE the benchmark harness was run against real data (this
project's own discipline: criteria fixed before results are seen). Scope:
this is a MEASUREMENT pass over the existing, unmodified
`src/services/trade_package_search_service.py` (the real package
generator) and its own preregistered quality gates
(`docs/codex/post_ui_v1/TRADE_PACKAGE_SEARCH_QUALITY_GATES_P1_3.md`).
Nothing in `trade_package_search_service.py`, `redraft_trade_analysis_
service.py`, or any ranking/scoring module is modified by this pass. The
new code this pass ships
(`src/services/trade_package_quality_benchmark_v1_service.py`) only READS
`TradePackageSearchResult`/`TradePackageCandidate`/`TradeEvaluation`
objects the generator already produces and computes diagnostic reports
over them.

Every rubric dimension below reuses fields the generator/evaluator
already compute (`net_marginal_utility`, `starting_lineup_value_delta`,
`starter_holes_before/after`, `package_shape`, `you_send`/`you_receive`,
`packages_evaluated`, `truncated`) -- no new scoring formula is
introduced anywhere in this pass.

## 1. Top-N dominated by simpler trade

The generator already applies a Pareto dominance filter (gate 4 of the
existing quality-gates doc, `_drop_dominated`) BEFORE returning candidates
-- a returned package should never be weakly dominated (equal-or-worse on
both owner and opponent net utility) by an equal-or-smaller package for
the SAME opponent. `check_dominance_violations` independently
RE-VERIFIES this invariant on the generator's own OUTPUT (not by
re-running the private filter -- an external, black-box check), scoped
per opponent. A violation here means gate 4 has a real hole; zero
violations on real output is the expected, passing result, not assumed.

## 2. Both teams gain real starter value

`net_marginal_utility > 0` (owner, FIND_WIN_WIN/IMPROVE_POSITION) or `>=
0` (opponent) is already gated at generation time -- but a positive NET
roster-utility number can be produced entirely from BENCH depth with zero
real starting-lineup impact on one or both sides (see dimension 4 below).
This dimension checks a stronger, more human-plausible bar:
`starting_lineup_value_delta` (a real field already on `TradeEvaluation`)
for EACH side independently, with a fixed, disclosed materiality
threshold `STARTER_VALUE_EPSILON = 0.5` (points) -- the SAME threshold
the generator's own `_explain` function already uses for its bench-delta
note, reused here rather than inventing a second number. A candidate is
labeled `BOTH_SIDES_STARTER_IMPACT`, `ONE_SIDED_STARTER_IMPACT` (only one
side's real starting lineup value moves by >= epsilon), or
`NEITHER_SIDE_STARTER_IMPACT`.

## 3. Position-need fit

For IMPROVE_POSITION mode this is already structurally guaranteed by
construction (every receive-combo includes a real player at the requested
position -- see the generator's own docstring). For FIND_WIN_WIN/
TARGET_PLAYER, this dimension checks whether the package actually
resolves a real, PRE-EXISTING starter hole on the owner's side --
`set(starter_holes_before) - set(starter_holes_after)` (a real field the
generator's own `_explain` already computes and surfaces in
`why_it_helps_you`) -- non-empty. A package that improves owner net
utility purely through bench-value/redundancy without ever touching a
real starter hole is labeled `NO_HOLE_ADDRESSED`, not a failure by itself
(a genuinely good depth trade can still be a fine trade), but tracked
so a systemic "never actually fixes real holes" pattern would be visible
if it existed.

## 4. Bench-for-bench clutter

A candidate where BOTH sides' `starting_lineup_value_delta` are within
`STARTER_VALUE_EPSILON` of zero -- i.e., every player moving in the trade
stays on the bench on both sides, the whole package is roster-depth
reshuffling with no real starting-lineup consequence for anyone. Flagged
`BENCH_FOR_BENCH_CLUTTER`. A single instance is not automatically bad
(bench-quality consolidation can be a legitimate, if minor, real
improvement), but a HIGH RATE of these among the top-ranked results would
be a real, human-plausibility problem worth a challenger.

## 5. Duplicate / near-duplicate packages

Exact duplicates are already structurally impossible (gate 5, a `seen_
keys` set keyed by `(opponent, frozenset(gives), frozenset(receives))`).
This dimension measures NEAR-duplicates: for every pair of RETURNED
candidates against the SAME opponent, the Jaccard similarity of their
combined `{you_send} | {you_receive}` player-id sets --
`|A ∩ B| / |A ∪ B|`. A fixed, disclosed threshold
`NEAR_DUPLICATE_JACCARD_THRESHOLD = 0.5` flags a pair as
`NEAR_DUPLICATE` (more than half the players in play are shared between
the two packages) when the pair is not identical. This is a genuinely
different measurement than gate 5 -- it targets "the same core trade
restated with a swapped throw-in," which gate 5's exact-key dedup cannot
catch by design.

## 6. Package-size penalty (does complexity scale sensibly?)

The generator's own dominance filter (gate 4) already guarantees that a
SURVIVING larger package beats every available smaller alternative on at
least one axis for the same opponent -- so, by construction, no returned
candidate should ever be "complexity for its own sake." This dimension
reports the REAL, OBSERVED distribution of owner/opponent net utility by
`package_shape` (mean/median grouped by total player count: 2, 3, 4) as a
DIAGNOSTIC, not a pass/fail gate -- a legitimate real league can go either
way (sometimes the best available trade really is a 2-for-2). What WOULD
be a real finding: a package_shape group whose mean owner utility is
LOWER than a strictly-smaller shape's mean AND still appears in the
top-N returned results in materially equal proportion -- that would
indicate dominance filtering is not actually doing its job at scale
(cross-checked against dimension 1's direct violation count, which is the
authoritative signal; this dimension is exploratory context only).

## 7. Roster consolidation cost

Independently re-verifies (never trusting the generator's own internal
gate 1 blindly) that EVERY returned candidate leaves both the owner's and
the opponent's post-trade roster within `0 <= size <=
total_roster_slots(profile)` -- the same check the generator itself
performs, re-run externally against the candidate's own `you_send`/
`you_receive` and the real pre-trade roster sizes supplied to the
benchmark harness. A second, real "sensible state" check: no side is left
with a negative or clearly absurd post-trade position count (e.g., a
required starting position going to zero rostered players of that
position with no flex/superflex substitute) -- computed from real
position labels the harness already has for both rosters, not fabricated.

## 8. Package diversity

For the full RETURNED candidate list (all opponents, one mode/run):
`distinct_players_used = |union of every candidate's (you_send |
you_receive)|`, and `max_single_player_frequency = max over players of
(how many returned candidates that player appears in)`. Reported as a
diagnostic ratio (`distinct_players_used / total_candidates`) and the max
frequency -- a generator producing genuinely different options should show
a healthy spread; a generator silently recycling the same 2-3 "obvious"
players across every returned package would show a low ratio and a high
max frequency. No fixed pass/fail threshold is preregistered here (a
small real league can legitimately have a small real trade-relevant
player pool) -- reported as real, honest context alongside the other
dimensions, not a lone verdict.

## 9. Latency

Reuses the existing preregistered target from the generator's own gates
doc (gate 7): FIND_WIN_WIN across every real opponent must complete in
under 5 real wall-clock seconds for a realistic league. This benchmark
re-measures it directly (not merely re-running the generator's own unit
test) against BOTH a realistic synthetic 10-team league fixture and the
real Fantasy Gamers league, for all three modes, and reports the real
elapsed time for each real run.

## Methodology

- Real sample: the real "Fantasy Gamers" Sleeper league (id
  `1312983576827920384`, read-only), using the REAL, currently-installed
  NWR ranking (the real `projections/2026/current.csv` snapshot already
  approved and installed at the owner's real AppData profile
  `4c5f04762921420595e4d8c7cda76582`, loaded READ-ONLY -- never written to)
  and the real, current Sleeper roster state for all 10 teams. Three real
  runs: FIND_WIN_WIN (every opponent), TARGET_PLAYER (a real, named
  opponent starter the owner's own roster has a real, disclosed hole at),
  IMPROVE_POSITION (the owner's own real, disclosed thinnest position).
- A larger, clearly-labeled SYNTHETIC 10-team league fixture (deterministic,
  committed test-style construction, not real player data) is also run, to
  get a bigger candidate sample than one real league's real candidate count
  can offer for the diversity/near-duplicate/size-penalty dimensions, which
  benefit from more data points. Every result from this fixture is labeled
  `SYNTHETIC_FIXTURE`, never blended into the real-league numbers as if it
  were real.
- No ranking/recommendation logic is tuned based on what this benchmark
  finds. Per the owner's standing instruction: a ranking challenger is only
  recommended if a coherent, MECHANICALLY-EXPLAINABLE failure pattern
  appears across MULTIPLE real cases -- never from a single anecdote, and
  never opportunistically built the same night it is found.

See `docs/codex/prospective_outcomes_v1/trade_package_quality_benchmark_v1/`
for the real, run-once JSON output this rubric was applied to, and the
LEDGER's Worker 7 entry for the narrative verdict.
