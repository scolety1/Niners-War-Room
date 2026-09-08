# Rookie Prediction Bias — Subgroup Follow-Up V1 (2026-09-08)

**Context:** NWR class-time autonomous hardening directive, Section 14. Extends the prior
session's `NWR_ROOKIE_SPECIFIC_BIAS_STUDY_V1_20260907.md` (real finding: true rookies are
under-predicted ~16.7 pts/season on average, consistent by position and by round) with the
deeper subgroup breakdowns the directive names: draft round (already done), draft capital
(overall pick quartile), market tier (proxy: overall pick), projected workload (proxy: the
model's own predicted-points quartile, i.e., its own cohort-median workload expectation),
early vs late pick (both within-round and overall). Same real data:
`WALK_FORWARD_PREDICTIONS.csv`, 796 real rookie-seasons, 2016-2025, leakage-safe walk-forward.

## Real breakdowns

**By season** (stability check, 2016-2025): bias is negative every single real year, ranging
-11.50 to -24.11 -- persistent across a full decade, not a recent artifact, with no clear
monotonic trend (2023 and 2025 show the largest bias, but not as part of a steady worsening
pattern).

**By overall-pick quartile** (real market-tier proxy): -17.43 (earliest) / -16.35 / -20.47 /
-12.55 (latest) -- mild, non-monotonic variation, no clean "early picks worse" or "late picks
worse" story.

**By predicted-points quartile** (real projected-workload proxy -- the model's own cohort
expectation): -15.04 (lowest) / -23.95 / -16.76 / -11.08 (highest) -- again mild and
non-monotonic; the model's own highest-workload-expectation rookies are actually the LEAST
under-predicted bucket, the opposite of what a "the model doesn't trust high-workload rookies
enough" story would predict.

**By within-round half** (early vs late pick inside the same round): a real, interesting but
inconsistent pattern -- rounds 1-3 show much larger bias in the early-half of the round
(round 1: -24.80 vs -11.63; round 2: -27.49 vs -5.13; round 3: -21.71 vs -2.18) but this
reverses or flattens in rounds 4-7. Not a stable, monotonic subgroup.

**Position x pick-quartile cross-tab**: the largest local cells are QB in pick-quartile 3
(-31.88, n=29) and TE in the earliest pick-quartile (-31.69, n=30) -- but TE in the LATEST
pick-quartile is nearly zero (-4.45, n=29), the opposite direction, and none of these cells
carry a large enough sample to be trusted as a real, stable pattern rather than noise.

## The decisive check: bucket-to-bucket spread vs. real noise

```
Overall mean bias: -16.70, overall bias STD: 53.04 (i.e., real per-rookie variance is huge)

Dimension            Bucket range          Spread   vs overall STD (53.04)
position              -17.70 to -12.66      5.04     9.5%
round                  -22.54 to -12.00     10.54     19.9%
pick_quartile          -20.47 to -12.55      7.91     14.9%
predicted_quartile     -23.95 to -11.08     12.87     24.3%
```

**Every single-dimension bucket-to-bucket spread is small relative to the real per-rookie
noise (STD 53.04)** -- the largest (predicted-points quartile) is still under a quarter of one
standard deviation. This is the real, quantitative answer to "is underprediction concentrated
in a coherent subgroup": **no.** The bias is real, large, and pervasive across essentially
every rookie regardless of position, round, market tier, or projected workload -- not a
targetable pocket.

## Disposition: no calibration challenger built (per the directive's own explicit rule)

"Test a calibration challenger ONLY if a coherent subgroup pattern exists. No global rookie
bump." No coherent subgroup pattern was found -- the handful of larger local cross-tab cells
(TE early picks, QB pick-quartile-3) are small-sample, non-monotonic, and not part of any
stable, interpretable story (TE's OWN late-pick cell swings the opposite direction). Building
a challenger targeting any of these would functionally be a disguised global rookie bump,
which the directive explicitly forbids. **No correction built, no code change** -- consistent
with, and now further evidenced beyond, the prior session's own "no correction proposed"
disposition.

## Status

Section 14: **DONE.** Deeper subgroup analysis confirms the prior finding's own honest
conclusion: real, pervasive, decade-stable rookie under-prediction with no coherent subgroup
to calibrate against.
