# As-Of And Leakage Guardrail Report

## Checks

- Feature season N to target season N+1 lag: PASS for all 3,108 rows.
- Target outcomes separated from features: PASS.
- Current-only roster/status/injury/depth/schedule context excluded from canonical columns: PASS.
- Market/vendor/projection/ADP fields excluded: PASS.
- Routes, route proxies, TPRR, YPRR, and ambiguous `rz_att` absent: PASS.
- Red-zone side fields excluded from canonical substrate pending stronger historical admission: PASS.
- Missing values not forced to zero by this builder: PASS, with source-level YELLOW caveat documented in `missingness_semantics_report.md`.

## As-Of Rule

Each row uses completed season N facts as the feature side and completed season N+1 outcomes as the target side. No target-season availability, depth, schedule, ADP, rankings, projections, vendor context, hidden sort, or recommendation output is admitted as a feature.
