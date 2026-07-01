# As-Of And Leakage Guardrail Report V2

## Checks

- Feature season N to target season N+1 lag: PASS for all `5,518` rows.
- Target outcomes separated from features: PASS.
- Current-only roster/status/injury/depth/schedule context excluded: PASS.
- Market/vendor/projection/ADP/rank fields excluded as source truth: PASS.
- Routes, route proxies, TPRR, YPRR, and ambiguous `rz_att` absent: PASS.
- Missing values not forced to zero by the V2 builder: PASS.

Each row uses completed season N facts only and full season N+1 outcomes only.
