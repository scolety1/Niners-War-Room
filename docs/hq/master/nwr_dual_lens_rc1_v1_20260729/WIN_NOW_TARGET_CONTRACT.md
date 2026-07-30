# Win Now target contract

The decision anchor is the start of target season `t`; model inputs are facts
available by completed season `t-1`. The primary target is target-season NWR
points minus position replacement. W2 predicts conditional production and a
continuous `EXPECTED_GAMES_FRACTION`; their product yields expected production.

The separate binary output `P(GAMES_PLAYED >= 8)` is fit chronologically to an
exact binary target. It is never substituted for expected games fraction.
Continuous availability is evaluated with MAE, RMSE, residual, and calibration
slope/intercept. Only the binary output receives Brier, binary log loss, ECE,
event-count, slope, and intercept evaluation.

Candidate selection uses the unweighted mean of nDCG calculated independently
within each chronological target season. Pooled nDCG is diagnostic only. No
random split, current ADP, target-season/future context, Outcome V3 feature,
name join, or unsupported rookie fallback is allowed.
