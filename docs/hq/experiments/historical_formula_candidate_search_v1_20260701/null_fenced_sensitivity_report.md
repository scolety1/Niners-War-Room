# Null-Fenced Sensitivity Report

The primary candidate pass excludes null-fenced fields. Sensitivity variants use optional air/YAC and snap-context fields only on rows where the required inputs are non-null. Missing values are not filled with zero.

See `null_fenced_sensitivity_report.csv` for row counts and metrics.
