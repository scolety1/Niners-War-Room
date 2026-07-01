# Overfit And Leakage Report

Leakage checks: PASS.

- Feature season N and target season N+1 lag is preserved.
- Target outcomes are not used as features.
- Holdout was evaluated after validation selection.
- Null-fenced fields were excluded from primary candidates.
- Sensitivity variants exclude rows with null-fenced inputs rather than filling missing values with zero.
- Blocked feature families are absent from formulas.

Overfit gap details are tracked in `overfit_gap_matrix.csv`, `position_level_metric_report.csv`, and `season_level_metric_report.csv`.
