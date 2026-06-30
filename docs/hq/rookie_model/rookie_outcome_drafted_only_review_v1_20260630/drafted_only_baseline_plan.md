# Drafted-Only Baseline Plan

This is a future plan only. No model was trained or tuned in this lane.

Allowed future post-draft factual features for a drafted-only baseline:
- position
- draft_year / rookie_class_year
- draft_round
- overall_pick
- drafted_team as context only unless a later policy approves modeling use

Blocked leakage fields:
- future NFL production
- Outcome V2 labels as input features
- market/ADP/DynastyProcess
- projections, grades, vendor text, Gmail/news, injuries as projection inputs
- CFBD production unless a later gate explicitly approves it

Needed labels are rookie-year, 2Y, first-3Y, and first-5Y threshold hits by
position. A future baseline should use class-year holdout splits, report Brier
score, log loss, calibration buckets, and sample sizes by position/target. It
must define minimum sample sizes before any tuning. These drafted-only results
do not apply to UDFAs because their entry path and missingness are different.
