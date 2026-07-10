# Uncertainty and Stability Review

## Independent information

The evaluation has **11 independent target seasons**, 2015–2025. Player rows are not treated as independent seasons. The complete grid contains 44 season-position groups.

## Frozen method

Paired ridge-minus-PYF season deltas were constructed by equally averaging the four position deltas within each season. A deterministic season-cluster bootstrap sampled the 11 seasons with replacement for 10,000 draws using NumPy seed `20260710`. The two-sided percentile interval uses the 2.5th and 97.5th percentiles.

## Result

- Point estimate, position-balanced: `+0.007801`.
- Point estimate, season-balanced: `+0.007801`.
- Position-balanced 95% season-cluster interval: `[+0.003512, +0.012502]`.
- Season-balanced 95% season-cluster interval: `[+0.003512, +0.012502]`.
- Minimum leave-one-season-out position-balanced delta: `+0.006373`.
- Minimum leave-one-season-out season-balanced delta: `+0.006373`.
- Positive season deltas: `9/11`.
- Mechanical uncertainty gate: `PASS`.

Position-balanced and season-balanced values coincide because every one of the 11 seasons has all four positions with equal weights. Leave-one-season-out results are aggregation sensitivity checks over frozen out-of-fold predictions, not model refits.

Eleven seasons are materially more informative than two, but still a limited number of independent units. The interval is a stability diagnostic; it does not establish formal certainty, causality, or production superiority.
