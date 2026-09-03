# SHADOW numeric authorities V1 — Team Score / Championship Equity / Pick Score

Implementation doc for `src/services/shadow_numeric_authorities_service.py`
and `src/services/redraft_draft_room_v1_service.py`'s `simulate_pick_now`/
`evaluate_pick_candidates` companions. Everything here is **RESEARCH_ONLY /
SHADOW** — nothing is wired into production ranking, Suggestions, or any
owner-facing decision surface. No weight was hand-picked and called
validated.

## TEAM SCORE — RESEARCH

**Semantics**: percentile strength of a roster's optimal starting lineup
value relative to a population of real simulated comparable rosters under
the exact same league format.

**Implementation**: `optimal_starting_lineup_value()` greedily fills
required position slots (by `replacement_adjusted_value`, already
computed and governed by `generate_rankings()` — not a new formula), then
FLEX/superflex with the best remaining eligible players. Documented as a
heuristic, not proven globally optimal.
`simulate_comparable_leagues()` re-runs the real, already-tested
`run_complete_mock()` CPU-vs-CPU simulator `trials` times with different
seeds and owner-slot draws, producing a population of every team's roster
across every simulated league. `team_score()` reports where the target
roster's lineup value falls in that population.

**Example** (10-team, 1QB, `_ranking()` fixture, 3 trials): the single
best possible roster (top starter at every position) landed at the 100th
percentile of a 30-roster simulated population — at or above every
comparable roster, as expected. See
`tests/test_shadow_numeric_authorities_service.py::test_team_score_from_a_real_simulated_population_is_a_real_percentile`.

**~50 = league average**: falls out of the population by construction
(the population *is* a set of real comparable rosters for this format),
not a hand-picked normalization constant.

**Latency**: `simulate_comparable_leagues(trials=10)` — 0.49s (10 teams),
0.59s (12 teams), 0.80s (16 teams). Dominated by re-running
`run_complete_mock`; can be computed once per pick and reused across many
candidate evaluations.

**Caveats**: Player Score proxy (`replacement_adjusted_value`) inherits
whatever calibration state the live ranking formula is in, including the
QB-replacement-depth defect documented in
`docs/codex/QB_MARGINAL_VALUE_AND_ROOKIE_CALIBRATION_AUDIT_20260903.md` —
Team Score does not correct that defect, it inherits it as an input.
K/DST and unmodeled-skill-player assets always contribute 0 (no fake NWR
score, per section 17) — a roster's Team Score does not reward or penalize
*which* K/DST it holds, only whether the slot is filled.

## CHAMPIONSHIP EQUITY — SIMULATED RESEARCH

**Semantics**: fraction of Monte Carlo-simulated seasons a roster wins,
inserted into one real simulated league (the other `team_count - 1`
rosters held fixed from one `simulate_comparable_leagues` trial).

**Implementation**: `championship_equity()` converts each team's season
total lineup value to a per-week mean, then `_simulate_one_season_winner()`
runs disclosed, explicit `ChampionshipEquityAssumptions` — 14-week regular
season (standings by simulated point total, not real matchup win/loss),
top-4 single-elimination playoffs, 18% weekly Gaussian noise — repeated
`seasons` times. Returns `win_probability` plus a binomial Monte Carlo
`standard_error`.

**Example**: a QB-0-only roster (rank 1 overall in the fixture) vs. a
TE-29-only roster (rank 240) in an otherwise-identical 4-team league, 200
simulated seasons each, seed 3: the QB-0 roster's win probability was
strictly higher (see
`test_championship_equity_strong_roster_beats_weak_roster_in_expectation`)
— a sanity check, not a calibration claim.

**Monte Carlo uncertainty**: standard error reported explicitly on every
result; not hidden. At `seasons=150-300` (used in the latency benchmark
and tests) standard error is typically in the 0.02-0.04 range for
mid-probability estimates — wide enough that small equity-gain
differences between similar candidates should not be over-read.

**Caveats**: the regular-season/playoff structure is an explicitly
disclosed simplification (`ChampionshipEquityAssumptions.note`), not this
league's actual configured schedule (`LeagueProfile` does not carry one).
Do not present `win_probability` as a calibrated real-world probability —
it is a probability *within this simulation's own assumptions* only.

## RESEARCH_ONLY_PICK_SCORE

**Semantics**: 0-100, but explicitly relative to only the candidates
evaluated in one call — 100 = strongest of this set, 0 = weakest, 50 =
mid-spread. Never an absolute/calibrated score. Also reports the literal
Team Score After / Championship Equity After / Equity Gain / Cost of
Waiting values alongside the 0-100 number, per section 11's explicit "do
not hide uncertainty, show the raw numbers too."

**Example**: `pick_score()` over 3 synthetic candidates (Team Score
90/60/30, Champ Equity 0.30/0.15/0.05) returns relative scores 100 / ~57 /
0 — proportional to each candidate's position within the evaluated
equity spread, not the raw team-score numbers directly.

**Cost of waiting**: currently a documented lower-bound placeholder — the
Team Score gap between a candidate and the best *other* evaluated
candidate. Not yet weighted by make-it-back/ADP-survival probability (the
full version proposed in `docs/codex/NUMERIC_AUTHORITIES_RESEARCH_V1.md`);
treat as a floor, not the final number.

**Caveats**: candidate-relative only — a Pick Score of 100 in a weak
candidate set is not equivalent to a Pick Score of 100 in a strong one.
Never compare Pick Scores across two different picks/candidate sets as if
they were on the same absolute scale.

## Look-ahead (section 12)

`simulate_pick_now()` forces one candidate as the owner's next selection
then completes the rest of the draft (opponents and the owner's own later
picks) via the same market/auto-score logic `run_complete_mock()` uses —
one plausible continuation per candidate, not an exhaustive search.
`evaluate_pick_candidates()` runs this per candidate, scores each
resulting roster against one shared comparable-league population (computed
once, reused across all candidates), and ranks with `pick_score()`.

**Measured end-to-end latency** (10 comparable-league trials, 150 seasons/
candidate):

| Teams | 8 candidates | 10 candidates |
|---|---|---|
| 10 | 0.96s | 1.06s |
| 12 | 1.18s | 1.43s |
| 16 | 1.76s | 1.91s |

All under the <2s preferred target through 16 teams / 10 candidates.
Stability across seeds was not separately re-measured beyond the fixed
seeds used in tests; treat as a known gap before any production use.

## What none of this claims

Not a calibrated ranking, not decision authority, not validated against
any real historical outcome. Every result in this module should carry its
`label` field (`TEAM SCORE — RESEARCH`, `CHAMPIONSHIP EQUITY — SIMULATED
RESEARCH`, `RESEARCH_ONLY_PICK_SCORE`) wherever it is ever surfaced, per
this lane's own governance.
