# Candidate Evidence Consolidation

Inputs consolidated:

- Candidate Search V1 validation leaderboard and metric reports.
- Candidate Review V1 metric, stability, risk, and casebook reports.
- V3 historical tuning substrate with `5,518` review-only rows.
- Source Contract V1 allowed-feature contract.

What the candidate improves beyond raw MAE:

- Holdout Spearman is effectively stable at `0.001126`.
- Aggregate holdout startable precision is flat at `0.0`.
- All holdout positions and both holdout seasons improve MAE.

What prevents advancement today:

- Bucket and cutline effects are mixed.
- The regression casebook contains elite-QB prior-scoring rows that need football-context judgment.
- This remains historical review evidence only and is not approved for production use.
