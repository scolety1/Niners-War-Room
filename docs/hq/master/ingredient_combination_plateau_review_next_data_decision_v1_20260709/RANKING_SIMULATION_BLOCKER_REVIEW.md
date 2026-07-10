# Ranking Simulation Blocker Review

Decision: `REVIEW_ONLY_RANKING_SIMULATION_NOT_JUSTIFIED`

Ranking simulation remains blocked because the best full-history lift is only `0.758`, the best broad-window lift is `0.763`, and the `0.790` results are partial-window modern results. These are useful review-only findings, but they do not clear the bar for a ranking simulation or production-adjacent board projection.

Ranking simulation can be reconsidered only after a new ingredient sidecar provides a material full-history or broad-window lift with clean same-row baselines, leakage/as-of proof, source/use-gate status, and stable slice behavior.
