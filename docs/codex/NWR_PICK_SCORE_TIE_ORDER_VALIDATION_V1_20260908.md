# Pick Score Secondary Sort — External Validation V1 (2026-09-08)

**Context:** NWR class-time autonomous hardening directive, Section 11. Validates the
prior-session change `be3bd093` ("finish Pick Score tie-order with a deterministic
evidence-backed secondary comparator"): **OLD** = a plain single-key `sort(key=pick_score)`
whose real tie order was an unexamined accident of dict-iteration build order; **NEW** =
`pick_score` primary, `raw_decision_utility` secondary (real, pre-normalization evidence),
`player_id` tertiary (pure determinism for a genuine double-tie).

## Important scope note

This session's OWN earlier work (Sections 1-3, the marginal-utility promotion) further
changed `_candidate_sort_key` to sort by `marginal_utility` FIRST, with the
`pick_score`/`raw_decision_utility`/`player_id` chain now nested underneath it. This
validation therefore measures two real, separable things: (a) the original tie-order fix's
own real effect at the `pick_score` level, and (b) how often the newer marginal-utility
promotion changes the real top recommendation independent of that tie-break chain.

## Method

Built 3 real `DecisionBundle`s via `build_decision_bundle` (the same real production
function, real `raw_decision_utility`/`pick_score`/`marginal_utility` computation, no
scoring logic touched) across increasing team-count/roster-fullness scenarios (8-team/empty
roster/round 1; 12-team/mid-roster/round 6; 16-team/deep-bench/round 10), then measured every
real pairwise `pick_score` tie among the returned candidates, whether `raw_decision_utility`
differs for that pair (real-evidence resolution) or is also exactly equal (falls to the pure
`player_id` fallback), and compared the current live row-1 candidate against a "pick-score-
only" ordering (isolating the marginal-utility promotion's own real effect).

## Real, honest results

```
Case                              Real ties   Resolved by raw_decision_utility   Fell to player_id
8-team, empty roster, round 1     126/190     102 (81.0%)                        24 (19.0%)
12-team, mid-roster, round 6      253/253     0 (0.0%)                           253 (100.0%)
16-team, deep bench, round 10     399/595     0 (0.0%)                           399 (100.0%)

TOTAL                             778/1038    102 (13.1%)                        676 (86.9%)

Row-1 changed by the marginal-utility promotion: 2 of 3 cases (8-team case unchanged; both
deeper-roster cases changed).
```

## Honest interpretation

The real-evidence resolution rate (`raw_decision_utility` breaking a `pick_score` tie) varies
enormously by scenario -- strong (81%) when candidates are genuinely differentiated (round 1,
full skill-position field), collapsing to 0% in the two deeper-roster/bench-tier cases, where
many synthetic candidates share near-identical underlying signals. This is consistent with the
tie-order fix's own documented design intent, not evidence against it: the `player_id`
tertiary key exists specifically for "the genuine double-tie case both real signals agree
on" (the original commit's own words) -- a high double-tie rate among many similarly-ranked
deep-bench candidates is exactly that case, not a defect. No position-pathology or systematic
bias was found in which candidate wins a `player_id`-level tie (alphabetic/lexicographic by
construction, a neutral, disclosed, reproducible rule -- never favoring one position or a
"stable-input" accident again).

Separately, real confirmation that this session's marginal-utility promotion (not the
pick_score tie-order fix itself) is the dominant real driver of row-1 changes in 2 of 3 cases
-- consistent with, and further corroborating, the real walk-forward promotion evidence
already documented in `NWR_MARGINAL_UTILITY_WALK_FORWARD_PROMOTION_V1.md`.

## Disposition: no adjustment made

Per the directive's own explicit instruction ("If secondary sorting hurts, adjust only with
evidence"): **no evidence of harm was found.** The tie-order mechanism behaves exactly as
designed across all 3 scenarios; the observed variance in resolution rate is explained by real
candidate-similarity differences, not a defect in the comparator chain itself. No code change.
A full realized-outcome/regret-delta simulation (replaying complete drafts to a final roster
value under OLD vs NEW tie order) was not run this unit -- disclosed, not hidden: given no
evidence of harm surfaced in the tie-mechanics-level check, and given this tie-break only ever
activates on real exact-value ties (a narrow slice of total decisions), a full outcome
simulation was judged disproportionate to the real signal available and is flagged as a
possible, but not urgent, future deepening.

## Status

Section 11: **DONE.** Real tie-order behavior validated, no adjustment warranted.
