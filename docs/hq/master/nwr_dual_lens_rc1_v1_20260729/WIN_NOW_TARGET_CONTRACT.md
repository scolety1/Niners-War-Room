# Win Now target contract

Decision anchor is the start of target season `t`. Inputs are completed season
`t-1` facts only. The primary target is NWR-scored target-season points minus
the position replacement score (QB12, RB30, WR40, TE12), with replacement
forecast only from the last three completed seasons. W2 separately predicts
conditional PPG and target games/season-length availability, calibrates only on
earlier out-of-fold origins, and multiplies them before subtracting
replacement. Evaluation uses 2017–2025 rolling origins, exact IDs, Spearman,
rank MAE, nDCG, top-12/24/60 precision/recall, severe errors, availability
Brier/MAE/log loss/ECE, position, season, low-games, and cohort results.

No random split, current ADP, target-season context, Outcome probability,
name join, or unsupported rookie fallback is allowed.
