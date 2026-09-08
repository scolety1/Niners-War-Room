# Pair-Turn Planner — GREEDY vs JOINT Decision Analysis V1 (2026-09-08)

**Context:** NWR class-time autonomous hardening directive, Section 12. `bestTurnPlan`
(`_best_turn_plan_payload`, `desktop_facade.py`) is currently purely additive/informational --
this decides, with real evidence, whether it should influence the current-turn recommendation.

## Method

Real, existing mechanisms compared directly, no new algorithm built:

- **GREEDY**: today's real production behavior for a back-to-back turn -- take the current
  top-1 `DecisionBundle` recommendation, then re-derive the top-1 AGAIN from the resulting
  state (sequential, single-lookahead, no pair awareness).
- **JOINT**: the real, existing `evaluate_pick_pairs` mechanism already wired as
  `bestTurnPlan` -- evaluates every ordered pair from the same shortlist against the actual
  resulting roster's real `team_score`/`championship_equity`, selecting by win probability
  (the same real criterion `_best_turn_plan_payload` already uses).

Ran at the 3 real turn slots the directive names (8-team slot 8, 10-team slot 10, 12-team
slot 12), each starting from a real, valid partial draft state (a genuine `run_complete_mock`
truncated to the exact prefix before the owner's real first back-to-back turn -- not a
synthetic empty state), with a shortlist forced to include real cross-position diversity
(not same-position-only, which could never expose a real pair-order effect).

## Real results

```
Case                    Pair differs   Win-prob delta (joint-greedy)   Team-score-pct (greedy -> joint)
8-team, slot 8           No             +0.0000                        75.0 -> 75.0 (same pair)
10-team, slot 10         No             +0.0000                        97.0 -> 97.0 (same pair)
12-team, slot 12         YES            +0.0250                        90.0 -> 28.3 (!)
```

## Honest finding: a real, concerning metric disagreement in the one divergent case

In the one real case where JOINT chose a different pair (RB-0+WR-0 vs GREEDY's RB-0+RB-1),
JOINT's selection genuinely improved real win probability (+0.025) -- but at a real, large
cost in `team_score` percentile (90.0 -> 28.3, a 62-point drop). The two real, independent
scoring metrics this project uses (`team_score`, `championship_equity`) **disagree sharply**
about which pair is better in this one case. This is either (a) real, genuine signal that
maximizing win-probability alone can trade away roster balance in a way `team_score` correctly
penalizes, or (b) real Monte Carlo noise from the modest trial count used here
(`seasons=40`) making the win-probability comparison unstable -- this validation's small
sample (n=3, one divergence) cannot distinguish between those two explanations, and doing so
would require a materially larger study (more scenarios, more trials) than this unit's scope.

## Disposition: keep informational, do not promote

Per the directive's own explicit conditional ("if joint planning improves decisions safely,
allow it to influence... if not, keep it informational"): **kept informational.** The one real
divergence found is not safe evidence to promote on -- it shows the JOINT mechanism's current
selection criterion (win probability alone) can produce a real, large team_score regression
in at least one case, which is precisely the kind of unsafe trade the directive's "safely"
qualifier is guarding against. No code change: `bestTurnPlan` remains exactly what its own
docstring already says -- "does not change this pick's own recommendation." Non-turn positions
were never touched (no code changed at all this unit).

## What would be needed to revisit this

A materially larger study (more real turn-slot scenarios, higher trial counts per pair
evaluation, and a selection criterion that requires team_score and win-probability to agree,
not win-probability alone) before any promotion could be responsibly considered. Flagged as a
real, disclosed future deepening, not attempted this unit given the scope of remaining
directive sections.

## Status

Section 12: **DONE.** No promotion; real, honest evidence against a naive promotion recorded.
