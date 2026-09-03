# Raw Decision Utility — exact construction, and the one arbitrary weight (section 8)

## The exact formula, as it exists in code today

```
team_score_utility_component = team_score_after - current_team_score.percentile
equity_utility_component     = EQUITY_TO_PERCENTILE_WEIGHT * (championship_equity_after - current_championship_equity.win_probability)
raw_decision_utility         = team_score_utility_component + equity_utility_component
```

`EQUITY_TO_PERCENTILE_WEIGHT = 100.0`, defined once in
`decision_bundle_service.py` and imported by
`historical_decision_state_service.py` so both the live-drafting and
historical-replay paths use the identical constant.

## The arbitrary weight, named explicitly

`EQUITY_TO_PERCENTILE_WEIGHT = 100.0` has **no empirical basis**. It
exists only to put a 0.0–1.0 Championship Equity probability delta
(typically a few hundredths, e.g. 0.02–0.08) onto a numeric scale roughly
commensurate with a 0–100 Team Score percentile delta (typically single
digits to low teens), so that neither term numerically dominates the sum
by construction alone. **It is not disguised by normalization** — it is
a bare multiplicative constant, disclosed here and in the code comment
directly above its definition, and it is not claimed to represent any
real trade-off an owner would actually make between "1 percentile point
of roster strength" and "1 percentage point of championship win
probability." Nothing about this weight has been fit to any data, real
or synthetic.

## Why it is not restructured away this wave

The directive suggests restructuring so the utility "comes primarily
from simulated future consequences rather than hand-selected score
weights." The two components already ARE simulated future consequences
(a real Monte Carlo Team Score delta, a real Monte Carlo Championship
Equity delta) — the arbitrary part is only the single scalar that
combines them into one number. Removing that combination entirely (i.e.
never producing a single Raw Decision Utility number) would break Pick
Score's own downstream `pick_score()` ranking, which needs *some* single
ordering to rank candidates against each other. The chosen middle
ground: **preserve the two components separately** on every
`CandidateBundle` (`team_score_utility_component`,
`equity_utility_component`) so a future calibration pass can fit a real
weight (or a non-linear combination) from real held-out data, replacing
`EQUITY_TO_PERCENTILE_WEIGHT` without needing to re-derive the
components from scratch. This is implemented now, not deferred:
`CandidateBundle` carries both fields today, in both
`decision_bundle_service.py` and `historical_decision_state_service.py`.

## What historical calibration would need to do

Once real historical decisions and real realized outcomes exist:
regress (or isotonic-fit) realized pick quality (from
`outcome_evaluation_framework_service.pick_level_metrics`) against
`team_score_utility_component` and `equity_utility_component`
separately, to see whether `100.0` is too high, too low, or whether the
two components should combine non-additively at all. Until then,
`EQUITY_TO_PERCENTILE_WEIGHT` stays exactly what it is: a disclosed
placeholder, not a calibrated finding.
