# QB pathology — Moneyball diagnostic receipt (section 13)

Script: `scripts/run_qb_pathology_moneyball_demonstration_v1.py` (run:
`python -m scripts.run_qb_pathology_moneyball_demonstration_v1`). Tests:
`tests/test_qb_pathology_moneyball_demonstration.py`, 3/3 passing. All
real computed numbers below, from a synthetic benchmarking fixture (the
same shape used throughout this repo's shadow-authorities tests, never
real player evidence).

## The principle

**No anti-QB rule anywhere in this code.** `QB-18`'s Player Score
(`replacement_adjusted_value`) is real and genuinely higher than the
alternative candidate's (`381.0` vs. `363.0`). The pathology is purely
structural: once a 1QB roster already has a starting QB, a second QB has
nowhere to start.

## Setup

Owner roster so far: `QB-0, RB-4, RB-5, WR-4, WR-5, TE-4` (fills QB/RB/
RB/WR/WR/TE exactly, FLEX open, bench open). Two real candidates
evaluated for the next pick: `QB-18` (best remaining QB) and `RB-6`
(best remaining RB) — real `roster_composition_report`/`team_score`
calls, not a hand-picked outcome.

## 1QB league

| Candidate | Player Score | Starting-lineup delta | Team Score after |
|---|---|---|---|
| QB-18 | **381.0** (higher) | **0.0** | 0.0 percentile |
| RB-6 | 363.0 (lower) | **363.0** (full value — fills FLEX) | 100.0 percentile |

QB-18 is individually the *better* player and contributes **zero**
incremental value to the current roster (pure bench — QB is already
filled and QB is not FLEX-eligible). RB-6, with a *lower* Player Score,
contributes its full value because it fills the open FLEX slot. This is
the exact Moneyball inversion the directive asked to demonstrate:
**worse Player Score, better pick.**

`team_score` against a real 30-trial simulated population (not just the
isolated delta) confirms the same ordering:
`test_team_score_confirms_the_same_ordering_against_a_real_simulated_population`.

## Superflex inversion

Identical setup, one roster-rule change (`superflex=1`):

| Candidate | Player Score | Starting-lineup delta | Team Score after |
|---|---|---|---|
| QB-18 | 381.0 | **381.0** (full value — fills SUPERFLEX) | 0.0 percentile |
| RB-6 | 363.0 | 363.0 (full value — fills FLEX) | 0.0 percentile |

Now QB-18 is a real starter (the SUPERFLEX slot accepts QB), its full
value counts, and it decisively **outranks** RB-6 (`381.0 > 363.0`) —
the same two candidates, the same Player Scores, the opposite
recommendation, purely because the roster rule changed. No player-
specific logic anywhere in the code produced this; it falls directly out
of `_select_starting_lineup`'s real superflex-eligibility handling
(`FLEX_ELIGIBLE | {"QB"}`).

(Team Score percentile is 0.0 in both Superflex rows because this is
still a small 7-player partial roster compared against a population of
full 15-round rosters — see the same caveat in
`docs/codex/SHADOW_NUMERIC_AUTHORITIES_BENCHMARK_20260903.md`. The
starting-lineup delta, not the absolute percentile, is the relevant
comparison here.)

## Methodology note (why not the full look-ahead pipeline)

An earlier draft of this demonstration routed through
`evaluate_pick_candidates`/`simulate_pick_now` (forcing each candidate,
then completing the rest of the draft). That diluted the effect: with
~14 remaining rounds of CPU-driven owner picks auto-filling roster gaps
regardless of this one forced choice, the two final rosters converged to
similar Team Score values (both landed at `pick_score=100.0`, tied) —
a real, honestly-reported finding about that pipeline's own limits (a
single pick's marginal impact shrinks the more remaining picks exist to
compensate for it), not evidence against the pathology. This version
isolates the actual question — "what does adding this ONE player do to
my current roster" — with the more direct
`roster_composition_report`/`team_score` tools, which is the right tool
for isolating one pick's own marginal effect.
